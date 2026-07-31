# 🚛 FreightAI — Enterprise Freight Rate Prediction Platform

> **AI-powered freight rate intelligence built with XGBoost, LightGBM, CatBoost, SHAP & FastAPI.**  
> Predict B2B freight rates in < 50ms with 94%+ accuracy across 7 benchmarked ML models.

---

## ✨ Platform Overview

FreightAI is a **production-ready Machine Learning platform** designed for logistics teams that need fast, accurate, and explainable freight rate predictions. Every layer of the system — from data preprocessing to REST API — was engineered to production standards.

| Feature | Details |
|---|---|
| 🧠 **ML Engine** | XGBoost, LightGBM, CatBoost, Random Forest, Extra Trees, Gradient Boosting, Linear Regression |
| 🔍 **Explainability** | SHAP TreeExplainer — global summaries + interactive local waterfall attributions |
| ⚡ **Inference Speed** | < 50ms per prediction via FastAPI |
| 📊 **Validation R²** | 0.94+ on held-out validation set |
| 📅 **Forecasting** | Day-by-day December 2025 rate forecast with seasonality analysis |
| 📁 **Batch Processing** | Drag-and-drop CSV upload → instant bulk predictions with stats summary |
| 🎨 **Frontend** | Premium glassmorphism dark-mode UI with 15+ interactive Chart.js visualizations |
| 🐳 **Docker** | Fully containerised — one command to run |

---

## 🏗️ Architecture

```
project/
├── backend/
│   ├── api/
│   │   └── routes.py              # REST endpoints (predict, train, metrics, download)
│   ├── app.py                     # FastAPI entrypoint with CORS + static mounts
│   ├── config.py                  # Single source of truth for all paths & settings
│   ├── train.py                   # Full training pipeline orchestrator
│   ├── predict.py                 # Validation + December inference runner
│   ├── preprocessing.py           # Scikit-learn compatible transformer (fit/transform)
│   ├── feature_engineering.py     # 15+ feature extraction (haversine, cyclical, bins)
│   ├── hyperparameter_tuning.py   # Optuna integration (15 trials, 5-min cap)
│   ├── model_selection.py         # 7-model CV benchmark
│   ├── evaluate.py                # RMSE, MAE, R² with SHAP + chart generation
│   └── utils.py                   # Logger, timeit decorator, directory helpers
│
├── frontend/
│   ├── css/
│   │   ├── style.css              # Design system (tokens, glassmorphism, layout)
│   │   ├── dashboard.css          # KPI cards, tables, badges, toast system
│   │   └── animations.css        # 10+ micro-animation keyframes
│   ├── js/
│   │   ├── main.js                # Shared API helper, particles, GSAP init
│   │   ├── theme.js               # Dark / light mode toggle + persistence
│   │   ├── prediction.js          # Single predict form + full analytics dashboard
│   │   ├── upload.js              # Batch CSV drag & drop + results summary
│   │   ├── dashboard.js           # Metrics fetch + dynamic Chart.js charts
│   │   └── charts.js              # Static chart loader helper
│   ├── index.html                 # Landing page — hero, features, tech stack
│   ├── prediction.html            # Live prediction + 5-chart analytics dashboard
│   ├── dashboard.html             # Model performance dashboard
│   ├── analytics.html             # EDA charts — distribution, correlation, scatter
│   ├── model.html                 # SHAP explainability + interactive waterfall
│   └── december.html              # December 2025 forecast — time-series charts
│
└── data/
    ├── train-test.csv             # Training dataset
    ├── validation.csv             # Held-out validation dataset
    └── december-chart-inputs.csv  # December route inputs for forecasting
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Install Dependencies

```bash
cd project
pip install -r requirements.txt
```

### 2. Train the Model

```bash
cd backend
python train.py
```

This runs the full pipeline:
- Cleans & preprocesses training data  
- Engineers 15+ features (haversine, cyclical dates, target encoding, bins)  
- Benchmarks 7 ML models with 5-fold cross-validation  
- Runs Optuna hyperparameter tuning on the best model (15 trials)  
- Generates SHAP values, feature importance, scatter, and residual charts  
- Saves `models/best_model.pkl`, `metrics.json`, `model_comparison.json`

### 3. Generate Assessment Deliverables

```bash
python predict.py
```

Outputs:
- `validation_predictions.csv` — predictions on the held-out validation set  
- `december_chart_predictions.csv` — day-by-day December 2025 rate forecasts

### 4. Start the Platform

**Backend (FastAPI on port 8000):**
```bash
python app.py
```

**Frontend (on port 3000):**
```bash
cd ../frontend
python -m http.server 3000
```

Open **http://localhost:3000** in your browser.

> 📖 **Interactive API docs** available at **http://localhost:8000/docs**

---

## 🐳 Docker (Optional)

```bash
cd project
docker build -t freightai .
docker run -p 8000:8000 freightai
```

---

## 📊 Frontend Pages

| Page | URL | Description |
|---|---|---|
| 🏠 Home | `/index.html` | Hero landing page with feature showcase |
| 📈 Dashboard | `/dashboard.html` | Live model metrics + benchmark comparison charts |
| ⚡ Predict | `/prediction.html` | Single load prediction + 5-chart analytics dashboard |
| 🔬 Analytics | `/analytics.html` | EDA — distributions, correlations, feature impact |
| 🧠 Models | `/model.html` | SHAP explainability + interactive waterfall simulator |
| 📅 Dec Forecast | `/december.html` | December 2025 daily rate forecast with time-series chart |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | API health check + model readiness |
| `GET` | `/api/v1/metrics` | Model performance metrics (RMSE, MAE, R²) |
| `GET` | `/api/v1/models/compare` | Full model benchmark comparison |
| `POST` | `/api/v1/predict/single` | Single load rate prediction |
| `POST` | `/api/v1/predict/batch` | CSV file batch prediction |
| `POST` | `/api/v1/train` | Trigger background retraining |
| `GET` | `/api/v1/download/validation` | Download validation predictions CSV |
| `GET` | `/api/v1/download/december` | Download December forecast CSV |

---

## 🧪 Key Technical Decisions

### Feature Engineering
- **Target Encoding** with smoothing (k=20) for high-cardinality city columns — prevents overfitting on rare routes
- **Cyclical date features** (sin/cos month, dayofweek) to capture seasonal periodicity correctly
- **Haversine distance** incorporated as a cross-check against reported distance
- **Distance & weight bins** to capture non-linear threshold effects

### Model Selection
Tree-based ensembles consistently outperform linear models because:
1. Freight rate relationships are **non-linear** (rate/mile differs by haul length tier)
2. Route-level interactions (pickup × delivery × season) are captured via tree splits
3. Boosting handles the **heavy tail** in the rate distribution naturally

### Preprocessing
- **Negative weight** anomalies fixed by taking absolute values (data quality issue)
- **Missing `market_index`** imputed by month-median → global median fallback
- **Missing `weight`** imputed by route-median → global median fallback

---

## 📄 License
MIT License — see [LICENSE](LICENSE)
