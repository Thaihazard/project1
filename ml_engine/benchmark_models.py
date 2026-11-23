"""Model bake-off and benchmarking for AI CompHub salary prediction models."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

# Ensure ml_engine packages can be imported
ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from ml_engine.src.data_loader import load_csv, validate_training_data
from ml_engine.src.feature_engineering import engineer_features
from ml_engine.src.preprocessor import build_preprocessor


def run_benchmark(data_path: Path) -> pd.DataFrame:
    with (ROOT / "config" / "model_config.yaml").open(encoding="utf-8") as f:
        model_cfg = yaml.safe_load(f)["model"]
    with (ROOT / "config" / "features_config.yaml").open(encoding="utf-8") as f:
        feat_cfg = yaml.safe_load(f)

    raw_df = load_csv(data_path)
    clean_df = validate_training_data(raw_df)
    prepared = engineer_features(clean_df)

    feature_names = [*feat_cfg["numeric_features"], *feat_cfg["categorical_features"]]
    X = prepared[feature_names]
    y = prepared[feat_cfg["target"]]

    cv = KFold(n_splits=model_cfg.get("cv_folds", 5), shuffle=True, random_state=model_cfg.get("random_state", 42))

    models = {
        "Ridge": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=150, max_depth=6, random_state=model_cfg["random_state"], n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=model_cfg.get("n_estimators", 400),
            max_depth=model_cfg.get("max_depth", 4),
            learning_rate=model_cfg.get("learning_rate", 0.05),
            random_state=model_cfg["random_state"],
            objective="reg:squarederror",
            eval_metric="mae",
            n_jobs=-1,
        ),
    }

    scoring = {
        "mae": "neg_mean_absolute_error",
        "rmse": "neg_root_mean_squared_error",
        "r2": "r2",
    }

    results = []
    for name, regressor in models.items():
        preprocessor = build_preprocessor(feat_cfg["numeric_features"], feat_cfg["categorical_features"])
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", regressor)])
        cv_res = cross_validate(pipeline, X, y, cv=cv, scoring=scoring)

        mae_mean = -cv_res["test_mae"].mean()
        mae_std = cv_res["test_mae"].std()
        rmse_mean = -cv_res["test_rmse"].mean()
        r2_mean = cv_res["test_r2"].mean()

        results.append({
            "Model": name,
            "CV MAE (₫)": f"{mae_mean:,.0f} ± {mae_std:,.0f}",
            "CV RMSE (₫)": f"{rmse_mean:,.0f}",
            "CV R²": f"{r2_mean:.4f}",
            "_raw_mae": mae_mean,
        })

    summary_df = pd.DataFrame(results).sort_values("_raw_mae").drop(columns=["_raw_mae"])
    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark salary prediction models.")
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data" / "raw" / "payroll_training.csv",
        help="Path to training CSV file",
    )
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Data file not found at {args.data}. Generating sample data first...")
        from ml_engine.generate_sample_data import generate_payroll_data
        sample_df = generate_payroll_data(600)
        args.data.parent.mkdir(parents=True, exist_ok=True)
        sample_df.to_csv(args.data, index=False)
        print(f"Sample data generated: {args.data}")

    print("\n--- MODEL BENCHMARK RESULTS (5-Fold CV) ---")
    df_results = run_benchmark(args.data)
    print(df_results.to_string(index=False))
