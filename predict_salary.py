import joblib
import argparse
import sys
import pandas as pd
from typing import Dict, Any
from pathlib import Path
from preprocessing import CATEGORICAL_FEATURES, validate_model_input_values

class SalaryPredictor:
    """A class used to load a trained salary prediction model pipeline and predict salaries for single or batch data."""

    def __init__(self, model_path: str = None) -> None:
        """Initialize the SalaryPredictor with the specified model artifact path."""
        project_root = Path(__file__).resolve().parent
        if model_path is None:
            model_path = project_root / "model_registry" / "best_salary_model.pkl"
        else:
            model_path = Path(model_path)
            if not model_path.is_absolute():
                model_path = project_root / model_path

        self.model_path = model_path
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]

    def _validate_input(self, df: pd.DataFrame) -> None:
        validate_model_input_values(df)
        self.pipeline.named_steps["schema"].validate_consistency(df)

        schema = self.pipeline.named_steps["schema"]
        prepared = schema.transform(df)
        prepared = self.pipeline.named_steps["cleaner"].transform(prepared)
        preprocessor = self.pipeline.named_steps["model"].regressor_.named_steps["preprocessor"]
        encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
        unsupported = []
        for column, categories in zip(CATEGORICAL_FEATURES, encoder.categories_):
            unseen = ~prepared[column].isin(categories)
            if unseen.any():
                unsupported.append(column)
        if unsupported:
            raise ValueError(f"Unseen categorical values unsupported by this model in: {unsupported}")

    def predict_single(self, data_dict: Dict[str, Any]) -> float:
        """Predict salary for a single data record represented as a dictionary."""
        df = pd.DataFrame([data_dict])
        self._validate_input(df)
        prediction = self.pipeline.predict(df)[0]
        return float(prediction)

    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
        """Predict salaries for a batch of records provided in a pandas DataFrame."""
        self._validate_input(df)
        predictions = self.pipeline.predict(df)
        return pd.Series(predictions, name="Predicted_Salary")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Dự đoán lương từ một file CSV.")
    parser.add_argument(
        "--input",
        default="input/predict.csv",
        help="Đường dẫn file CSV đầu vào.",
    )
    parser.add_argument(
        "--output",
        default="output/salary_predictions.csv",
        help="Đường dẫn file CSV kết quả.",
    )
    parser.add_argument(
        "--model",
        default="model_registry/best_salary_model.pkl",
        help="Đường dẫn model artifact (.pkl).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = project_root / input_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    people = pd.read_csv(input_path)
    predictor = SalaryPredictor(model_path=args.model)
    result = people.copy()
    result["Predicted_Salary"] = predictor.predict_batch(people).to_numpy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"Đã dự đoán {len(result)} dòng.")
    print(f"File kết quả: {output_path}")
