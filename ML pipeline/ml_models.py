"""
ml_models.py
────────────
Trains Linear Regression (baseline) and Random Forest per country.
Falls back to LR-only for countries with sparse data (< 15 rows).
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


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
