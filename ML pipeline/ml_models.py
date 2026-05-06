"""
ml_models.py
────────────
Trains Linear Regression (baseline) and Random Forest per country.
Falls back to LR-only for countries with sparse data (< 15 rows).

Task 1 addition:
  • ARIMA(1,1,1) is fitted on the historical emissions series per country.
  • Final ensemble forecast = 0.6 × ARIMA + 0.4 × RF.
  • Falls back to RF-only when ARIMA fails (insufficient data / convergence).
  • Confidence bands = prediction ± (1.5 × MAE of the ensemble).
"""

import warnings
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class CountryModelResult:
    country: str
    rf_pred:   np.ndarray
    lr_pred:   np.ndarray
    rf_model:  Any
    lr_model:  Any
    rf_r2:     float
    lr_r2:     float
    rf_mae:    float
    lr_mae:    float
    feature_importances: Dict[str, float] = field(default_factory=dict)
    sparse: bool = False   # True if not enough data for RF


@dataclass
class ARIMAResult:
    """Holds the fitted ARIMA model and its in-sample metrics."""
    model_fit:  Any          # statsmodels ARIMAResults or None
    arima_r2:   float
    arima_mae:  float
    success:    bool         # False if ARIMA fitting failed


@dataclass
class EnsembleForecast:
    """Output of ensemble_forecast() — all arrays have length = n_future_steps."""
    forecast:    List[float]
    upper_band:  List[float]
    lower_band:  List[float]
    arima_r2:    float
    rf_r2:       float
    ensemble_r2: float       # computed on test set when available; else in-sample
    used_arima:  bool        # False if ARIMA was unavailable → pure RF


# ── Train LR + RF (unchanged from original) ───────────────────────────────────

def train_country(X_train, X_test, y_train, y_test,
                  feature_cols: list, sparse: bool = False) -> CountryModelResult:
    """
    Train LR + RF on one country's data.
    RF is trained on LR residuals (trend-corrected) so it can handle
    time-series extrapolation without bounding to training range.
    Falls back to LR-only when sparse or when RF underperforms LR.
    """
    # ── Linear Regression ─────────────────────────────────────────────────────
    lr = LinearRegression()
    lr.fit(X_train, y_train)

    if len(X_test) > 0:
        lr_pred_test = lr.predict(X_test)
        lr_r2  = float(r2_score(y_test, lr_pred_test))
        lr_mae = float(mean_absolute_error(y_test, lr_pred_test))
    else:
        lr_pred_test = np.array([])
        lr_train_pred = lr.predict(X_train)
        lr_r2  = float(r2_score(y_train, lr_train_pred))
        lr_mae = float(mean_absolute_error(y_train, lr_train_pred))

    fi_lr = {col: abs(float(c)) for col, c in zip(feature_cols, lr.coef_)}
    # Normalise LR importances so they sum to 1
    total = sum(fi_lr.values()) or 1.0
    fi_lr = {k: v / total for k, v in fi_lr.items()}

    if sparse:
        return CountryModelResult(
            country="", rf_pred=lr_pred_test, lr_pred=lr_pred_test,
            rf_model=lr, lr_model=lr,
            rf_r2=lr_r2, lr_r2=lr_r2,
            rf_mae=lr_mae, lr_mae=lr_mae,
            feature_importances=fi_lr, sparse=True,
        )

    # ── Random Forest on LR residuals (trend-corrected) ───────────────────────
    lr_train_pred = lr.predict(X_train)
    residuals     = y_train - lr_train_pred   # RF learns what LR missed

    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=6,                # shallower = less overfit on short time series
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, residuals)

    if len(X_test) > 0:
        rf_correction = rf.predict(X_test)
        rf_pred_test  = lr_pred_test + rf_correction    # LR trend + RF residual
        rf_r2  = float(r2_score(y_test, rf_pred_test))
        rf_mae = float(mean_absolute_error(y_test, rf_pred_test))
    else:
        rf_pred_test = np.array([])
        rf_corr_tr   = rf.predict(X_train)
        rf_r2  = float(r2_score(y_train, lr_train_pred + rf_corr_tr))
        rf_mae = float(mean_absolute_error(y_train, lr_train_pred + rf_corr_tr))

    fi_rf = {col: float(imp) for col, imp in zip(feature_cols, rf.feature_importances_)}

    # ── Auto-fallback: use whichever model is better ───────────────────────────
    # Only swap to LR-only (sparse mode) if LR meaningfully beats RF
    if rf_r2 < lr_r2 and lr_r2 > 0:
        return CountryModelResult(
            country="", rf_pred=lr_pred_test, lr_pred=lr_pred_test,
            rf_model=lr, lr_model=lr,
            rf_r2=lr_r2, lr_r2=lr_r2,
            rf_mae=lr_mae, lr_mae=lr_mae,
            feature_importances=fi_lr, sparse=True,
        )

    return CountryModelResult(
        country="",
        rf_pred=rf_pred_test, lr_pred=lr_pred_test,
        rf_model=rf, lr_model=lr,
        rf_r2=rf_r2, lr_r2=lr_r2,
        rf_mae=rf_mae, lr_mae=lr_mae,
        feature_importances=fi_rf, sparse=False,
    )


def forecast_country(result: CountryModelResult, X_future: np.ndarray) -> tuple:
    """
    Returns (rf_forecast, lr_forecast) numpy arrays.
    For non-sparse models: rf_forecast = LR trend + RF residual correction.
    For sparse/fallback models: both return the same LR prediction.
    """
    lr_fc = np.clip(result.lr_model.predict(X_future), 0, None)

    if result.sparse:
        return lr_fc, lr_fc

    # RF was trained on residuals — add LR trend back
    rf_correction = result.rf_model.predict(X_future)
    rf_fc = np.clip(lr_fc + rf_correction, 0, None)
    return rf_fc, lr_fc


# ── TASK 1: ARIMA fitting ──────────────────────────────────────────────────────

def fit_arima(co2_series: np.ndarray) -> ARIMAResult:
    """
    Fit ARIMA(1,1,1) on a 1-D array of annual CO2 emissions (in order).
    Returns ARIMAResult with success=False if fitting fails for any reason
    (insufficient data, convergence error, etc.).

    Requirements: statsmodels >= 0.14.
    """
    MIN_OBS = 15  # ARIMA(1,1,1) needs at least ~15 observations

    if len(co2_series) < MIN_OBS:
        return ARIMAResult(model_fit=None, arima_r2=0.0, arima_mae=float("inf"),
                           success=False)

    try:
        from statsmodels.tsa.arima.model import ARIMA

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(co2_series, order=(1, 1, 1))
            fit   = model.fit()

        # In-sample fitted values (aligned to original series)
        fitted = fit.fittedvalues
        # ARIMA(1,1,1) loses the first differenced point; align by index
        actual = co2_series[len(co2_series) - len(fitted):]
        arima_r2  = float(r2_score(actual, fitted))
        arima_mae = float(mean_absolute_error(actual, fitted))

        return ARIMAResult(model_fit=fit, arima_r2=arima_r2, arima_mae=arima_mae,
                           success=True)

    except Exception:
        return ARIMAResult(model_fit=None, arima_r2=0.0, arima_mae=float("inf"),
                           success=False)


# ── TASK 1: Ensemble forecast ──────────────────────────────────────────────────

def ensemble_forecast(
    rf_forecast:  np.ndarray,
    arima_result: ARIMAResult,
    rf_mae:       float,
    rf_r2:        float,
    y_test:       Optional[np.ndarray] = None,
    arima_r2_override: Optional[float] = None,
) -> EnsembleForecast:
    """
    Combine ARIMA and RF forecasts into a weighted ensemble.

    Weights  : 0.6 × ARIMA  +  0.4 × RF  (when ARIMA is available)
    Fallback : 1.0 × RF     (when ARIMA failed)
    Bands    : forecast  ±  (1.5 × MAE)

    Parameters
    ----------
    rf_forecast        : RF point forecast array (n_steps,)
    arima_result       : output of fit_arima()
    rf_mae             : RF mean absolute error (used for band when ARIMA absent)
    rf_r2              : RF R² score
    y_test             : optional hold-out actuals to compute ensemble_r2
    arima_r2_override  : if provided, use this instead of arima_result.arima_r2
    """
    n = len(rf_forecast)
    rf_fc = np.clip(rf_forecast, 0, None)

    if arima_result.success and arima_result.model_fit is not None:
        # Extend ARIMA n steps beyond the last fitted point
        try:
            arima_fc_raw = arima_result.model_fit.forecast(steps=n)
            arima_fc     = np.clip(np.asarray(arima_fc_raw, dtype=float), 0, None)

            ensemble_fc  = 0.6 * arima_fc + 0.4 * rf_fc
            combo_mae    = 0.6 * arima_result.arima_mae + 0.4 * rf_mae
            used_arima   = True
            arima_r2_val = arima_r2_override if arima_r2_override is not None \
                           else arima_result.arima_r2

        except Exception:
            # ARIMA forecast step failed → fall back silently
            ensemble_fc  = rf_fc.copy()
            combo_mae    = rf_mae
            used_arima   = False
            arima_r2_val = 0.0
    else:
        ensemble_fc  = rf_fc.copy()
        combo_mae    = rf_mae
        used_arima   = False
        arima_r2_val = 0.0

    # Confidence bands
    band         = 1.5 * combo_mae
    upper_band   = (ensemble_fc + band).tolist()
    lower_band   = np.clip(ensemble_fc - band, 0, None).tolist()
    forecast_lst = ensemble_fc.tolist()

    # ensemble_r2: use test set if provided, else report RF r2
    if y_test is not None and len(y_test) > 0 and len(y_test) == n:
        try:
            ens_r2 = float(r2_score(y_test, ensemble_fc))
        except Exception:
            ens_r2 = rf_r2
    else:
        ens_r2 = rf_r2

    return EnsembleForecast(
        forecast=forecast_lst,
        upper_band=upper_band,
        lower_band=lower_band,
        arima_r2=round(arima_r2_val, 4),
        rf_r2=round(rf_r2, 4),
        ensemble_r2=round(ens_r2, 4),
        used_arima=used_arima,
    )
