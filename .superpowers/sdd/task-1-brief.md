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

