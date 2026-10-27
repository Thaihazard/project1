"""Train, evaluate, and package the selected salary model."""

import hashlib
import joblib
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from benchmark_salary_models import MODEL_NAMES, ModelBenchmarker, make_regressor
from preprocessing import MODEL_FEATURES, SalaryPipelineFactory, validate_model_input_values

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = Path(os.getenv("DATA_PATH", "archive/Salary_Data.csv"))
if not DATA_PATH.is_absolute():
    DATA_PATH = PROJECT_ROOT / DATA_PATH
MODEL_TYPE = os.getenv("MODEL_TYPE", "auto").lower()
RARE_THRESHOLD = int(os.getenv("RARE_THRESHOLD", 20))
TEST_SIZE = float(os.getenv("TEST_SIZE", 0.2))
RANDOM_STATE = int(os.getenv("RANDOM_STATE", 42))


class SalaryModelTrainer:
    """Run the complete train/benchmark/evaluate/save workflow."""

    def __init__(
        self,
        data_path=None,
        model_output_path=None,
        model_type="random_forest",
        test_size=0.2,
        random_state=42,
        rare_threshold=20,
        n_splits=5,
    ):
        self.data_path = Path(data_path) if data_path is not None else PROJECT_ROOT / "archive" / "Salary_Data.csv"
        if not self.data_path.is_absolute():
            self.data_path = PROJECT_ROOT / self.data_path

        self.model_output_path = (
            Path(model_output_path)
            if model_output_path is not None
            else PROJECT_ROOT / "model_registry" / "best_salary_model.pkl"
        )
        if not self.model_output_path.is_absolute():
            self.model_output_path = PROJECT_ROOT / self.model_output_path

        self.model_type = model_type.lower()
        self.test_size = test_size
        self.random_state = random_state
        self.rare_threshold = rare_threshold
        self.n_splits = n_splits

    def train(self) -> dict:
        """Select, fit, evaluate, and serialize one salary prediction pipeline."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")
        if self.model_type != "auto" and self.model_type not in MODEL_NAMES:
            raise ValueError(
                f"Unsupported model_type {self.model_type!r}; choose 'auto' or one of {MODEL_NAMES}."
            )

        df = pd.read_csv(self.data_path)
        raw_rows = len(df)
        df = df.drop_duplicates().dropna(subset=["Salary", *MODEL_FEATURES])
        validate_model_input_values(df)
        salary = pd.to_numeric(df["Salary"], errors="coerce")
        if not np.isfinite(salary).all() or (salary <= 0).any():
            raise ValueError("Salary must contain finite positive numeric values for log1p training.")
        df["Salary"] = salary
        print(f"Using {len(df)} complete rows; removed {raw_rows - len(df)} duplicate/incomplete rows.")
        X = df.drop(columns=["Salary"])
        y = df["Salary"]
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
        )

        selected_model = self.model_type
        if selected_model == "auto":
            benchmarker = ModelBenchmarker(
                n_splits=self.n_splits,
                rare_threshold=self.rare_threshold,
                random_state=self.random_state,
            )
            cv_scores = benchmarker.benchmark(X_train, y_train)
            selected_model = cv_scores.loc[cv_scores["MAE"].idxmin(), "Model"]
            print("\nCross-validation results on training split:")
            print(cv_scores[["Model", "MAE", "MAE_std"]].to_string(index=False))
            print(f"Selected model: {selected_model} (lowest mean CV MAE)")

        evaluation_pipeline = SalaryPipelineFactory.create_pipeline(
            make_regressor(selected_model, self.random_state),
            rare_threshold=self.rare_threshold,
        )
        evaluation_pipeline.fit(X_train, y_train)
        predictions = evaluation_pipeline.predict(X_test)

        metrics = {
            "MAE": float(mean_absolute_error(y_test, predictions)),
            "RMSE": float(mean_squared_error(y_test, predictions) ** 0.5),
            "R2": float(r2_score(y_test, predictions)),
        }
        mean_salary = float(y_test.mean())
        mae_percent = metrics["MAE"] / mean_salary * 100

        print(f"Lương trung bình holdout: {mean_salary:.2f}")
        print(f"MAE chiếm {mae_percent:.2f}% lương trung bình")
        print("Đạt mục tiêu MAE < 15%:", mae_percent < 15)

        print(f"\nHoldout metrics for {selected_model}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")

        # Keep holdout metrics tied to the evaluation model, then refit the deployable
        # artifact on every complete labeled row.
        pipeline = SalaryPipelineFactory.create_pipeline(
            make_regressor(selected_model, self.random_state),
            rare_threshold=self.rare_threshold,
        )
        pipeline.fit(X, y)

        self.model_output_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "pipeline": pipeline,
            "evaluation_pipeline": evaluation_pipeline,
            "cleaner": pipeline.named_steps["cleaner"],
            "model_type": selected_model,
            "metrics": metrics,
            "features": list(MODEL_FEATURES),
            "training_rows": len(X),
            "evaluation_training_rows": len(X_train),
            "evaluation_rows": len(X_test),
            "evaluation_indices": X_test.index.tolist(),
            "evaluation_test_size": self.test_size,
            "evaluation_random_state": self.random_state,
            "evaluation_data_sha256": hashlib.sha256(self.data_path.read_bytes()).hexdigest(),
        }
        joblib.dump(artifact, self.model_output_path)
        print(f"Model artifact saved to {self.model_output_path}")
        return metrics


def main():
    trainer = SalaryModelTrainer(
        data_path=DATA_PATH,
        model_type=MODEL_TYPE,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        rare_threshold=RARE_THRESHOLD,
    )
    trainer.train()


if __name__ == "__main__":
    main()
