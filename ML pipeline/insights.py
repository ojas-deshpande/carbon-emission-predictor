"""
insights.py
───────────
Generates country-specific insights from forecast results.
"""

import numpy as np
from typing import Dict


TIPS = {
    "Energy Consumption": (
        "💡 Transitioning to renewables and improving energy efficiency are the "
        "highest-impact levers for this country's emission profile."
    ),
    "GDP per Capita": (
        "🏭 Economic growth is the primary driver — green industrial policy and "
        "carbon pricing can decouple GDP growth from emission growth."
    ),
    "Population": (
        "🏙️ Population-driven emission growth calls for investment in clean urban "
        "infrastructure, public transit, and per-capita efficiency standards."
    ),
    "Year (Trend)": (
        "📅 The dominant factor is the underlying time trend — this reflects "
        "structural shifts in the energy mix and technology adoption rate."
    ),
}

FACTOR_LABELS = {
    "year":              "Year (Trend)",
    "energy_per_capita": "Energy Consumption",
    "gdp_per_capita":    "GDP per Capita",
    "population":        "Population",
}


def generate_country_insights(
    country: str,
    historical_co2: np.ndarray,
    rf_forecast: np.ndarray,
    feature_importances: Dict[str, float],
    rf_r2: float,
    rf_mae: float,
    forecast_years: list,
) -> dict:
    last_val  = float(historical_co2[-1])
    fc_end    = float(rf_forecast[-1])
    fc_mean   = float(np.mean(rf_forecast))
    pct_chg   = ((fc_end - last_val) / max(last_val, 0.01)) * 100
    direction = "rise" if pct_chg > 0 else "decline"
    emoji     = "📈" if pct_chg > 0 else "📉"

    top_key   = max(feature_importances, key=feature_importances.get)
    top_label = FACTOR_LABELS.get(top_key, top_key)
    top_weight = feature_importances[top_key]

    if abs(pct_chg) < 3:
        risk, risk_color = "Low",      "#22c55e"
    elif abs(pct_chg) < 10:
        risk, risk_color = "Moderate", "#f59e0b"
    elif abs(pct_chg) < 20:
        risk, risk_color = "High",     "#ef4444"
    else:
        risk, risk_color = "Critical", "#b91c1c"

    headline = (
        f"{emoji} {country}'s emissions are forecast to "
        f"{direction} by {abs(pct_chg):.1f}% "
        f"by {forecast_years[-1]}."
    )

    detail = (
        f"Random Forest model (R² = {rf_r2:.3f}, MAE = {rf_mae:.1f} MT) "
        f"projects an average of {fc_mean:.1f} MT/yr, "
        f"reaching {fc_end:.1f} MT by {forecast_years[-1]}. "
        f"Top driver: {top_label} ({top_weight:.1%} importance)."
    )

    base_tip = TIPS.get(top_label, "📊 Review all drivers for targeted intervention.")
    if direction == "decline":
        rec = "✅ Emissions are trending down. " + base_tip
    else:
        rec = base_tip
    if abs(pct_chg) > 25:
        rec += " ⚠️ Urgent climate policy action is recommended."

    return {
        "headline": headline, "detail": detail, "recommendation": rec,
        "risk": risk, "risk_color": risk_color,
        "pct_change": round(pct_chg, 2),
        "forecast_end": round(fc_end, 2),
        "forecast_mean": round(fc_mean, 2),
        "top_factor": top_label,
    }
