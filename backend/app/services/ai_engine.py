from pathlib import Path

from app.core.config import settings
from app.schemas.ai import AIPredictInput, AIPredictOutput, FeatureContribution


class SalaryPredictionService:
    """Uses a loaded model when available; otherwise exposes a transparent demo baseline."""

    def __init__(self) -> None:
        self.model = None
        self.preprocessor = None
        self.explainer = None
        model_path: Path = settings.model_path
        preprocessor_path: Path = settings.scaler_pipeline_path
        if model_path.is_file() and preprocessor_path.is_file():
            try:
                import joblib
                self.model = joblib.load(model_path)
                self.preprocessor = joblib.load(preprocessor_path)
                if settings.shap_explainer_path.is_file():
                    self.explainer = joblib.load(settings.shap_explainer_path)
            except Exception:
                # Missing or incompatible optional artifacts must not prevent API startup.
                self.model = None
                self.preprocessor = None
                self.explainer = None

    def predict(self, payload: AIPredictInput) -> AIPredictOutput:
        if self.model is not None:
            import pandas as pd

            features = pd.DataFrame([{
                "current_salary": payload.current_salary,
                "kpi_score": payload.kpi_score,
                "soft_skill_score": payload.soft_skill_score,
                "years_experience": payload.years_experience,
                "certification_count": payload.certification_count,
                "kpi_skill_interaction": payload.kpi_score * payload.soft_skill_score,
                "experience_adjusted_kpi": payload.kpi_score / (payload.years_experience + 1.0),
            }])
            transformed = self.preprocessor.transform(features)
            median = float(self.model.predict(transformed)[0])
            version = "xgboost_salary_v1"
            method = "XGBoost prediction; SHAP explainer unavailable"
            contributions: list[FeatureContribution] = []
            disclaimer = "Model output is advisory and requires human review before any compensation decision."
            if self.explainer is not None:
                try:
                    raw_values = self.explainer(transformed).values[0]
                    names = ["Current salary", "KPI", "Soft skills", "Experience", "Certifications", "KPI × skills", "Experience-adjusted KPI"]
                    contributions = [FeatureContribution(feature=name, impact=float(value), explanation="SHAP feature contribution for this prediction.") for name, value in zip(names, raw_values)]
                    method = "SHAP"
                except (AttributeError, TypeError, ValueError, IndexError):
                    method = "XGBoost prediction; SHAP explanation failed"
        else:
            median = payload.current_salary + (payload.kpi_score - 80) * 150_000 + (payload.soft_skill_score - 4) * 500_000 + (payload.years_experience - 5) * 100_000 + payload.certification_count * 500_000
            version = "baseline-demo-v1"
            method = "transparent baseline contributions (not SHAP)"
            contributions = [
                FeatureContribution(feature="KPI", impact=(payload.kpi_score - 80) * 150_000, explanation="Difference from baseline KPI score of 80."),
                FeatureContribution(feature="Soft skills", impact=(payload.soft_skill_score - 4) * 500_000, explanation="Difference from baseline score of 4/5."),
                FeatureContribution(feature="Experience", impact=(payload.years_experience - 5) * 100_000, explanation="Difference from baseline experience of 5 years."),
                FeatureContribution(feature="Certifications", impact=payload.certification_count * 500_000, explanation="Demo assumption of 500,000 VND per certification."),
            ]
            disclaimer = "Demo estimate only. No trained model is installed; this is not a real salary recommendation. Human review is required."
        median = max(0, median)
        return AIPredictOutput(
            min_salary=round(median * 0.9), median_salary=round(median), max_salary=round(median * 1.1),
            change_percent=round((median / payload.current_salary - 1) * 100, 2), model_version=version,
            explanation_method=method, contributions=contributions, disclaimer=disclaimer,
        )


salary_prediction_service = SalaryPredictionService()
