# AI CompHub API

FastAPI backend with versioned endpoints, async SQLAlchemy persistence, JWT/RBAC, payroll APIs, and a replaceable salary prediction service. Swagger UI is available at `/docs`.

## Run locally

From the repository root, install backend dependencies and start the API:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend --port 8001
```

The API and Swagger UI are available at `http://127.0.0.1:8001` and `http://127.0.0.1:8001/docs`. The default development database is SQLite at `backend/data/comp_hub.db`. On first startup, the API seeds a sample Q3 2026 payroll period and demo accounts. The Vite dev server proxies `/api` to `http://127.0.0.1:8001`.

Demo logins: `hr` / `AdminDemo123!`, `manager` / `ManagerDemo123!`, `employee` / `EmployeeDemo123!`. Change these through environment variables before using a shared environment. For PostgreSQL, set `DATABASE_URL=postgresql+asyncpg://...`.

## API overview

- `POST /api/v1/auth/login`, `/refresh`, `/change-password`; `GET /api/v1/auth/me`
- `GET /api/v1/employees` (manager/HR)
- `GET /api/v1/payroll/payslips?payPeriodId=...` (manager/HR)
- `POST /api/v1/payroll/calculate`, `GET /api/v1/payroll/export?payPeriodId=...` (HR)
- `GET /api/v1/payroll/proposals`, `POST /api/v1/payroll/proposals/{id}/decision` (HR; decisions are audited and do not alter payslips)
- `GET /api/v1/payroll/me/payslips/latest` (authenticated employee)
- `GET /api/v1/attendance/me`, `POST /api/v1/attendance/check-in`, `/check-out`; `GET /api/v1/attendance/team` (manager/HR)
- `GET /api/v1/leave/me`, `POST /api/v1/leave/requests`, team review endpoints; leave types include annual, sick, personal, and unpaid leave
- `/api/v1/overtime` for overtime registration and manager/HR approval
- `/api/v1/contracts` for employee contract records and HR contract creation
- `/api/v1/benefits` for benefit catalog, employee enrollment, and HR review/management
- `POST /api/v1/ai-salary/predict`, `/simulate`, `/budget-simulation`
- Attendance check-in and leave requests are persisted in the development database. Leave approvals are restricted to HR or the employee's assigned manager.

`docker compose -f backend/docker-compose.yml up --build` starts the API, PostgreSQL, Redis, and Celery worker. Before production, run `python -m alembic upgrade head` from the backend directory, then create an initial HR user with `python -m scripts.create_user --username your-admin --role hr` from that directory. The local SQLite/demo mode is intended for development. No trained model artifacts are checked in; until approved artifacts are placed in `ml_engine/artifacts`, the prediction endpoint reports `baseline-demo-v1` and explicitly identifies its output as illustrative, not SHAP. Follow `ml_engine/README.md` to train and evaluate a model. Install `backend/requirements-ml.txt` from the repository root and provide the model, fitted preprocessing pipeline, and SHAP artifacts to enable XGBoost/SHAP inference.
# Firebase Authentication with Google

1. Create a Firebase project and register a Web app. In Firebase Console, enable **Authentication → Sign-in method → Google** and add `localhost` to Authorized domains.
2. Copy the web app config (`apiKey`, `authDomain`, `projectId`, `appId`) to `frontend/.env` using the `VITE_FIREBASE_*` names shown in `frontend/.env.example`. These web config values are intended to be public; protect production data with Firebase Security Rules.
3. In Firebase Console **Project settings → Service accounts**, generate an Admin SDK key for local development. Store the JSON outside the repository, then set `FIREBASE_PROJECT_ID` and `FIREBASE_SERVICE_ACCOUNT_PATH` in `backend/.env`. Never commit or share the service-account private key.
4. HR can set a work email using `PATCH /api/v1/employees/{employee_id}/email` with `{"email":"person@example.com"}`. Firebase sign-in matches this verified email to the employee record and obtains the employee/manager role from that record; an existing AI CompHub user linked by `employee_id` is required. For HR or other non-employee accounts, optionally map the verified email to an existing username with `FIREBASE_AUTH_EMAIL_MAP={"hr@example.com":"hr"}`. Unknown emails are denied; no role is assigned from the email domain.
5. Install requirements and apply migrations from `backend`: `python -m pip install -r requirements.txt` then `python -m alembic upgrade head`.
6. Start backend on port `8001` (`python -m uvicorn app.main:app --reload --port 8001`) and restart the frontend. The Vite proxy and API Docs link use port 8001.

The frontend signs in with Google through Firebase, obtains a Firebase ID token, and sends it to `/api/v1/auth/firebase`. The backend verifies it with Firebase Admin before linking the Firebase UID to the local user and issuing AI CompHub tokens. See Google's [Firebase web sign-in guide](https://firebase.google.com/docs/auth/web/google-signin), [ID token verification guide](https://firebase.google.com/docs/auth/admin/verify-id-tokens), and [Admin SDK setup](https://firebase.google.com/docs/admin/setup).
