import numpy as np
import pandas as pd
from pathlib import Path
import sys
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import MODEL_FEATURES, SalaryPipelineFactory, validate_model_input_values

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def make_regressor(name: str, random_state: int = 42):
    """Create a fresh instance of one of the supported regression models."""
    if name == "ridge":
        return Ridge(alpha=1.0)
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=150, max_depth=15, random_state=random_state, n_jobs=-1
        )
    if name == "xgboost":
        return XGBRegressor(
            n_estimators=150, learning_rate=0.1, random_state=random_state, n_jobs=1
        )
    if name == "catboost":
        return CatBoostRegressor(
            iterations=200, learning_rate=0.1, verbose=0, random_seed=random_state
        )
    raise ValueError(f"Unsupported model: {name}")


MODEL_NAMES = ("ridge", "random_forest", "xgboost", "catboost")

class ModelBenchmarker:
    """Class to benchmark different regression models for salary prediction using K-Fold cross-validation."""

    def __init__(self, data_path: str = None, n_splits: int = 5,
                rare_threshold: int = 20, random_state: int = 42) -> None:
        """Initialize the ModelBenchmarker.

        Args:
            data_path: Path to the raw CSV dataset.
            n_splits: Number of folds for K-Fold cross-validation.
        """
        project_root = Path(__file__).resolve().parent
        if data_path is None:
            data_path = project_root / "archive" / "Salary_Data.csv"
        else:
            data_path = Path(data_path)
            if not data_path.is_absolute():
                data_path = project_root / data_path

        self.data_path = data_path
        self.n_splits = n_splits
        self.rare_threshold = rare_threshold
        self.random_state = random_state

    def _mape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate MAPE over non-zero targets; MAPE is undefined at zero."""
        nonzero = y_true != 0
        if not np.any(nonzero):
            return np.nan
        return np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100

    def benchmark(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Cross-validate candidate pipelines on caller-provided training data.

        Returns:
            Numeric mean and standard deviation metrics for each candidate.
        """
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        results = {name: {'MAE': [], 'RMSE': [], 'R2': [], 'MAPE': []} for name in MODEL_NAMES}

        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            for name in MODEL_NAMES:
                model = SalaryPipelineFactory.create_pipeline(
                    make_regressor(name, self.random_state),
                    rare_threshold=self.rare_threshold,
                )
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                actuals = y_val.values

                mae = mean_absolute_error(actuals, preds)
                rmse = np.sqrt(mean_squared_error(actuals, preds))
                r2 = r2_score(actuals, preds)
                mape = self._mape(actuals, preds)

                results[name]['MAE'].append(mae)
                results[name]['RMSE'].append(rmse)
                results[name]['R2'].append(r2)
                results[name]['MAPE'].append(mape)

        summary = []
        for name, metrics in results.items():
            row = {"Model": name}
            for metric, values in metrics.items():
                row[metric] = float(np.mean(values))
                row[f"{metric}_std"] = float(np.std(values))
            summary.append(row)
        return pd.DataFrame(summary)

    def evaluate(self) -> pd.DataFrame:
        """Load the full dataset and print cross-validation comparison metrics."""
        df = pd.read_csv(self.data_path).drop_duplicates().dropna(subset=["Salary", *MODEL_FEATURES])
        validate_model_input_values(df)
        if not np.isfinite(pd.to_numeric(df["Salary"], errors="coerce")).all() or (df["Salary"] <= 0).any():
            raise ValueError("Salary must contain finite positive numeric values for log1p training.")
        scores = self.benchmark(df.drop(columns=['Salary']), df['Salary'])
        display = scores.copy()
        for metric, precision in (("MAE", 2), ("RMSE", 2), ("R2", 3), ("MAPE", 2)):
            display[metric] = scores.apply(
                lambda row: f"{row[metric]:.{precision}f} ± {row[f'{metric}_std']:.{precision}f}",
                axis=1,
            )
        display = display[["Model", "MAE", "RMSE", "R2", "MAPE"]]
        display = display.rename(columns={"MAPE": "MAPE (%)"})
        print(f"\n================ MODEL BAKE-OFF RESULTS ({self.n_splits}-Fold CV) ================")
        print(display.to_string(index=False))
        return scores


if __name__ == "__main__":
    benchmarker = ModelBenchmarker()
    benchmarker.evaluate()
