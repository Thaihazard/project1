import sys
from pathlib import Path

# Setup paths (support both running on host and inside /app container)
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if BACKEND_DIR.is_dir():
    sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))
if Path("/app").is_dir():
    sys.path.insert(0, "/app")

from app.schemas.ai import AIPredictInput
from app.services.ai_engine import SalaryPredictionService

def main():
    print("Initializing SalaryPredictionService...")
    service = SalaryPredictionService()
    
    print(f"Model loaded: {service.model is not None}")
    print(f"Preprocessor loaded: {service.preprocessor is not None}")
    print(f"SHAP Explainer loaded: {service.explainer is not None}")

    test_input = AIPredictInput(
        current_salary=25_000_000,
        kpi_score=92.5,
        soft_skill_score=4.2,
        years_experience=4.0,
        certification_count=2
    )

    print(f"\nMaking prediction with test input: {test_input.model_dump()}")
    output = service.predict(test_input)

    print("\n--- PREDICTION RESULT ---")
    print(f"Model Version: {output.model_version}")
    print(f"Explanation Method: {output.explanation_method}")
    print(f"Min Salary: {output.min_salary:,.0f} ₫")
    print(f"Median Salary: {output.median_salary:,.0f} ₫")
    print(f"Max Salary: {output.max_salary:,.0f} ₫")
    print(f"Change: {output.change_percent}%")
    print("\nFeature Contributions (SHAP):")
    for c in output.contributions:
        print(f"  - {c.feature}: {c.impact:+,.0f} ₫ ({c.explanation})")
    print(f"\nDisclaimer: {output.disclaimer}")

    assert output.model_version == "xgboost_salary_v1", f"Expected xgboost_salary_v1, got {output.model_version}"
    assert output.explanation_method == "SHAP", f"Expected SHAP, got {output.explanation_method}"
    print("\n>>> ALL CHECKS PASSED! AI ENGINE IS OFFICIALLY CONNECTED AND ACTIVE! <<<")

if __name__ == "__main__":
    main()
