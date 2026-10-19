from __future__ import annotations


def build_explainer(model):
    """Build a TreeExplainer for a fitted XGBoost model."""
    import shap

    return shap.TreeExplainer(model)
