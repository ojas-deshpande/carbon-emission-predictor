# 🌍 Carbon Emission Prediction Dashboard

> A full-stack machine learning web application for predicting and analyzing global CO₂ emissions across 62+ countries using Random Forest and Linear Regression models.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=flat-square&logo=mysql)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-red?style=flat-square&logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 About the Project

This is a **Final Year BCA Project** at Tilak Maharashtra Vidyapeeth University. It combines machine learning forecasting with an interactive web dashboard to analyze and predict CO₂ emissions for 62 countries (1990–2028).

**Key highlights:**
- Trains separate ML models per country (Random Forest + Linear Regression)
- Forecasts emissions 5 years into the future
- Interactive dashboard with 5 tabs and 10+ charts
- Mobile-responsive design (works on phone, tablet, desktop)
- AI chatbot powered by Claude that answers questions about the data
- Full-stack version with Flask, MySQL, admin login, and CSV upload

---

## ✨ Features

### 5-Tab Interactive Dashboard
| Tab | Description |
|---|---|
| 🗺️ **World Map** | Choropleth map with year slider and total/per-capita toggle |
| 📊 **Country Detail** | Forecast chart, emission gauge, feature importance, ML metrics |
| 🆚 **Compare** | Compare up to 4 countries side-by-side with 5 charts |
| 🌐 **Global Trends** | World total CO₂, top 10 pie chart, annual trend lines |
| 🤖 **AI Chat** | Live chatbot that answers data questions using your actual numbers |

### Machine Learning
- Random Forest Regressor (trend-residual approach for time series)
- Linear Regression (baseline + fallback)
- Per-country training with auto-fallback when RF underperforms
- Metrics: R² Score and Mean Absolute Error (MAE)
- 5-year forecast with confidence band

### Full-Stack Backend
- Admin login with Flask-Login and session management
- MySQL database with 7 normalized tables
- REST API endpoints for all dashboard data
- CSV upload to load real OWID dataset (200+ countries)
- Live model retraining from admin panel
- Audit logs for all uploads

### Responsive Design
- Desktop: fixed sidebar, 4-column KPIs
- Tablet: 2-column KPIs, stacked panels
- Mobile: hamburger menu, slide-in sidebar, stacked charts

---

## 🗂️ Project Structure

```
carbon-emission-dashboard/
│
├── index.html                  # Dashboard — open this in your browser
├── _template.html              # UI template (edit this for design changes)
├── generate_data.py            # Main script — runs pipeline → builds index.html
├── data_pipeline.py            # Data loading, cleaning, feature engineering
├── ml_models.py                # RF + LR model training
├── insights.py                 # Auto-generates insight text per country
├── chatbot_server.py           # Local proxy server for AI Chat tab
├── requirements.txt            # ML dependencies
│
└── backend/
    ├── app.py                  # Flask application (all routes and API)
    ├── models.py               # SQLAlchemy database models (7 tables)
    ├── config.py               # Database connection settings
    ├── init_db.py              # One-time database setup script
    └── requirements_backend.txt
```

---

## ⚡ Quick Start — Open Dashboard (5 Minutes)

**Step 1 — Install Python**

Download from https://www.python.org/downloads/
> On Windows: tick ✅ **"Add Python to PATH"** during install

**Step 2 — Set up project**

```bash
git clone https://github.com/YOUR_USERNAME/carbon-emission-dashboard.git
cd carbon-emission-dashboard

python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

**Step 3 — Build and open dashboard**

```bash
python generate_data.py
```

Then double-click `index.html` — dashboard opens in your browser. Done!

---

## 🏗️ Full-Stack Setup — Flask + MySQL (20 Minutes)

**Step 1 — Install MySQL**

Download from https://dev.mysql.com/downloads/installer/

**Step 2 — Create database**

```bash
mysql -u root -p
```

```sql
CREATE DATABASE carbon_emissions CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'carbon_user'@'localhost' IDENTIFIED BY 'carbon_pass';
GRANT ALL PRIVILEGES ON carbon_emissions.* TO 'carbon_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Step 3 — Install and initialize**

```bash
pip install -r requirements.txt
pip install -r backend/requirements_backend.txt

python generate_data.py

cd backend
python init_db.py
python app.py
```

Visit **http://localhost:5000** — login with `admin` / `admin123`

> Full guide: see `HOW_TO_RUN.md`

---

## 🤖 Enable AI Chat

```bash
# 1. Get a free API key at https://console.anthropic.com
# 2. Run the chat server
python chatbot_server.py
# 3. Open http://localhost:5500 in your browser
```

---

## 🌐 Use Real Data (200+ Countries)

```bash
# 1. Download owid-co2-data.csv from:
#    https://github.com/owid/co2-data

# 2. Put it in the project root folder

# 3. Re-run the generator
python generate_data.py
# → Automatically detects and uses real data
```

---

## 🧠 ML Pipeline

```
Raw Data (OWID CSV or Synthetic)
    ↓
data_pipeline.py
 • Filter real countries only
 • Interpolate missing values
 • StandardScaler (fit on train only — no data leakage)
 • 80/20 time-based split
    ↓
ml_models.py
 • Linear Regression (baseline)
 • Random Forest on LR residuals (fixes time-series extrapolation)
 • Auto-fallback to LR when RF underperforms
    ↓
insights.py
 • Risk classification: Low / Moderate / High / Critical
 • Natural language insight generation
    ↓
generate_data.py
 • 5-year forecast (2024–2028)
 • JSON export → inject into _template.html → index.html
```

### Sample Results (Synthetic Data)

| Country | RF R² | Latest CO₂ | 2028 Forecast |
|---|---|---|---|
| China | 0.588 | 11,500 MT | 12,198 MT |
| India | 0.747 | 2,700 MT | 3,039 MT |
| Vietnam | 0.804 | 320 MT | 332 MT |
| Germany | 0.152 | 660 MT | 615 MT |

---

## 🗄️ Database Schema (Full-Stack)

| Table | Purpose |
|---|---|
| `users` | Admin authentication |
| `countries` | Country name and ISO code |
| `emission_data` | Historical CO₂ per country per year |
| `model_metrics` | R², MAE for RF and LR per country |
| `forecasts` | 5-year forecast values |
| `insights` | AI-generated insight text |
| `upload_logs` | Audit log for CSV uploads |

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | ✅ Login | Main dashboard |
| GET | `/login` | ❌ Public | Login page |
| GET | `/admin` | ✅ Admin | Admin panel |
| GET | `/api/data` | ✅ Login | Full dashboard JSON |
| GET | `/api/countries` | ✅ Login | List all countries |
| POST | `/admin/upload` | ✅ Admin | Upload CSV dataset |
| POST | `/admin/retrain` | ✅ Admin | Retrain all ML models |

---

## 📦 Dependencies

**ML Pipeline** (`requirements.txt`)
```
pandas>=2.0.0
numpy>=1.26.0
scikit-learn>=1.4.0
```

**Flask Backend** (`backend/requirements_backend.txt`)
```
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.0
Flask-Login>=0.6.3
Flask-CORS>=4.0.0
PyMySQL>=1.1.0
Werkzeug>=3.0.0
```

**Frontend** (loaded from CDN — nothing to install)
```
Plotly.js 2.27
Space Grotesk + JetBrains Mono (Google Fonts)
```

---

## 🎓 University Details

| | |
|---|---|
| **University** | Tilak Maharashtra Vidyapeeth |
| **Degree** | Bachelor of Computer Application (BCA) |
| **Year** | 2025–2026 |
| **Project** | Carbon Emission Prediction using Machine Learning |

---

## 🔮 Future Scope

- Real-time CO₂ data via live API integration
- LSTM deep learning model
- Sector-level emission breakdown (Energy, Transport, Industry)
- Bar chart race animation
- PDF report export
- CO₂ vs temperature correlation chart
- Docker containerization
- Cloud deployment (AWS / Heroku)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

Dataset: [Our World in Data CO₂](https://github.com/owid/co2-data) — CC BY license.

---

## 📬 Contact

**[Your Name]**
PRN: [Your PRN Number]
University: Tilak Maharashtra Vidyapeeth

---

*Built with Python · Flask · MySQL · scikit-learn · Plotly.js · Anthropic Claude API*
