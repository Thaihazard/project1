from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
FEATURES_CONFIG = ROOT / "config" / "features_config.yaml"


def _feature_config() -> dict:
    with FEATURES_CONFIG.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_csv(path: Path) -> pd.DataFrame:
    """Load an approved training extract; never fetch or save data implicitly."""
    return pd.read_csv(path)


def load_postgres(database_url: str) -> pd.DataFrame:
    """Read approved/paid payroll outcomes without selecting employee names or IDs."""
    import psycopg

    url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    query = """
        SELECT
            e.base_salary AS current_salary,
            e.kpi_score,
            e.soft_skill_score,
            0::double precision AS years_experience,
            0::integer AS certification_count,
            p.gross_salary AS target_salary
        FROM employees AS e
        JOIN pay_slips AS p ON p.employee_id = e.id
        WHERE p.status IN ('approved', 'paid')
          AND p.gross_salary > 0
          AND e.base_salary > 0
    """
    with psycopg.connect(url) as connection:
        frame = pd.read_sql_query(query, connection)
    defaults = _feature_config().get("database_defaults", {})
    for column, value in defaults.items():
        if column in frame and frame[column].eq(0).all():
            frame[column] = value
    return frame


def validate_training_data(frame: pd.DataFrame) -> pd.DataFrame:
    config = _feature_config()
    required = [*config["input_features"], *config["categorical_features"], config["target"]]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Training data is missing required columns: {', '.join(missing)}")
    clean = frame[required].copy()
    for column in [*config["input_features"], config["target"]]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna(subset=required)
    clean = clean[(clean["current_salary"] > 0) & (clean[config["target"]] > 0)]
    if len(clean) < 20:
        raise ValueError(f"At least 20 valid payroll rows are required; received {len(clean)}")
    return clean
