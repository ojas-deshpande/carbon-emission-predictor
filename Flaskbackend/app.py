"""
app.py
──────
Full-stack Flask application with MySQL database, authentication, and admin panel.

Features:
• User authentication with Flask-Login
• Admin panel for CSV upload and model retraining
• REST API endpoints for dashboard data
• MySQL database with SQLAlchemy ORM
• APScheduler: auto-reruns generate_data.py every 24 hours
• 4 new Task-3 endpoints: /api/predict, /api/anomalies, /api/risk, /api/scenario

Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import subprocess
import numpy as np
import pandas as pd
import webbrowser
from threading import Timer

# ── APScheduler ────────────────────────────────────────────────────────────────
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

from config import Config
from models import db, User, Country, EmissionData, ModelMetrics, Forecast, Insight, DataUploadLog

# Import ML pipeline
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ML pipeline'))
from data_pipeline import preprocess_country, build_forecast_X, FEATURE_COLS
from ml_models import train_country, forecast_country
from insights import generate_country_insights

# ── Flask App Setup ────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Paths ───────────────────────────────────────────────────────────────────────
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.join(_THIS_DIR, '..', 'ML pipeline')
_GENERATE_PY  = os.path.join(_ML_DIR, 'generate_data.py')
_DASHBOARD_JSON = os.path.join(_ML_DIR, 'dashboard_data.json')

# In-process cache so we don't re-read the file on every request
_dashboard_cache: dict = {}
_cache_mtime: float    = 0.0


def _load_dashboard_json() -> dict:
    """
    Return parsed dashboard_data.json, re-reading from disk only when the
    file has changed (mtime comparison acts as a lightweight cache).
    """
    global _dashboard_cache, _cache_mtime
    try:
        mtime = os.path.getmtime(_DASHBOARD_JSON)
        if mtime != _cache_mtime:
            with open(_DASHBOARD_JSON, 'r', encoding='utf-8') as f:
                _dashboard_cache = json.load(f)
            _cache_mtime = mtime
    except FileNotFoundError:
        pass   # file not yet generated; return whatever is in cache
    return _dashboard_cache


# ── APScheduler: auto-regenerate every 24 hours ─────────────────────────────────
def _scheduled_generate():
    """
    Background task: runs generate_data.py as a subprocess so it uses
    its own Python interpreter / path context.  Errors are logged to stdout.
    """
    try:
        result = subprocess.run(
            [sys.executable, _GENERATE_PY],
            capture_output=True, text=True, timeout=600,
            cwd=_ML_DIR
        )
        if result.returncode == 0:
            print(f'[APScheduler] generate_data.py completed successfully at {datetime.utcnow().isoformat()}Z')
        else:
            print(f'[APScheduler] generate_data.py FAILED:\n{result.stderr[:500]}')
    except Exception as exc:
        print(f'[APScheduler] Error running generate_data.py: {exc}')


_scheduler = BackgroundScheduler(daemon=True)
_scheduler.add_job(
    func=_scheduled_generate,
    trigger=IntervalTrigger(hours=24),
    id='regenerate_dashboard',
    name='Regenerate dashboard data every 24 h',
    replace_existing=True,
)
_scheduler.start()
atexit.register(lambda: _scheduler.shutdown(wait=False))


# ── Helper Functions ───────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_dashboard_data():
    """Build the same JSON structure as static version, but from database."""
    countries = Country.query.all()
    
    # Meta
    all_years = db.session.query(EmissionData.year).distinct().order_by(EmissionData.year).all()
    year_start = min(y[0] for y in all_years) if all_years else 1990
    year_end = max(y[0] for y in all_years) if all_years else 2023
    
    # Global totals
    global_by_year = (
        db.session.query(EmissionData.year, db.func.sum(EmissionData.co2).label('total'))
        .group_by(EmissionData.year)
        .order_by(EmissionData.year)
        .all()
    )
    global_years = [row.year for row in global_by_year]
    global_totals = [round(row.total, 1) if row.total else 0 for row in global_by_year]
    
    # Top 10 (latest year)
    top10_data = (
        db.session.query(Country.name, db.func.sum(EmissionData.co2).label('total'))
        .join(EmissionData)
        .filter(EmissionData.year == year_end)
        .group_by(Country.name)
        .order_by(db.desc('total'))
        .limit(10)
        .all()
    )
    top10_countries = [row.name for row in top10_data]
    
    top10_series = {}
    for c_name in top10_countries:
        c_obj = Country.query.filter_by(name=c_name).first()
        if not c_obj:
            continue
        emissions = EmissionData.query.filter_by(country_id=c_obj.id).order_by(EmissionData.year).all()
        top10_series[c_name] = {
            'years': [e.year for e in emissions],
            'co2': [round(e.co2, 1) if e.co2 else 0 for e in emissions],
        }
    
    # Map data
    map_data = {'iso': [], 'country': [], 'co2': [], 'co2_per_capita': [], 'rank': []}
    latest_emissions = (
        db.session.query(Country, EmissionData)
        .join(EmissionData)
        .filter(EmissionData.year == year_end)
        .order_by(db.desc(EmissionData.co2))
        .all()
    )
    for rank, (country, emission) in enumerate(latest_emissions, 1):
        map_data['iso'].append(country.iso_code or '')
        map_data['country'].append(country.name)
        map_data['co2'].append(round(emission.co2, 1) if emission.co2 else 0)
        map_data['co2_per_capita'].append(round(emission.co2_per_capita, 3) if emission.co2_per_capita else 0)
        map_data['rank'].append(rank)
    
    # Year map snapshots
    year_map_data = {}
    for yr in range(year_start, year_end + 1, 5):
        yr_emissions = db.session.query(Country, EmissionData).join(EmissionData).filter(EmissionData.year == yr).all()
        if yr_emissions:
            year_map_data[str(yr)] = {
                'iso': [c.iso_code or '' for c, e in yr_emissions],
                'country': [c.name for c, e in yr_emissions],
                'co2': [round(e.co2, 1) if e.co2 else 0 for c, e in yr_emissions],
            }
    year_map_data[str(year_end)] = {'iso': map_data['iso'], 'country': map_data['country'], 'co2': map_data['co2']}
    
    # Per-country
    per_country = {}
    country_list = []
    for country in countries:
        country_list.append(country.name)
        emissions = EmissionData.query.filter_by(country_id=country.id).order_by(EmissionData.year).all()
        metrics = ModelMetrics.query.filter_by(country_id=country.id).order_by(ModelMetrics.trained_at.desc()).first()
        forecasts = Forecast.query.filter_by(country_id=country.id).order_by(Forecast.year).all()
        insight = Insight.query.filter_by(country_id=country.id).first()
        if not emissions:
            continue
        total_rows = len(emissions)
        split_idx = int(total_rows * 0.8)
        test_years = [e.year for e in emissions[split_idx:]]
        per_country[country.name] = {
            'iso': country.iso_code or '',
            'years': [e.year for e in emissions],
            'co2': [round(e.co2, 1) if e.co2 else None for e in emissions],
            'energy_pc': [round(e.energy_per_capita, 1) if e.energy_per_capita else None for e in emissions],
            'gdp_pc': [round(e.gdp_per_capita, 1) if e.gdp_per_capita else None for e in emissions],
            'population': [int(e.population) if e.population else None for e in emissions],
            'co2_per_capita': [round(e.co2_per_capita, 3) if e.co2_per_capita else None for e in emissions],
            'test_years': test_years, 'rf_test': [], 'lr_test': [],
            'forecast_years': [f.year for f in forecasts] if forecasts else [],
            'rf_forecast': [round(f.rf_forecast, 2) if f.rf_forecast else None for f in forecasts] if forecasts else [],
            'lr_forecast': [round(f.lr_forecast, 2) if f.lr_forecast else None for f in forecasts] if forecasts else [],
            'rf_r2': round(metrics.rf_r2, 4) if metrics and metrics.rf_r2 is not None else 0,
            'lr_r2': round(metrics.lr_r2, 4) if metrics and metrics.lr_r2 is not None else 0,
            'rf_mae': round(metrics.rf_mae, 2) if metrics and metrics.rf_mae is not None else 0,
            'lr_mae': round(metrics.lr_mae, 2) if metrics and metrics.lr_mae is not None else 0,
            'feature_importances': metrics.feature_importances if metrics and metrics.feature_importances else {},
            'sparse': metrics.sparse if metrics else False,
            'insight': {
                'headline': insight.headline if insight else '',
                'detail': insight.detail if insight else '',
                'recommendation': insight.recommendation if insight else '',
                'risk': insight.risk if insight else 'Unknown',
                'risk_color': insight.risk_color if insight else '#666',
                'pct_change': round(insight.pct_change, 2) if insight and insight.pct_change is not None else 0,
                'forecast_end': round(insight.forecast_end, 2) if insight and insight.forecast_end else 0,
                'forecast_mean': round(insight.forecast_mean, 2) if insight and insight.forecast_mean else 0,
                'top_factor': insight.top_factor if insight else 'Year',
            } if insight else {},
        }
    return {
        'meta': {'year_start': year_start, 'year_end': year_end, 'forecast_years': 5, 'n_countries': len(country_list), 'feature_cols': FEATURE_COLS},
        'global': {'years': global_years, 'total_co2': global_totals, 'top10': top10_series, 'top10_countries': top10_countries},
        'map': map_data, 'year_map': year_map_data, 'countries': sorted(country_list), 'per_country': per_country,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.args.get('fresh') == '1':
        logout_user()
        session.clear()
        return redirect(url_for('login'))
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=False)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    # External login template
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    # Serve static dashboard HTML
    return send_from_directory('../frontend', 'index.html')


@app.route('/api/data')
@login_required
def api_get_data():
    try:
        data = get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    stats = {
        'total_countries': Country.query.count(),
        'total_data_points': EmissionData.query.count(),
        'latest_year': db.session.query(db.func.max(EmissionData.year)).scalar(),
        'last_upload': DataUploadLog.query.order_by(DataUploadLog.uploaded_at.desc()).first(),
        'total_users': User.query.count(),
    }
    recent_uploads = DataUploadLog.query.order_by(DataUploadLog.uploaded_at.desc()).limit(10).all()
    # External admin template
    return render_template('admin.html', user=current_user, stats=stats, uploads=recent_uploads)


@app.route('/admin/upload', methods=['POST'])
@login_required
def admin_upload_csv():
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    log = None
    try:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        log = DataUploadLog(user_id=current_user.id, filename=filename, file_size=file_size, status='processing')
        db.session.add(log)
        db.session.commit()
        df = pd.read_csv(filepath)
        exclude = ["World", "Asia", "Europe", "Africa", "America", "income", "OECD", "Annex", "International", "bunker"]
        mask = ~df["country"].str.contains("|".join(exclude), case=False, na=False)
        df = df[mask & df["iso_code"].notna() & (df["year"] >= 1990)]
        countries_processed = 0
        for country_name in df['country'].unique():
            country_data = df[df['country'] == country_name]
            iso_code = country_data['iso_code'].iloc[0] if len(country_data) > 0 else None
            country = Country.query.filter_by(name=country_name).first()
            if not country:
                country = Country(name=country_name, iso_code=iso_code)
                db.session.add(country)
                db.session.flush()
            EmissionData.query.filter_by(country_id=country.id).delete()
            for _, row in country_data.iterrows():
                emission = EmissionData(
                    country_id=country.id, year=int(row['year']),
                    co2=float(row['co2']) if pd.notna(row.get('co2')) else None,
                    energy_per_capita=float(row['energy_per_capita']) if pd.notna(row.get('energy_per_capita')) else None,
                    gdp_per_capita=float(row['gdp_per_capita']) if pd.notna(row.get('gdp_per_capita')) else None,
                    population=int(row['population']) if pd.notna(row.get('population')) else None,
                    co2_per_capita=float(row['co2_per_capita']) if pd.notna(row.get('co2_per_capita')) else None,
                )
                db.session.add(emission)
            countries_processed += 1
        db.session.commit()
        log.status = 'success'
        log.countries_processed = countries_processed
        db.session.commit()
        return jsonify({'success': True, 'countries_processed': countries_processed})
    except Exception as e:
        if log:
            log.status = 'failed'
            log.error_message = str(e)
            db.session.commit()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/retrain', methods=['POST'])
@login_required
def admin_retrain_models():
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    try:
        countries = Country.query.all()
        retrained_count = 0
        for country in countries:
            emissions = EmissionData.query.filter_by(country_id=country.id).order_by(EmissionData.year).all()
            if len(emissions) < 10:
                continue
            df = pd.DataFrame([{
                'year': e.year, 'co2': e.co2, 'energy_per_capita': e.energy_per_capita,
                'gdp_per_capita': e.gdp_per_capita, 'population': e.population,
            } for e in emissions])
            prep = preprocess_country(df, FEATURE_COLS)
            if prep is None:
                continue
            X_train, X_test, y_train, y_test, scaler, df_clean = prep
            sparse = len(X_test) == 0
            result = train_country(X_train, X_test, y_train, y_test, FEATURE_COLS, sparse)
            X_future, future_years = build_forecast_X(df_clean, scaler, FEATURE_COLS, n_years=5)
            rf_fc, lr_fc = forecast_country(result, X_future)
            insight_data = generate_country_insights(country=country.name, historical_co2=df_clean["co2"].values, rf_forecast=rf_fc, feature_importances=result.feature_importances, rf_r2=result.rf_r2, rf_mae=result.rf_mae, forecast_years=future_years)
            metrics = ModelMetrics.query.filter_by(country_id=country.id).first()
            if not metrics:
                metrics = ModelMetrics(country_id=country.id)
                db.session.add(metrics)
            metrics.rf_r2 = result.rf_r2
            metrics.lr_r2 = result.lr_r2
            metrics.rf_mae = result.rf_mae
            metrics.lr_mae = result.lr_mae
            metrics.feature_importances = result.feature_importances
            metrics.sparse = sparse
            metrics.trained_at = datetime.utcnow()
            Forecast.query.filter_by(country_id=country.id).delete()
            for i, year in enumerate(future_years):
                forecast = Forecast(country_id=country.id, year=year, rf_forecast=float(rf_fc[i]), lr_forecast=float(lr_fc[i]))
                db.session.add(forecast)
            insight = Insight.query.filter_by(country_id=country.id).first()
            if not insight:
                insight = Insight(country_id=country.id)
                db.session.add(insight)
            insight.headline = insight_data['headline']
            insight.detail = insight_data['detail']
            insight.recommendation = insight_data['recommendation']
            insight.risk = insight_data['risk']
            insight.risk_color = insight_data['risk_color']
            insight.pct_change = insight_data['pct_change']
            insight.forecast_end = insight_data['forecast_end']
            insight.forecast_mean = insight_data['forecast_mean']
            insight.top_factor = insight_data['top_factor']
            retrained_count += 1
        db.session.commit()
        return jsonify({'success': True, 'countries_retrained': retrained_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — 4 new API endpoints (all require login)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/predict/<path:country>')
@login_required
def api_predict(country: str):
    """
    GET /api/predict/<country>
    Returns ensemble forecast JSON for the given country.
    Response:
        {
          country, forecast_years, forecast, upper_band, lower_band,
          rf_forecast, lr_forecast, arima_r2, rf_r2, ensemble_r2, used_arima
        }
    """
    data = _load_dashboard_json()
    if not data:
        return jsonify({'error': 'Dashboard data not yet generated. Run generate_data.py first.'}), 503

    per_country = data.get('per_country', {})
    # Case-insensitive lookup
    matched = next((k for k in per_country if k.lower() == country.lower()), None)
    if matched is None:
        return jsonify({'error': f'Country "{country}" not found. Available: {sorted(per_country.keys())}'}), 404

    c = per_country[matched]
    return jsonify({
        'country':       matched,
        'forecast_years': c.get('forecast_years', []),
        'forecast':      c.get('forecast', c.get('rf_forecast', [])),
        'upper_band':    c.get('upper_band', []),
        'lower_band':    c.get('lower_band', []),
        'rf_forecast':   c.get('rf_forecast', []),
        'lr_forecast':   c.get('lr_forecast', []),
        'arima_r2':      c.get('arima_r2', 0),
        'rf_r2':         c.get('rf_r2', 0),
        'ensemble_r2':   c.get('ensemble_r2', c.get('rf_r2', 0)),
        'used_arima':    c.get('used_arima', False),
    })


@app.route('/api/anomalies')
@login_required
def api_anomalies():
    """
    GET /api/anomalies
    Returns all countries that have at least one anomaly year.
    Response:
        {
          total_countries_with_anomalies: int,
          anomalies: [
            { country, iso, anomaly_years: [...], trend_reversal }
          ]
        }
    """
    data = _load_dashboard_json()
    if not data:
        return jsonify({'error': 'Dashboard data not yet generated. Run generate_data.py first.'}), 503

    per_country = data.get('per_country', {})
    result = []
    for country_name, c in per_country.items():
        anomaly_years = c.get('anomaly_years', [])
        if anomaly_years:   # only countries with at least one anomaly
            result.append({
                'country':        country_name,
                'iso':            c.get('iso', ''),
                'anomaly_years':  anomaly_years,
                'trend_reversal': c.get('trend_reversal', False),
            })

    # Sort by number of anomaly events descending
    result.sort(key=lambda x: len(x['anomaly_years']), reverse=True)
    return jsonify({
        'total_countries_with_anomalies': len(result),
        'anomalies': result,
    })


@app.route('/api/risk/<path:country>')
@login_required
def api_risk(country: str):
    """
    GET /api/risk/<country>
    Returns risk_level (Low/Moderate/High/Critical) and risk_score (0-100).

    Risk score formula:
        score = clamp(abs(pct_change) * 2.5, 0, 100)
    This maps:
        0 % change   →  0  (no risk)
        20% change   → 50  (moderate)
        40% change   → 100 (critical)
    """
    data = _load_dashboard_json()
    if not data:
        return jsonify({'error': 'Dashboard data not yet generated. Run generate_data.py first.'}), 503

    per_country = data.get('per_country', {})
    matched = next((k for k in per_country if k.lower() == country.lower()), None)
    if matched is None:
        return jsonify({'error': f'Country "{country}" not found.'}), 404

    c = per_country[matched]
    insight = c.get('insight', {})

    # Derive pct_change from insight block or recompute from forecast
    pct_change = insight.get('pct_change', None)
    if pct_change is None:
        co2     = c.get('co2', [])
        forecast = c.get('forecast', c.get('rf_forecast', []))
        if co2 and forecast:
            last_hist  = float(co2[-1]) if co2[-1] is not None else 0
            last_fc    = float(forecast[-1]) if forecast[-1] is not None else 0
            pct_change = ((last_fc - last_hist) / max(abs(last_hist), 0.01)) * 100
        else:
            pct_change = 0.0

    # risk_level buckets (mirrored from insights.py)
    abs_pct = abs(pct_change)
    if abs_pct < 3:
        risk_level = 'Low'
    elif abs_pct < 10:
        risk_level = 'Moderate'
    elif abs_pct < 20:
        risk_level = 'High'
    else:
        risk_level = 'Critical'

    # risk_score: 0–100 linear scale, caps at 40% change
    risk_score = round(min(abs_pct * 2.5, 100.0), 1)

    return jsonify({
        'country':    matched,
        'risk_level': risk_level,
        'risk_score': risk_score,
        'pct_change': round(float(pct_change), 2),
    })


@app.route('/api/scenario', methods=['POST'])
@login_required
def api_scenario():
    """
    POST /api/scenario
    Body (JSON):
        {
          "country":          str,
          "gdp_growth":       float,   # 0–10 %
          "policy_reduction": float,   # 0–50 %
          "energy_mix_shift": float    # 0–30 % (informational only)
        }

    Formula:
        adjusted_forecast[i] = base_forecast[i]
                                × (1 - policy_reduction / 100)
                                × (1 + gdp_growth / 200)

    Response:
        {
          country, forecast_years,
          baseline_forecast,   # original ensemble forecast
          scenario_forecast,   # adjusted values
          projected_savings    # sum(baseline) - sum(scenario), MT CO₂
        }
    """
    body = request.get_json(silent=True) or {}
    country         = body.get('country', '')
    gdp_growth      = float(body.get('gdp_growth', 0))
    policy_reduction = float(body.get('policy_reduction', 0))
    energy_mix_shift = float(body.get('energy_mix_shift', 0))  # stored but not in formula

    # Validate ranges
    if not (0 <= gdp_growth <= 10):
        return jsonify({'error': 'gdp_growth must be 0–10'}), 400
    if not (0 <= policy_reduction <= 50):
        return jsonify({'error': 'policy_reduction must be 0–50'}), 400
    if not (0 <= energy_mix_shift <= 30):
        return jsonify({'error': 'energy_mix_shift must be 0–30'}), 400
    if not country:
        return jsonify({'error': '"country" is required'}), 400

    data = _load_dashboard_json()
    if not data:
        return jsonify({'error': 'Dashboard data not yet generated. Run generate_data.py first.'}), 503

    per_country = data.get('per_country', {})
    matched = next((k for k in per_country if k.lower() == country.lower()), None)
    if matched is None:
        return jsonify({'error': f'Country "{country}" not found.'}), 404

    c = per_country[matched]
    baseline  = c.get('forecast', c.get('rf_forecast', []))
    fc_years  = c.get('forecast_years', [])

    if not baseline:
        return jsonify({'error': f'No forecast data available for "{matched}".'}), 404

    # Apply the scenario formula
    policy_factor = 1.0 - (policy_reduction / 100.0)
    gdp_factor    = 1.0 + (gdp_growth / 200.0)
    scenario = [
        round(float(v) * policy_factor * gdp_factor, 3)
        if v is not None else None
        for v in baseline
    ]

    # Projected savings (positive = emissions reduced)
    baseline_sum = sum(v for v in baseline  if v is not None)
    scenario_sum = sum(v for v in scenario  if v is not None)
    savings      = round(baseline_sum - scenario_sum, 2)

    return jsonify({
        'country':           matched,
        'forecast_years':    fc_years,
        'baseline_forecast': baseline,
        'scenario_forecast': scenario,
        'projected_savings': savings,
        'params': {
            'gdp_growth':       gdp_growth,
            'policy_reduction': policy_reduction,
            'energy_mix_shift': energy_mix_shift,
        },
    })


# ── Run ────────────────────────────────────────────────────────────────────────
def open_browser():
    webbrowser.open_new("http://localhost:5000/login?fresh=1")

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Only open browser once (prevents double-opening in debug mode)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1.5, open_browser).start()
        
    print("""
+------------------------------------------------------------+
|  Carbon Emission Dashboard - Full Stack Edition           |
+------------------------------------------------------------+

Server: http://localhost:5000

Setup Steps:
1. Initialize database: python init_db.py
2. Start Flask: python app.py
3. Login with admin credentials (see init_db.py output)

Features:
- Admin login with session management
- MySQL database for all data
- REST API endpoints
- CSV upload & retraining interface

Press Ctrl+C to stop
""")
    app.run(debug=True, host='0.0.0.0', port=5000)
