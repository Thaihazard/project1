from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import joblib
import yaml

from ml_engine.src.data_loader import ROOT, load_csv, load_postgres, validate_training_data
from ml_engine.src.explainer import build_explainer
from ml_engine.src.trainer import train


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the AI CompHub salary model.")
    parser.add_argument("--data", type=Path, help="CSV training extract. If omitted, use --database-url or DATABASE_URL.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL URL for approved payroll data.")
    parser.add_argument("--tune", action="store_true", help="Tune XGBoost hyperparameters with Optuna.")
    parser.add_argument("--enforce-quality", action="store_true", help="Do not replace artifacts unless configured MAE/R2 gates pass.")
    parser.add_argument("--artifacts-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()

    if args.data:
        frame = load_csv(args.data)
    elif args.database_url:
        frame = load_postgres(args.database_url)
    else:
        parser.error("Provide --data or a PostgreSQL --database-url/DATABASE_URL.")

    clean = validate_training_data(frame)
    model_config = read_yaml(ROOT / "config" / "model_config.yaml")
    features_config = read_yaml(ROOT / "config" / "features_config.yaml")
    result = train(clean, model_config, features_config, tune=args.tune)
    report = {**result.metrics, "cross_validation_mae": result.cv_mae, "rows": len(clean)}
    print(json.dumps(report, indent=2))

    quality = model_config["quality"]
    passed = result.metrics["mae"] <= quality["max_mae"] and result.metrics["r2"] >= quality["min_r2"]
    if args.enforce_quality and not passed:
        raise SystemExit("Quality gates failed; existing model artifacts were left unchanged.")

    args.artifacts_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.model, args.artifacts_dir / "xgboost_salary_v1.pkl")
    joblib.dump(result.preprocessor, args.artifacts_dir / "scaler_pipeline_v1.pkl")
    joblib.dump(build_explainer(result.model), args.artifacts_dir / "shap_explainer_v1.pkl")
    (args.artifacts_dir / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
