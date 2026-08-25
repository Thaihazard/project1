import joblib
import pandas as pd
from typing import Dict, Any

class SalaryPredictor:
    """A class used to load a trained salary prediction model pipeline and predict salaries for single or batch data."""

    def __init__(self, model_path: str = "model_registry/best_salary_model.pkl") -> None:
        """Initialize the SalaryPredictor with the specified model artifact path."""
        self.model_path = model_path
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]

    def predict_single(self, data_dict: Dict[str, Any]) -> float:
        """Predict salary for a single data record represented as a dictionary."""
        df = pd.DataFrame([data_dict])
        prediction = self.pipeline.predict(df)[0]
        return float(prediction)

    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
        """Predict salaries for a batch of records provided in a pandas DataFrame."""
        predictions = self.pipeline.predict(df)
        return pd.Series(predictions, name="Predicted_Salary")

if __name__ == "__main__":
    predictor = SalaryPredictor()
    sample = {
        'Age': 32,
        'Gender': 'Male',
        'Education Level': "Master's",
        'Job Title': 'Data Scientist',
        'Years of Experience': 5.0
    }
    print(f"Sample prediction: ${predictor.predict_single(sample):,.2f}")
