from __future__ import annotations

import pandas as pd


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create deterministic model features shared with the inference service."""
    result = frame.copy()
    result["kpi_skill_interaction"] = result["kpi_score"] * result["soft_skill_score"]
    result["experience_adjusted_kpi"] = result["kpi_score"] / (result["years_experience"] + 1.0)
    return result
