from __future__ import annotations
from typing import Any, List, Dict


def build_explainer(model):
    """Build a TreeExplainer for a fitted XGBoost model."""
    import shap

    return shap.TreeExplainer(model)


def explain_instance(explainer: Any, transformed_row: Any, feature_names: List[str]) -> List[Dict[str, Any]]:
    """Explain single inference row and return feature contribution breakdown."""
    try:
        explanation = explainer(transformed_row)
        values = explanation.values[0]
        return [
            {"feature": name, "impact": float(val), "explanation": "SHAP feature contribution"}
            for name, val in zip(feature_names, values)
        ]
    except Exception as e:
        return [{"feature": name, "impact": 0.0, "explanation": str(e)} for name in feature_names]

