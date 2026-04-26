"""
generate_data.py
────────────────
Orchestrates the full ML pipeline for all countries, builds the
dashboard JSON, and injects it into _template.html → index.html.

Usage:
    python generate_data.py
    open index.html
"""

import json
import sys
import numpy as np
import pandas as pd

from data_pipeline import (
    load_data, preprocess_country, build_forecast_X,
    FEATURE_COLS, YEAR_START, YEAR_END,
)
from ml_models import train_country, forecast_country
from insights import generate_country_insights

FORECAST_YEARS = 5   # how many years ahead to forecast
MIN_COUNTRIES  = 10  # min data rows to include a country at all


# ── Helpers ────────────────────────────────────────────────────────────────────

def safe_float(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), 3)

def series_to_list(arr):
    return [safe_float(v) for v in arr]


# ── Main pipeline ──────────────────────────────────────────────────────────────

def build_dashboard_data() -> dict:
    # ── 1. Load data ────────────────────────────────────────────────────────────
    print("  Loading data ...")
    df_all = load_data()
    df_all = df_all.dropna(subset=["co2"])
    df_all = df_all[df_all["co2"] > 0]

    countries_raw = sorted(df_all["country"].unique().tolist())
    print(f"  Found {len(countries_raw)} countries.")

    # ── 2. Global totals ────────────────────────────────────────────────────────
    print("  Building global totals ...")
    global_by_year = (
        df_all.groupby("year")["co2"].sum().reset_index()
        .rename(columns={"co2": "total_co2"})
    )
    global_years  = global_by_year["year"].tolist()
    global_totals = series_to_list(global_by_year["total_co2"])

    # Top 10 emitters (by latest year)
    latest_year = int(df_all["year"].max())
    top10 = (
        df_all[df_all["year"] == latest_year]
        .nlargest(10, "co2")["country"].tolist()
    )
    top10_series = {}
    for c in top10:
        sub = df_all[df_all["country"] == c].sort_values("year")
        top10_series[c] = {
            "years": sub["year"].tolist(),
            "co2":   series_to_list(sub["co2"]),
        }

    # ── 3. World map snapshot (latest year per country) ─────────────────────────
    print("  Building map snapshot ...")
    map_df = (
        df_all[df_all["year"] == latest_year]
        .dropna(subset=["iso_code"])
        .copy()
    )
    # Also compute global ranking
    map_df = map_df.sort_values("co2", ascending=False).reset_index(drop=True)
    map_df["rank"] = map_df.index + 1

    map_data = {
        "iso":          map_df["iso_code"].tolist(),
        "country":      map_df["country"].tolist(),
        "co2":          series_to_list(map_df["co2"]),
        "co2_per_capita": series_to_list(map_df.get("co2_per_capita", map_df["co2"] / (map_df.get("population", 1e6) / 1e6))),
        "rank":         map_df["rank"].tolist(),
    }

    # Also build year-slider map data
    year_map_data = {}
    for yr in range(max(YEAR_START, latest_year - 20), latest_year + 1, 5):
        yr_df = df_all[df_all["year"] == yr].dropna(subset=["iso_code"])
        if len(yr_df) == 0:
            continue
        year_map_data[str(yr)] = {
            "iso":     yr_df["iso_code"].tolist(),
            "country": yr_df["country"].tolist(),
            "co2":     series_to_list(yr_df["co2"]),
        }
    # Always include latest year
    year_map_data[str(latest_year)] = {
        "iso":     map_df["iso_code"].tolist(),
        "country": map_df["country"].tolist(),
        "co2":     series_to_list(map_df["co2"]),
    }

    # ── 4. Per-country ML ────────────────────────────────────────────────────────
    print("  Training models for each country ...")
    per_country = {}
    skipped = 0

    for country in countries_raw:
        sub = df_all[df_all["country"] == country].copy()
        if len(sub) < MIN_COUNTRIES:
            skipped += 1
            continue

        iso = sub["iso_code"].iloc[-1] if "iso_code" in sub.columns else ""
        prep = preprocess_country(sub, FEATURE_COLS)
        if prep is None:
            skipped += 1
            continue

        X_train, X_test, y_train, y_test, scaler, df_clean = prep
        sparse = len(X_test) == 0

        result = train_country(X_train, X_test, y_train, y_test, FEATURE_COLS, sparse)
        result.country = country

        X_future, future_years = build_forecast_X(df_clean, scaler, FEATURE_COLS, FORECAST_YEARS)
        rf_fc, lr_fc = forecast_country(result, X_future)

        insight = generate_country_insights(
            country=country,
            historical_co2=df_clean["co2"].values,
            rf_forecast=rf_fc,
            feature_importances=result.feature_importances,
            rf_r2=result.rf_r2,
            rf_mae=result.rf_mae,
            forecast_years=future_years,
        )

        years_hist = df_clean["year"].tolist()
        co2_hist   = series_to_list(df_clean["co2"])

        # Test-fit predictions aligned to test years
        test_start_idx = len(df_clean) - len(y_test) if len(y_test) > 0 else len(df_clean)
        test_years_list = years_hist[test_start_idx:]

        per_country[country] = {
            "iso":          iso,
            "years":        years_hist,
            "co2":          co2_hist,
            "energy_pc":    series_to_list(df_clean.get("energy_per_capita", pd.Series([None]*len(df_clean)))),
            "gdp_pc":       series_to_list(df_clean.get("gdp_per_capita",    pd.Series([None]*len(df_clean)))),
            "population":   series_to_list(df_clean.get("population",         pd.Series([None]*len(df_clean)))),
            "co2_per_capita": series_to_list(df_clean.get("co2_per_capita",  pd.Series([None]*len(df_clean)))),
            "test_years":   test_years_list,
            "rf_test":      series_to_list(result.rf_pred),
            "lr_test":      series_to_list(result.lr_pred),
            "forecast_years": future_years,
            "rf_forecast":  series_to_list(rf_fc),
            "lr_forecast":  series_to_list(lr_fc),
            "rf_r2":        round(result.rf_r2, 4),
            "lr_r2":        round(result.lr_r2, 4),
            "rf_mae":       round(result.rf_mae, 2),
            "lr_mae":       round(result.lr_mae, 2),
            "feature_importances": {k: round(v, 4) for k, v in result.feature_importances.items()},
            "sparse":       sparse,
            "insight":      insight,
        }

    print(f"  Processed {len(per_country)} countries. Skipped {skipped}.")

    return {
        "meta": {
            "year_start":   YEAR_START,
            "year_end":     latest_year,
            "forecast_years": FORECAST_YEARS,
            "n_countries":  len(per_country),
            "feature_cols": FEATURE_COLS,
        },
        "global": {
            "years":        global_years,
            "total_co2":    global_totals,
            "top10":        top10_series,
            "top10_countries": top10,
        },
        "map": map_data,
        "year_map": year_map_data,
        "countries": sorted(per_country.keys()),
        "per_country": per_country,
    }


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running multi-country carbon emission pipeline ...\n")

    data = build_dashboard_data()

    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    json_path = os.path.join(script_dir, "dashboard_data.json")
    template_path = os.path.join(project_dir, "frontend", "_template.html")
    index_path = os.path.join(project_dir, "frontend", "index.html")

    print(f"\n  Writing {json_path} ...")
    with open(json_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))   # compact — no indent for smaller file
    size_kb = round(len(json.dumps(data)) / 1024, 1)
    print(f"  JSON size: {size_kb} KB")

    print(f"  Injecting into {template_path} ...")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Accommodate placeholder with or without spaces
    if "%%DASHBOARD_DATA%%" not in template and "%% DASHBOARD_DATA %%" not in template and "__DASHBOARD_DATA__" not in template:
        print("ERROR: Dashboard placeholder not found in _template.html", file=sys.stderr)
        sys.exit(1)

    output = template.replace("%%DASHBOARD_DATA%%", json.dumps(data, separators=(",", ":")))
    output = output.replace("%% DASHBOARD_DATA %%", json.dumps(data, separators=(",", ":")))
    output = output.replace("__DASHBOARD_DATA__", json.dumps(data, separators=(",", ":")))

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(output)

    size_html = round(len(output) / 1024, 1)
    print(f"  index.html size: {size_html} KB")
    print("\nDone! Open index.html in any browser.")
    print(f"   Countries: {data['meta']['n_countries']} | "
          f"Years: {data['meta']['year_start']}-{data['meta']['year_end']} | "
          f"Forecast: +{data['meta']['forecast_years']} yrs")
