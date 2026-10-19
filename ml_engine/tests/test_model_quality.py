from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import yaml

from ml_engine.src.evaluator import evaluate_regression, meets_quality_gate
from ml_engine.src.feature_engineering import engineer_features

ROOT = Path(__file__).resolve().parents[1]


def test_quality_gate_accepts_good_predictions_and_rejects_bad_predictions():
    actual = np.array([10.0, 20.0, 30.0, 40.0])
    good = evaluate_regression(actual, np.array([10.5, 19.5, 30.5, 39.5]))
    bad = evaluate_regression(actual, np.array([40.0, 10.0, 20.0, 30.0]))
    assert meets_quality_gate(good, max_mae=2.0, min_r2=0.95)
    assert not meets_quality_gate(bad, max_mae=2.0, min_r2=0.95)


def test_trained_model_meets_configured_quality_gate():
    test_path = Path(os.getenv("ML_TEST_DATA", ROOT / "data" / "processed" / "test.csv"))
    model_path = ROOT / "artifacts" / "xgboost_salary_v1.pkl"
    preprocessor_path = ROOT / "artifacts" / "scaler_pipeline_v1.pkl"
    if not test_path.is_file() or not model_path.is_file() or not preprocessor_path.is_file():
        pytest.skip("Run the training pipeline and provide data/processed/test.csv to evaluate a trained artifact.")

    config = yaml.safe_load((ROOT / "config" / "model_config.yaml").read_text(encoding="utf-8"))
    features = yaml.safe_load((ROOT / "config" / "features_config.yaml").read_text(encoding="utf-8"))
    frame = pd.read_csv(test_path)
    prepared = engineer_features(frame)
    feature_names = [*features["numeric_features"], *features["categorical_features"]]
    actual = prepared[features["target"]].to_numpy()
    x = prepared[feature_names]
    model = joblib.load(model_path)
    preprocessor = joblib.load(preprocessor_path)
    metrics = evaluate_regression(actual, model.predict(preprocessor.transform(x)))
    quality = config["quality"]
    assert meets_quality_gate(metrics, quality["max_mae"], quality["min_r2"]), metrics
