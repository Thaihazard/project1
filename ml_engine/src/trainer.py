from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yaml
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from xgboost import XGBRegressor

from .evaluator import evaluate_regression
from .feature_engineering import engineer_features
from .preprocessor import build_preprocessor


@dataclass
class TrainingResult:
    model: XGBRegressor
    preprocessor: object
    metrics: dict[str, float]
    cv_mae: float
    transformed_test: object


def _model(params: dict, random_state: int) -> XGBRegressor:
    return XGBRegressor(
        **params,
        objective="reg:squarederror",
        n_jobs=-1,
        random_state=random_state,
        eval_metric="mae",
    )


def tune_hyperparameters(x: pd.DataFrame, y: pd.Series, config: dict, features_config: dict) -> dict:
    import optuna
    from sklearn.pipeline import Pipeline

    random_state = config["model"]["random_state"]
    folds = min(config["model"]["cv_folds"], len(x))
    cv = KFold(n_splits=folds, shuffle=True, random_state=random_state)

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 2, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "subsample": trial.suggest_float("subsample", 0.65, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.65, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 20.0, log=True),
        }
        candidate = Pipeline([
            ("preprocessor", build_preprocessor(features_config["numeric_features"], features_config["categorical_features"])),
            ("model", _model(params, random_state)),
        ])
        return -cross_val_score(candidate, x, y, cv=cv, scoring="neg_mean_absolute_error", n_jobs=1).mean()

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=config["tuning"]["trials"])
    return study.best_params


def train(frame: pd.DataFrame, config: dict, features_config: dict, tune: bool = False) -> TrainingResult:
    prepared = engineer_features(frame)
    feature_names = [*features_config["numeric_features"], *features_config["categorical_features"]]
    x = prepared[feature_names]
    y = prepared[features_config["target"]]
    model_cfg = config["model"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=model_cfg["test_size"], random_state=model_cfg["random_state"]
    )
    cv = KFold(n_splits=min(model_cfg["cv_folds"], len(x_train)), shuffle=True, random_state=model_cfg["random_state"])
    preprocessor = build_preprocessor(features_config["numeric_features"], features_config["categorical_features"])
    # Cross-validation fits preprocessing separately in each fold to prevent leakage.
    from sklearn.pipeline import Pipeline

    params = {key: value for key, value in model_cfg.items() if key in {
        "max_depth", "learning_rate", "n_estimators", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda"
    }}
    if tune:
        params.update(tune_hyperparameters(x_train, y_train, config, features_config))
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", _model(params, model_cfg["random_state"]))])
    cv_mae = float(-cross_val_score(pipeline, x_train, y_train, cv=cv, scoring="neg_mean_absolute_error", n_jobs=1).mean())
    pipeline.fit(x_train, y_train)
    fitted_preprocessor = pipeline.named_steps["preprocessor"]
    fitted_model = pipeline.named_steps["model"]
    transformed_test = fitted_preprocessor.transform(x_test)
    metrics = evaluate_regression(y_test.to_numpy(), fitted_model.predict(transformed_test))
    return TrainingResult(fitted_model, fitted_preprocessor, metrics, cv_mae, transformed_test)
