import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


NUMERIC_FEATURES = [
    "Age",
    "Years of Experience",
    "Education_Ordinal",
    "Career_Start_Age",
    "Seniority_Level",
    "sim_avg_hours_per_week",
    "sim_projects_completed",
    "sim_years_at_company",
    "sim_num_job_changes",
    "sim_absence_days_per_month",
    "sim_location_cost_level",
]

CATEGORICAL_FEATURES = [
    "Gender",
    "Education Level",
    "Job Title",
    "Job_Family",
    "sim_employment_type",
    "sim_work_mode",
    "sim_company_size",
    "sim_industry",
]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

EDUCATION_ORDINAL = {
    "high school": 0,
    "bachelor's": 1,
    "bachelor's degree": 1,
    "master's": 2,
    "master's degree": 2,
    "phd": 3,
    "ph.d.": 3,
}


def validate_feature_consistency(X):
    """Raise when supplied derived features conflict with their source fields."""
    issues = []
    if {"Age", "Years of Experience", "Career_Start_Age"}.issubset(X.columns):
        age = pd.to_numeric(X["Age"], errors="coerce")
        experience = pd.to_numeric(X["Years of Experience"], errors="coerce")
        start_age = pd.to_numeric(X["Career_Start_Age"], errors="coerce")
        complete = age.notna() & experience.notna() & start_age.notna()
        bad = complete & ~np.isclose(start_age, age - experience, atol=1e-6, rtol=0)
        if bad.any():
            issues.append(f"Career_Start_Age must equal Age - Years of Experience (rows {list(X.index[bad][:5])})")

    if {"Education Level", "Education_Ordinal"}.issubset(X.columns):
        education = X["Education Level"].astype("string").str.strip().str.casefold()
        expected = education.map(EDUCATION_ORDINAL)
        ordinal = pd.to_numeric(X["Education_Ordinal"], errors="coerce")
        complete = expected.notna() & ordinal.notna()
        bad = complete & (expected != ordinal)
        if bad.any():
            issues.append(f"Education_Ordinal conflicts with Education Level (rows {list(X.index[bad][:5])})")

    for derived in ("Job_Family", "Seniority_Level"):
        if {"Job Title", derived}.issubset(X.columns):
            pairs = X[["Job Title", derived]].copy()
            pairs["Job Title"] = pairs["Job Title"].astype("string").str.strip()
            pairs = pairs.dropna().drop_duplicates()
            counts = pairs.groupby("Job Title")[derived].nunique()
            conflicts = counts[counts > 1].index.tolist()
            if conflicts:
                issues.append(f"{derived} is inconsistent for Job Title values {conflicts[:5]}")

    if issues:
        raise ValueError("Inconsistent model input fields: " + "; ".join(issues))


def validate_model_input_values(X):
    """Validate completeness, numeric domains, and derived-field relationships."""
    missing_columns = [column for column in MODEL_FEATURES if column not in X.columns]
    if missing_columns:
        raise ValueError(f"Missing required model fields: {missing_columns}")
    empty = X[MODEL_FEATURES].isna().copy()
    for column in CATEGORICAL_FEATURES:
        empty[column] |= X[column].astype("string").str.strip().eq("").fillna(False)
    numeric = X[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    for column in NUMERIC_FEATURES:
        empty[column] |= numeric[column].isna()
    invalid_columns = empty.columns[empty.any()].tolist()
    if invalid_columns:
        raise ValueError(f"Missing or invalid values in model fields: {invalid_columns}")
    non_finite = ~np.isfinite(numeric)
    if non_finite.any().any():
        raise ValueError(f"Non-finite numeric values in: {non_finite.columns[non_finite.any()].tolist()}")

    rules = {
        "Age": numeric["Age"] > 0,
        "Years of Experience": (numeric["Years of Experience"] >= 0)
        & (numeric["Years of Experience"] <= numeric["Age"]),
        "Career_Start_Age": (numeric["Career_Start_Age"] >= 0)
        & (numeric["Career_Start_Age"] <= numeric["Age"]),
        "Education_Ordinal": numeric["Education_Ordinal"].isin([0, 1, 2, 3]),
        "Seniority_Level": numeric["Seniority_Level"].isin([1, 2, 3, 4, 5]),
        "sim_avg_hours_per_week": numeric["sim_avg_hours_per_week"].between(0, 168),
        "sim_projects_completed": numeric["sim_projects_completed"] >= 0,
        "sim_years_at_company": (numeric["sim_years_at_company"] >= 0)
        & (numeric["sim_years_at_company"] <= numeric["Years of Experience"]),
        "sim_num_job_changes": numeric["sim_num_job_changes"] >= 0,
        "sim_absence_days_per_month": numeric["sim_absence_days_per_month"].between(0, 31),
        "sim_location_cost_level": numeric["sim_location_cost_level"].isin([1, 2, 3]),
    }
    invalid = [column for column, valid in rules.items() if not valid.all()]
    if invalid:
        raise ValueError(f"Out-of-range numeric values in: {invalid}")

    normalized_education = X["Education Level"].astype("string").str.strip().str.casefold()
    unknown_education = normalized_education[~normalized_education.isin(EDUCATION_ORDINAL)].unique().tolist()
    if unknown_education:
        raise ValueError(f"Unsupported Education Level values: {unknown_education[:5]}")
    validate_feature_consistency(X)


class SalaryFeatureSchema(BaseEstimator, TransformerMixin):
    """Align input data to all model features and coerce values to usable types."""

    def fit(self, X, y=None):
        validate_model_input_values(X)
        self.title_to_family_ = self._learn_title_mapping(X, "Job_Family")
        self.title_to_seniority_ = self._learn_title_mapping(X, "Seniority_Level")
        return self

    @staticmethod
    def _learn_title_mapping(X, feature):
        if not {"Job Title", feature}.issubset(X.columns):
            return {}
        pairs = X[["Job Title", feature]].copy()
        pairs["Job Title"] = pairs["Job Title"].astype("string").str.strip()
        pairs = pairs.dropna().drop_duplicates()
        counts = pairs.groupby("Job Title")[feature].nunique()
        conflicts = counts[counts > 1].index.tolist()
        if conflicts:
            raise ValueError(f"{feature} has conflicting values for titles: {conflicts[:5]}")
        return pairs.set_index("Job Title")[feature].to_dict()

    def validate_consistency(self, X):
        validate_feature_consistency(X)
        title = X["Job Title"].astype("string").str.strip()
        for column, mapping in (("Job_Family", self.title_to_family_), ("Seniority_Level", self.title_to_seniority_)):
            if not mapping:
                continue
            expected = title.map(mapping)
            provided = X[column]
            known = expected.notna() & provided.notna()
            if column == "Seniority_Level":
                bad = known & ~np.isclose(
                    pd.to_numeric(expected, errors="coerce"),
                    pd.to_numeric(provided, errors="coerce"),
                    atol=1e-6,
                    rtol=0,
                )
            else:
                bad = known & (expected.astype("string") != provided.astype("string"))
            if bad.any():
                raise ValueError(
                    f"{column} conflicts with Job Title in rows {list(X.index[bad][:5])}"
                )

    def transform(self, X):
        X_ = X.copy()
        for column in MODEL_FEATURES:
            if column not in X_.columns:
                X_[column] = np.nan

        X_ = X_[MODEL_FEATURES]
        for column in NUMERIC_FEATURES:
            X_[column] = pd.to_numeric(X_[column], errors="coerce")
        return X_

class SalaryCleaner(BaseEstimator, TransformerMixin):
    def __init__(self, rare_threshold=20):
        self.rare_threshold = rare_threshold
        self.rare_job_titles_ = set()

    def _clean_education(self, series: pd.Series) -> pd.Series:
        mapping = {
            "Bachelor'S": "Bachelor's",
            "Bachelor'S Degree": "Bachelor's",
            "Master'S": "Master's",
            "Master'S Degree": "Master's",
            "Phd": "PhD",
            "Ph.D.": "PhD"
        }
        cleaned = series.astype(str).str.strip().str.title()
        cleaned = cleaned.replace(mapping)
        cleaned = cleaned.where(series.notna(), np.nan)
        return cleaned

    def fit(self, X, y=None):
        X_ = X.copy()
        if 'Education Level' in X_.columns:
            X_['Education Level'] = self._clean_education(X_['Education Level'])

        if 'Job Title' in X_.columns:
            X_['Job Title'] = X_['Job Title'].astype('string').str.strip()
            vc = X_['Job Title'].value_counts()
            self.rare_job_titles_ = set(vc[vc < self.rare_threshold].index)
            self.known_job_titles_ = set(X_['Job Title'].dropna().unique())
        return self

    def transform(self, X):
        X_ = X.copy()

        if 'Education Level' in X_.columns:
            X_['Education Level'] = self._clean_education(X_['Education Level'])

        if 'Job Title' in X_.columns:
            X_['Job Title'] = X_['Job Title'].astype('string').str.strip()
            known = getattr(self, 'known_job_titles_', None)
            X_['Job Title'] = X_['Job Title'].apply(
                lambda x: 'Other' if (pd.notna(x) and (x in self.rare_job_titles_ or (known is not None and x not in known))) else x
            )

        return X_

def load_and_clean_data(filepath=None):
    if filepath is None:
        filepath = Path(__file__).resolve().parent / "archive" / "Salary_Data.csv"
    else:
        filepath = Path(filepath).resolve()

    df = pd.read_csv(filepath).drop_duplicates().dropna(subset=["Salary", *MODEL_FEATURES])
    validate_model_input_values(df)
    if (pd.to_numeric(df["Salary"], errors="coerce") <= 0).any():
        raise ValueError("Salary must contain positive numeric values for log1p target transformation.")
    X = df.drop(columns=['Salary'])
    y = df['Salary']
    return X, y

def build_preprocessor(numeric_features=None, categorical_features=None):
    numeric_features = NUMERIC_FEATURES if numeric_features is None else numeric_features
    categorical_features = CATEGORICAL_FEATURES if categorical_features is None else categorical_features
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    return preprocessor

class SalaryPipelineFactory:
    @staticmethod
    def create_pipeline(regressor, rare_threshold=20):
        preprocessor = build_preprocessor()

        model_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', regressor)
        ])

        transformed_model = TransformedTargetRegressor(
            regressor=model_pipeline,
            func=np.log1p,
            inverse_func=np.expm1
        )

        full_pipeline = Pipeline([
            ('schema', SalaryFeatureSchema()),
            ('cleaner', SalaryCleaner(rare_threshold=rare_threshold)),
            ('model', transformed_model)
        ])
        return full_pipeline

if __name__ == "__main__":
    X, y = load_and_clean_data()
    print(f"Cleaned X shape: {X.shape}, y shape: {y.shape}")
    print("Education levels:", X['Education Level'].unique())
    print("Sample job titles:", list(X['Job Title'].unique())[:5])
