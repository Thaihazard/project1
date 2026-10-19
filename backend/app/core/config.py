from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "AI CompHub API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite+aiosqlite:///{(DATA_DIR / 'comp_hub.db').as_posix()}"
    jwt_secret: str = "dev-only-change-this-secret-before-deployment"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    firebase_project_id: str = ""
    firebase_service_account_path: Path | None = None
    firebase_auth_email_map: dict[str, str] = {}
    demo_admin_password: str = "AdminDemo123!"
    demo_manager_password: str = "ManagerDemo123!"
    demo_employee_password: str = "EmployeeDemo123!"
    model_path: Path = BACKEND_DIR.parent / "ml_engine" / "artifacts" / "xgboost_salary_v1.pkl"
    shap_explainer_path: Path = BACKEND_DIR.parent / "ml_engine" / "artifacts" / "shap_explainer_v1.pkl"
    scaler_pipeline_path: Path = BACKEND_DIR.parent / "ml_engine" / "artifacts" / "scaler_pipeline_v1.pkl"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore", protected_namespaces=())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
