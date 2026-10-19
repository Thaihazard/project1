from __future__ import annotations

from math import sqrt

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_regression(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def meets_quality_gate(metrics: dict[str, float], max_mae: float, min_r2: float) -> bool:
    return metrics["mae"] <= max_mae and metrics["r2"] >= min_r2
