# AI CompHub

AI CompHub contains a React/Vite HR compensation dashboard and a FastAPI backend with PostgreSQL-ready async persistence, JWT/RBAC, payroll workflows, and an optional salary-model service.

## Run the backend

From the repository root, install dependencies and start the API:

    python -m pip install -r backend/requirements.txt
    python -m uvicorn app.main:app --reload --app-dir backend --port 8001

The API is served at http://localhost:8001. Open [Swagger UI](http://127.0.0.1:8001/docs) for the interactive API documentation. The frontend header also has a **Backend API / Docs** link. Local development uses SQLite at backend/data/comp_hub.db.

## Run the frontend

In another terminal:

    npm.cmd --prefix frontend run dev

Vite proxies /api requests to the backend. Set VITE_API_BASE_URL to use a different API address.

## Demo logins

- HR: hr / AdminDemo123!
- Manager: manager / ManagerDemo123!
- Employee: employee / EmployeeDemo123!

Change these demo passwords and the JWT secret before exposing the service. Demo payroll and baseline AI predictions are illustrative; there is no trained model checked in. See backend/README.md for the API overview, Docker Compose, PostgreSQL and ML setup.

## ML salary model

The training pipeline and model artifact layout live in `ml_engine/`. See [ml_engine/README.md](ml_engine/README.md) for approved data inputs, training commands, quality gates, and artifact loading.

