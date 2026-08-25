# ML Tier OOP Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the script-based ML tier into a robust Object-Oriented Programming (OOP) architecture with automatic target transformation (`TransformedTargetRegressor`), making it easily pluggable into a Streamlit application or downstream APIs.

**Architecture:** Encapsulate each tier stage into dedicated classes (`SalaryPipelineFactory`, `SalaryModelTrainer`, `SalaryPredictor`, `ModelBenchmarker`, `SalaryExplainer`). Wrap models with `TransformedTargetRegressor` to natively handle `log1p`/`expm1` transformations inside the pipeline.

**Tech Stack:** Python 3.9+, scikit-learn, pandas, numpy, xgboost, catboost, shap, joblib, pytest.

## Global Constraints

- Python files must use absolute paths or relative paths from project root.
- All classes must follow PEP 8 standards with clear docstrings and typed methods.
- Pipeline artifacts must automatically handle target transformations so `predict()` outputs real salary amounts ($).

---

## File Structure

- Create: `predict_salary.py` (`SalaryPredictor`)
- Modify: `preprocessing.py` (`SalaryCleaner`, `SalaryPipelineFactory`)
- Modify: `train_final_model.py` (`SalaryModelTrainer`)
- Modify: `benchmark_salary_models.py` (`ModelBenchmarker`)
- Modify: `explainability.py` (`SalaryExplainer`)
- Create: `tests/test_ml_oop.py` (Unit tests for all OOP classes)

---

### Task 1: Refactor `preprocessing.py` with `SalaryPipelineFactory`

**Files:**
- Modify: `preprocessing.py`
- Test: `tests/test_ml_oop.py`

**Interfaces:**
- Consumes: Raw CSV dataset path.
- Produces: `SalaryCleaner` and a scikit-learn `Pipeline` / `TransformedTargetRegressor`.

- [ ] **Step 1: Write the failing test for `SalaryCleaner` and `SalaryPipelineFactory`**

```python
import pandas as pd
import numpy as np
from preprocessing import SalaryCleaner, SalaryPipelineFactory

def test_salary_cleaner():
    df = pd.DataFrame({
        'Age': [25, 25, 30],
        'Gender': ['Male', 'Male', 'Female'],
        'Education Level': ["bachelor's", "Bachelor'S Degree", "Master's"],
        'Job Title': ['Software Engineer', 'Software Engineer', 'Data Scientist'],
        'Salary': [50000, 50000, 80000]
    })
    cleaner = SalaryCleaner(rare_threshold=2)
    cleaned = cleaner.fit_transform(df)
    assert len(cleaned) == 2 # Drop duplicates
    assert 'Software Engineer' in cleaned['Job Title'].values
```

- [ ] **Step 2: Run test to verify it fails (or passes if cleaner already works, but check factory)**

Run: `pytest tests/test_ml_oop.py -k test_salary_cleaner -v`
Expected: FAIL or PASS depending on test file existence.

- [ ] **Step 3: Update `preprocessing.py` with `SalaryPipelineFactory`**

```python
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

class SalaryCleaner(BaseEstimator, TransformerMixin):
    def __init__(self, rare_threshold=20):
        self.rare_threshold = rare_threshold
        self.rare_job_titles_ = set()

    def fit(self, X, y=None):
        X_ = X.copy()
        X_['Education Level'] = X_['Education Level'].str.strip().str.title()
        mapping = {
            "Bachelor'S": "Bachelor's",
            "Bachelor'S Degree": "Bachelor's",
            "Master'S": "Master's",
            "Master'S Degree": "Master's",
            "Phd": "PhD",
            "Ph.D.": "PhD"
        }
        X_['Education Level'] = X_['Education Level'].replace(mapping)
        
        if 'Job Title' in X_.columns:
            vc = X_['Job Title'].value_counts()
            self.rare_job_titles_ = set(vc[vc < self.rare_threshold].index)
        return self

    def transform(self, X):
        X_ = X.copy()
        if 'Salary' in X_.columns:
            X_ = X_.drop_duplicates()
            X_ = X_.dropna()
        else:
            X_ = X_.dropna()
            
        X_['Education Level'] = X_['Education Level'].str.strip().str.title()
        mapping = {
            "Bachelor'S": "Bachelor's",
            "Bachelor'S Degree": "Bachelor's",
            "Master'S": "Master's",
            "Master'S Degree": "Master's",
            "Phd": "PhD",
            "Ph.D.": "PhD"
        }
        X_['Education Level'] = X_['Education Level'].replace(mapping)
        
        if 'Job Title' in X_.columns:
            X_['Job Title'] = X_['Job Title'].apply(
                lambda x: 'Other' if x in self.rare_job_titles_ else x
            )
            
        return X_

class SalaryPipelineFactory:
    @staticmethod
    def create_pipeline(regressor, rare_threshold=20):
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), ['Age', 'Years of Experience']),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['Gender', 'Education Level', 'Job Title'])
            ]
        )
        
        model_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', regressor)
        ])
        
        # Wrap with TransformedTargetRegressor for automatic log1p/expm1
        transformed_model = TransformedTargetRegressor(
            regressor=model_pipeline,
            func=np.log1p,
            inverse_func=np.expm1
        )
        
        full_pipeline = Pipeline([
            ('cleaner', SalaryCleaner(rare_threshold=rare_threshold)),
            ('model', transformed_model)
        ])
        return full_pipeline
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ml_oop.py -k test_salary_cleaner -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add preprocessing.py tests/test_ml_oop.py
git commit -m "refactor: update preprocessing.py with SalaryPipelineFactory and TransformedTargetRegressor"
```

---

### Task 2: Refactor `train_final_model.py` into `SalaryModelTrainer`

**Files:**
- Modify: `train_final_model.py`
- Test: `tests/test_ml_oop.py`

**Interfaces:**
- Consumes: `SalaryPipelineFactory`
- Produces: `model_registry/best_salary_model.pkl` containing the trained full pipeline and metrics.

- [ ] **Step 1: Write the test for `SalaryModelTrainer`**

```python
import os
from train_final_model import SalaryModelTrainer

def test_salary_model_trainer(tmp_path):
    model_path = tmp_path / "best_salary_model.pkl"
    trainer = SalaryModelTrainer(data_path="archive/Salary_Data.csv", model_output_path=str(model_path))
    metrics = trainer.train()
    assert os.path.exists(model_path)
    assert 'MAE' in metrics
    assert 'R2' in metrics
```

- [ ] **Step 2: Rewrite `train_final_model.py` using `SalaryModelTrainer` class**

```python
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryPipelineFactory

class SalaryModelTrainer:
    def __init__(self, data_path="archive/Salary_Data.csv", model_output_path="model_registry/best_salary_model.pkl"):
        self.data_path = data_path
        self.model_output_path = model_output_path

    def train(self):
        df = pd.read_csv(self.data_path)
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
        
        X_train = train_df.drop(columns=['Salary'])
        y_train = train_df['Salary']
        
        X_test = test_df.drop(columns=['Salary'])
        y_test = test_df['Salary']
        
        regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        pipeline = SalaryPipelineFactory.create_pipeline(regressor=regressor, rare_threshold=20)
        pipeline.fit(X_train, y_train)
        
        preds = pipeline.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        os.makedirs(os.path.dirname(self.model_output_path), exist_ok=True)
        joblib.dump({
            "pipeline": pipeline,
            "metrics": {"MAE": mae, "RMSE": rmse, "R2": r2},
            "features": list(X_train.columns)
        }, self.model_output_path)
        
        return {"MAE": mae, "RMSE": rmse, "R2": r2}

if __name__ == "__main__":
    trainer = SalaryModelTrainer()
    metrics = trainer.train()
    print(f"Trained & Saved. Metrics: {metrics}")
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_ml_oop.py -k test_salary_model_trainer -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add train_final_model.py tests/test_ml_oop.py
git commit -m "refactor: encapsulate training logic in SalaryModelTrainer class"
```

---

### Task 3: Create `predict_salary.py` with `SalaryPredictor`

**Files:**
- Create: `predict_salary.py`
- Test: `tests/test_ml_oop.py`

**Interfaces:**
- Consumes: `model_registry/best_salary_model.pkl`
- Produces: `predict_single(data_dict)` and `predict_batch(df)` returning real salary values.

- [ ] **Step 1: Write test for `SalaryPredictor`**

```python
import pandas as pd
from predict_salary import SalaryPredictor

def test_salary_predictor():
    predictor = SalaryPredictor(model_path="model_registry/best_salary_model.pkl")
    sample = {
        'Age': 28,
        'Gender': 'Female',
        'Education Level': "Bachelor's",
        'Job Title': 'Software Engineer',
        'Years of Experience': 3.0
    }
    pred = predictor.predict_single(sample)
    assert isinstance(pred, float)
    assert pred > 0
```

- [ ] **Step 2: Create `predict_salary.py`**

```python
import joblib
import pandas as pd

class SalaryPredictor:
    def __init__(self, model_path="model_registry/best_salary_model.pkl"):
        self.model_path = model_path
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]

    def predict_single(self, data_dict: dict) -> float:
        df = pd.DataFrame([data_dict])
        prediction = self.pipeline.predict(df)[0]
        return float(prediction)

    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
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
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_ml_oop.py -k test_salary_predictor -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add predict_salary.py tests/test_ml_oop.py
git commit -m "feat: implement SalaryPredictor class in predict_salary.py"
```

---

### Task 4: Refactor `benchmark_salary_models.py` into `ModelBenchmarker`

**Files:**
- Modify: `benchmark_salary_models.py`
- Test: `tests/test_ml_oop.py`

**Interfaces:**
- Consumes: Raw dataset path.
- Produces: Summary DataFrame with cross-validation metrics across models.

- [ ] **Step 1: Write test for `ModelBenchmarker`**

```python
import pandas as pd
from benchmark_salary_models import ModelBenchmarker

def test_model_benchmarker():
    benchmarker = ModelBenchmarker(data_path="archive/Salary_Data.csv", n_splits=2)
    summary_df = benchmarker.evaluate()
    assert isinstance(summary_df, pd.DataFrame)
    assert 'Model' in summary_df.columns
    assert 'MAE' in summary_df.columns
```

- [ ] **Step 2: Refactor `benchmark_salary_models.py`**

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryPipelineFactory

class ModelBenchmarker:
    def __init__(self, data_path="archive/Salary_Data.csv", n_splits=5):
        self.data_path = data_path
        self.n_splits = n_splits

    def _mape(self, y_true, y_pred):
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    def evaluate(self):
        df = pd.read_csv(self.data_path)
        from preprocessing import SalaryCleaner
        cleaner = SalaryCleaner(rare_threshold=20)
        df_clean = cleaner.fit_transform(df)
        
        X = df_clean.drop(columns=['Salary'])
        y = df_clean['Salary']
        
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)
        
        models = {
            "Ridge": SalaryPipelineFactory.create_pipeline(Ridge(alpha=1.0)),
            "RandomForest": SalaryPipelineFactory.create_pipeline(RandomForestRegressor(n_estimators=50, random_state=42)),
            "XGBoost": SalaryPipelineFactory.create_pipeline(XGBRegressor(n_estimators=50, learning_rate=0.1, random_state=42, n_jobs=1))
        }
        
        results = {name: {'MAE': [], 'RMSE': [], 'R2': [], 'MAPE': []} for name in models.keys()}
        
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            for name, model in models.items():
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                
                mae = mean_absolute_error(y_val, preds)
                rmse = np.sqrt(mean_squared_error(y_val, preds))
                r2 = r2_score(y_val, preds)
                mape = self._mape(y_val, preds)
                
                results[name]['MAE'].append(mae)
                results[name]['RMSE'].append(rmse)
                results[name]['R2'].append(r2)
                results[name]['MAPE'].append(mape)
                
        summary = []
        for name, metrics in results.items():
            summary.append({
                "Model": name,
                "MAE": f"{np.mean(metrics['MAE']):.2f} ± {np.std(metrics['MAE']):.2f}",
                "RMSE": f"{np.mean(metrics['RMSE']):.2f} ± {np.std(metrics['RMSE']):.2f}",
                "R2": f"{np.mean(metrics['R2']):.3f} ± {np.std(metrics['R2']):.3f}",
                "MAPE (%)": f"{np.mean(metrics['MAPE']):.2f}% ± {np.std(metrics['MAPE']):.2f}%"
            })
        return pd.DataFrame(summary)

if __name__ == "__main__":
    benchmarker = ModelBenchmarker()
    print(benchmarker.evaluate().to_string(index=False))
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_ml_oop.py -k test_model_benchmarker -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add benchmark_salary_models.py tests/test_ml_oop.py
git commit -m "refactor: encapsulate benchmark logic in ModelBenchmarker class"
```

---

### Task 5: Refactor `explainability.py` into `SalaryExplainer`

**Files:**
- Modify: `explainability.py`
- Test: `tests/test_ml_oop.py`

**Interfaces:**
- Consumes: Trained model artifact.
- Produces: SHAP values and fairness residual metrics dataframe.

- [ ] **Step 1: Write test for `SalaryExplainer`**

```python
import pandas as pd
from explainability import SalaryExplainer

def test_salary_explainer():
    explainer = SalaryExplainer(model_path="model_registry/best_salary_model.pkl", data_path="archive/Salary_Data.csv")
    fairness_df = explainer.compute_fairness()
    assert isinstance(fairness_df, pd.DataFrame)
    assert 'AbsError' in fairness_df.columns
```

- [ ] **Step 2: Refactor `explainability.py`**

```python
import joblib
import pandas as pd
import numpy as np
import shap

class SalaryExplainer:
    def __init__(self, model_path="model_registry/best_salary_model.pkl", data_path="archive/Salary_Data.csv"):
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]
        self.data_path = data_path

    def compute_fairness(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)
        # Use cleaner from pipeline or standalone
        cleaner = self.pipeline.named_steps['cleaner']
        df_clean = cleaner.transform(df)
        
        X = df_clean.drop(columns=['Salary'])
        y = df_clean['Salary']
        
        preds = self.pipeline.predict(X)
        residuals = y - preds
        
        df_clean['Prediction'] = preds
        df_clean['Residual'] = residuals
        df_clean['AbsError'] = np.abs(residuals)
        return df_clean

if __name__ == "__main__":
    explainer = SalaryExplainer()
    df_clean = explainer.compute_fairness()
    print("Fairness by Gender:")
    print(df_clean.groupby('Gender')['AbsError'].mean())
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_ml_oop.py -k test_salary_explainer -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add explainability.py tests/test_ml_oop.py
git commit -m "refactor: encapsulate explainability and fairness checks in SalaryExplainer class"
```
