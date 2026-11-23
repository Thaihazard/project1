# AI CompHub

AI CompHub is an end-to-end HR compensation intelligence platform featuring a modern React/Vite dashboard, a FastAPI backend with PostgreSQL/SQLite async persistence, JWT/RBAC security, payroll workflows, and an XGBoost/SHAP salary prediction machine learning engine.

---

## 🚀 Quick Start with Docker

To run the entire full-stack application (PostgreSQL, Redis, Backend, Celery Worker, and Frontend) in one command:

```bash
docker compose up -d --build
```

### Access URLs
- **Web Dashboard (Frontend)**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger Docs**: [http://localhost:3000/docs](http://localhost:3000/docs) (or direct API at port `8000`)

---

## 💻 Local Development Setup (Without Docker)

For local development with hot-reloading (uses SQLite at `backend/data/comp_hub.db` automatically):

### 1. Backend (FastAPI)

From the repository root:

```bash
# 1. Install base API and ML inference dependencies
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-ml.txt

# 2. Start the API server
python -m uvicorn app.main:app --reload --app-dir backend --port 8001
```

- API Base URL: `http://localhost:8001`
- Interactive Swagger UI: `http://localhost:8001/docs`

> **Note on Linux**: Ensure the OpenMP library is installed for XGBoost: `sudo apt install -y libgomp1`.

### 2. Frontend (React + Vite)

In another terminal:

```bash
cd frontend

# Install npm dependencies (first time only)
npm install

# Start the Vite development server
npm run dev
```

- Web UI: `http://localhost:5173`
- The Vite dev server automatically proxies `/api` requests to `http://localhost:8001`.

---

## 🧠 ML Salary Model (XGBoost & SHAP)

The reproducible training pipeline, benchmark scripts, and artifacts live in `ml_engine/`.

```bash
# 1. Generate realistic synthetic payroll data (if no DB records exist yet)
python ml_engine/generate_sample_data.py

# 2. Run model bake-off benchmark (Ridge, Random Forest, XGBoost with 5-Fold CV)
python ml_engine/benchmark_models.py

# 3. Train the production XGBoost model with quality gates
python ml_engine/train_pipeline.py --data ml_engine/data/raw/payroll_training.csv --enforce-quality

# 4. Verify model loading and SHAP explanation in backend
python test_ai_connection.py
```

### Model Artifacts Layout
Trained artifacts are stored in `ml_engine/artifacts/`:
- `xgboost_salary_v1.pkl`: Trained XGBoost regression model.
- `scaler_pipeline_v1.pkl`: Scikit-learn preprocessing pipeline.
- `shap_explainer_v1.pkl`: SHAP TreeExplainer for feature importance.
- `quality_report.json`: Metrics (MAE, RMSE, R²) and validation results.

*Note: If no artifacts are installed, the backend safely falls back to a transparent `baseline-demo-v1` mode.*

---

## 🔑 Demo Logins

The application seeds demo accounts on first run:

| Role | Username | Password | Key Permissions |
| :--- | :--- | :--- | :--- |
| **HR / Admin** | `hr` | `AdminDemo123!` | Payroll approval, compensation proposals, contracts, budget simulation |
| **Manager** | `manager` | `ManagerDemo123!` | Team attendance, leave requests, team salary overview & proposals |
| **Employee** | `employee` | `EmployeeDemo123!` | Personal payslips, attendance check-in/out, AI salary estimation |

> Change these passwords and `JWT_SECRET` in `.env` before exposing to a production environment.

---

## 📚 Documentation
- [Backend Architecture & API Docs](backend/README.md)
- [ML Engine Pipeline & Data Contracts](ml_engine/README.md)
