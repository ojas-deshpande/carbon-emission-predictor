"""
data_pipeline.py
────────────────
Loads and processes CO2 emission data for 60+ countries.

Priority:
  1. If  owid-co2-data.csv  is present in the same folder → use it (real data).
  2. Otherwise → generate a realistic synthetic dataset based on known 
     country emission profiles and historical trends.

OWID CSV download:
  https://github.com/owid/co2-data  →  owid-co2-data.csv
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# ── Country profiles ───────────────────────────────────────────────────────────
# (name, iso3, co2_1990_MT, co2_2023_MT, growth_shape, energy_pc_2023, gdp_pc_2023, pop_2023_M)
# growth_shape: 'linear','exponential','peaked','flat','decline'
COUNTRY_PROFILES = [
    # Major emitters
    ("China",           "CHN", 2200,  11500, "exponential", 2500,  12700, 1412),
    ("United States",   "USA", 5100,   4800, "peaked",      7500,  63000,  335),
    ("India",           "IND",  600,   2700, "exponential", 1100,   2400, 1429),
    ("Russia",          "RUS", 2400,   1750, "decline",     5800,  12000,  144),
    ("Japan",           "JPN", 1200,   1050, "decline",     3800,  33000,  125),
    ("Germany",         "DEU",  980,    660, "decline",     4100,  48000,   84),
    ("South Korea",     "KOR",  230,    620, "exponential", 5500,  32000,   52),
    ("Iran",            "IRN",  220,    730, "linear",      2800,   5500,   87),
    ("Saudi Arabia",    "SAU",  200,    700, "linear",      6100,  23000,   36),
    ("Canada",          "CAN",  460,    550, "flat",        7600,  52000,   39),
    ("Indonesia",       "IDN",  150,    700, "exponential", 1000,   4300,  277),
    ("Brazil",          "BRA",  220,    500, "linear",      1700,   8700,  215),
    ("Mexico",          "MEX",  290,    450, "linear",      1900,  10000,  128),
    ("South Africa",    "ZAF",  300,    470, "flat",        4200,   6000,   60),
    ("Australia",       "AUS",  280,    390, "flat",        5600,  54000,   26),
    ("Turkey",          "TUR",  150,    450, "exponential", 1800,  10500,   85),
    ("United Kingdom",  "GBR",  580,    330, "decline",     3300,  46000,   68),
    ("Italy",           "ITA",  430,    320, "decline",     3000,  35000,   59),
    ("France",          "FRA",  380,    290, "decline",     3500,  42000,   68),
    ("Poland",          "POL",  380,    320, "decline",     3900,  18000,   38),
    ("Spain",           "ESP",  220,    240, "flat",        2800,  30000,   47),
    ("Ukraine",         "UKR",  700,    130, "decline",     2900,   4500,   44),
    ("Thailand",        "THA",   90,    320, "exponential", 1900,   7100,   72),
    ("Malaysia",        "MYS",   60,    270, "exponential", 3200,  11000,   33),
    ("Egypt",           "EGY",   80,    270, "linear",      1000,   3600,  105),
    ("Pakistan",        "PAK",   70,    220, "linear",       600,   1500,  231),
    ("UAE",             "ARE",   60,    250, "linear",       9000,  44000,   10),
    ("Kazakhstan",      "KAZ",  240,    250, "flat",        5200,   9500,   19),
    ("Netherlands",     "NLD",  170,    140, "decline",     4800,  56000,   18),
    ("Argentina",       "ARG",  110,    190, "linear",      2100,   10000,   46),
    ("Nigeria",         "NGA",   50,    130, "linear",       400,   2100,  223),
    ("Algeria",         "DZA",   80,    160, "linear",      1600,   4100,   45),
    ("Venezuela",       "VEN",  120,    100, "peaked",      2900,   5000,   29),
    ("Czech Republic",  "CZE",  160,    110, "decline",     5600,  25000,   11),
    ("Belgium",         "BEL",  130,    100, "decline",     5300,  47000,   12),
    ("Romania",         "ROU",  220,    100, "decline",     3000,  14000,   19),
    ("Vietnam",         "VNM",   20,    320, "exponential",  900,   4000,   98),
    ("Bangladesh",      "BGD",   10,     95, "exponential",  300,   2400,  171),
    ("Philippines",     "PHL",   40,     90, "linear",       700,   3600,  115),
    ("Uzbekistan",      "UZB",  130,    120, "flat",        2000,   2000,   35),
    ("Chile",           "CHL",   30,    100, "linear",      1900,  15000,   19),
    ("Romania",         "ROU",  220,    100, "decline",     3000,  14000,   19),
    ("Sweden",          "SWE",   60,     40, "decline",     4800,  55000,   10),
    ("Norway",          "NOR",   35,     40, "flat",        7000,  90000,    5),
    ("Denmark",         "DNK",   55,     35, "decline",     5200,  64000,    6),
    ("Finland",         "FIN",   55,     35, "decline",     7100,  50000,    6),
    ("Switzerland",     "CHE",   45,     35, "decline",     4200,  90000,    9),
    ("Austria",         "AUT",   60,     55, "decline",     4500,  51000,    9),
    ("Greece",          "GRC",   85,     55, "decline",     3000,  19000,   11),
    ("Portugal",        "PRT",   50,     45, "flat",        2700,  23000,   10),
    ("Hungary",         "HUN",   70,     50, "decline",     3800,  18000,   10),
    ("Israel",          "ISR",   50,     65, "linear",      3100,  52000,    9),
    ("Colombia",        "COL",   60,    100, "linear",      1100,   6500,   52),
    ("Peru",            "PER",   20,     50, "linear",       900,   6700,   33),
    ("Cuba",            "CUB",   30,     25, "flat",        1200,   8000,   11),
    ("Morocco",         "MAR",   25,     75, "linear",       700,   3600,   37),
    ("Ethiopia",        "ETH",    2,     20, "linear",       100,    900,  126),
    ("Kenya",           "KEN",    5,     18, "linear",       200,   2000,   55),
    ("Ghana",           "GHA",    5,     20, "linear",       300,   2300,   33),
    ("Tanzania",        "TZA",    2,     15, "linear",       100,   1100,   65),
    ("New Zealand",     "NZL",   25,     35, "flat",        4200,  42000,    5),
    ("Singapore",       "SGP",   30,     55, "linear",      8500,  65000,    6),
    ("Hong Kong",       "HKG",   35,     45, "flat",        5500,  48000,    7),
]

# Deduplicate
seen = set()
COUNTRY_PROFILES_CLEAN = []
for p in COUNTRY_PROFILES:
    if p[0] not in seen:
        seen.add(p[0])
        COUNTRY_PROFILES_CLEAN.append(p)
COUNTRY_PROFILES = COUNTRY_PROFILES_CLEAN

YEAR_START = 1990
YEAR_END   = 2023
YEARS      = list(range(YEAR_START, YEAR_END + 1))
N_YEARS    = len(YEARS)


def _growth_curve(start: float, end: float, n: int, shape: str, seed_offset: int = 0) -> np.ndarray:
    """Generate a realistic emission trajectory between start and end values."""
    rng = np.random.default_rng(42 + seed_offset)
    t = np.linspace(0, 1, n)

    if shape == "exponential":
        base = start * np.exp(np.log(end / max(start, 1)) * t ** 0.7)
    elif shape == "decline":
        base = start * (end / max(start, 1)) ** t
    elif shape == "peaked":
        peak_t = 0.45
        peak_v = max(start, end) * 1.15
        left  = np.interp(t[t <= peak_t], [0, peak_t], [start, peak_v])
        right = np.interp(t[t > peak_t],  [peak_t, 1], [peak_v, end])
        base  = np.concatenate([left, right])
    elif shape == "flat":
        mid  = (start + end) / 2
        bump = mid * 0.08 * np.sin(2 * np.pi * t * 2)
        base = np.linspace(start, end, n) + bump
    else:  # linear
        base = np.linspace(start, end, n)

    noise = rng.normal(0, max(start, end) * 0.02, n)
    return np.clip(base + noise, 0, None)


def generate_synthetic_data() -> pd.DataFrame:
    """
    Build a realistic multi-country annual CO2 dataset (1990–2023).
    Mirrors the structure of the OWID CSV so the rest of the pipeline
    is identical regardless of data source.
    """
    rows = []
    for idx, (country, iso3, co2_start, co2_end, shape,
               energy_pc, gdp_pc, pop_M) in enumerate(COUNTRY_PROFILES):
        rng = np.random.default_rng(idx * 7 + 13)

        co2_series = _growth_curve(co2_start, co2_end, N_YEARS, shape, seed_offset=idx)

        # Energy per capita: loosely tracks CO2
        energy_ratio = energy_pc / max(co2_end, 1)
        energy_series = co2_series * energy_ratio * (
            1 + rng.normal(0, 0.04, N_YEARS)
        )

        # GDP per capita: mostly upward trend
        gdp_series = np.linspace(gdp_pc * 0.45, gdp_pc, N_YEARS) * (
            1 + rng.normal(0, 0.03, N_YEARS)
        )
        # GFC dip 2009, COVID dip 2020
        gdp_series[19] *= 0.94  # 2009
        gdp_series[30] *= 0.93  # 2020

        # Population: smooth linear-ish growth
        pop_start = pop_M * rng.uniform(0.72, 0.82)
        pop_series = np.linspace(pop_start, pop_M, N_YEARS) * (
            1 + rng.normal(0, 0.005, N_YEARS)
        )

        # co2_per_capita
        co2_pc_series = (co2_series * 1e6) / (pop_series * 1e6)  # tonnes per person

        for i, yr in enumerate(YEARS):
            rows.append({
                "country":          country,
                "iso_code":         iso3,
                "year":             yr,
                "co2":              round(float(co2_series[i]), 2),
                "energy_per_capita": round(float(energy_series[i]), 1),
                "gdp_per_capita":   round(float(gdp_series[i]), 1),
                "population":       round(float(pop_series[i] * 1e6), 0),
                "co2_per_capita":   round(float(co2_pc_series[i]), 3),
            })

    df = pd.DataFrame(rows)
    return df


def load_owid_csv(filepath: str) -> pd.DataFrame:
    """
    Load real OWID CO2 CSV and reshape to match our schema.
    Download from: https://github.com/owid/co2-data
    """
    raw = pd.read_csv(filepath)

    # Filter: real countries only (drop continents/world aggregates)
    exclude_keywords = ["World", "Asia", "Europe", "Africa", "America",
                        "income", "OECD", "Annex", "International", "bunker"]
    mask = ~raw["country"].str.contains("|".join(exclude_keywords), case=False, na=False)
    raw  = raw[mask & raw["iso_code"].notna() & (raw["year"] >= YEAR_START)]

    keep = ["country", "iso_code", "year", "co2",
            "energy_per_capita", "gdp_per_capita", "population", "co2_per_capita"]
    available = [c for c in keep if c in raw.columns]
    df = raw[available].copy()

    # Ensure all schema columns exist
    for col in keep:
        if col not in df.columns:
            df[col] = np.nan

    return df.reset_index(drop=True)


def load_data(owid_path: str = "owid-co2-data.csv") -> pd.DataFrame:
    """Auto-detects whether real OWID data is available."""
    if os.path.exists(owid_path):
        print(f"  [DATA] Loading real OWID data from {owid_path} ...")
        return load_owid_csv(owid_path)
    else:
        print("  [INFO] OWID CSV not found -- using realistic synthetic dataset.")
        print("         (Drop owid-co2-data.csv here to use real data)")
        return generate_synthetic_data()


def preprocess_country(df_country: pd.DataFrame, feature_cols: list):
    """
    Clean and scale a single country's time series.
    Returns X_train, X_test, y_train, y_test, scaler, df_clean.
    Minimum 10 valid rows required; returns None if insufficient.
    """
    df = df_country.sort_values("year").copy()

    # Must have target
    df = df.dropna(subset=["co2"])
    if len(df) < 10:
        return None

    # Impute features
    for col in feature_cols:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear").ffill().bfill()
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = 0.0

    X = df[feature_cols].values
    y = df["co2"].values

    if len(df) < 15:
        # Not enough for a meaningful split — use all for training, none for test
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return X_scaled, np.array([]), y, np.array([]), scaler, df

    split = max(int(len(df) * 0.8), len(df) - 8)
    X_train_raw, X_test_raw = X[:split], X[split:]
    y_train, y_test         = y[:split], y[split:]

    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test  = scaler.transform(X_test_raw)

    return X_train, X_test, y_train, y_test, scaler, df


def build_forecast_X(df_clean: pd.DataFrame, scaler: StandardScaler,
                     feature_cols: list, n_years: int = 5) -> tuple:
    """
    Extrapolate features n_years into the future using trailing trend.
    Returns (X_future_scaled, future_years).
    """
    last_year = int(df_clean["year"].max())
    future_years = list(range(last_year + 1, last_year + n_years + 1))

    window = min(10, len(df_clean))
    recent = df_clean.sort_values("year").tail(window)

    future_rows = []
    for step in range(1, n_years + 1):
        row = {}
        for col in feature_cols:
            if col == "year":
                row[col] = last_year + step
            elif col in recent.columns:
                slope = (recent[col].iloc[-1] - recent[col].iloc[0]) / max(window - 1, 1)
                row[col] = float(recent[col].iloc[-1]) + slope * step
            else:
                row[col] = 0.0
        future_rows.append(row)

    future_df = pd.DataFrame(future_rows)[feature_cols]
    X_future  = scaler.transform(future_df.values)
    return X_future, future_years


FEATURE_COLS = ["year", "energy_per_capita", "gdp_per_capita", "population"]
