from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    transformers = []
    if numeric_features:
        transformers.append(("numeric", numeric, numeric_features))
    if categorical_features:
        transformers.append(("categorical", categorical, categorical_features))
    if not transformers:
        raise ValueError("At least one configured model feature is required")
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)
