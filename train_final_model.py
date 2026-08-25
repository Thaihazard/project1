import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryCleaner, build_preprocessor

def train_and_save_final_model():
    print("--- GIAI DOAN 4: TRAIN FINAL MODEL & GIAI DOAN 6: PACKAGING ---")
    df = pd.read_csv("archive/Salary_Data.csv")
    
    # Split train/test (80/20 hold-out)
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    cleaner = SalaryCleaner(rare_threshold=20)
    train_clean = cleaner.fit_transform(train_df)
    test_clean = cleaner.transform(test_df)
    
    X_train = train_clean.drop(columns=['Salary'])
    y_train = train_clean['Salary']
    
    X_test = test_clean.drop(columns=['Salary'])
    y_test = test_clean['Salary']
    
    # Build pipeline with tuned RandomForest (best from bake-off)
    final_pipeline = Pipeline([
        ('cleaner', cleaner),
        ('preprocessor', build_preprocessor()),
        ('regressor', RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    # Train on original target with log1p transformation inside or manual
    # For simplicity in pipeline, we train on log1p(y)
    y_train_log = np.log1p(y_train)
    
    # Note: Pipeline includes cleaner, but cleaner is fitted. Let's build a clean pipeline
    # Actually, cleaner is part of pipeline if we wrap correctly, or we clean X_train directly and pipeline has preprocessor + regressor.
    
    pipe = Pipeline([
        ('preprocessor', build_preprocessor()),
        ('regressor', RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    pipe.fit(X_train, y_train_log)
    
    # Evaluate on test set
    preds_log = pipe.predict(X_test)
    preds = np.expm1(preds_log)
    
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    
    print(f"Test Set Evaluation Metrics:")
    print(f"  - MAE:  {mae:.2f}")
    print(f"  - RMSE: {rmse:.2f}")
    print(f"  - R²:   {r2:.4f}")
    
    # Save model artifact and metadata
    os.makedirs("model_registry", exist_ok=True)
    model_path = "model_registry/best_salary_model.pkl"
    joblib.dump({
        "pipeline": pipe,
        "cleaner": cleaner,
        "metrics": {"MAE": mae, "RMSE": rmse, "R2": r2},
        "features": list(X_train.columns)
    }, model_path)
    print(f"\nModel saved successfully to {model_path}")

if __name__ == "__main__":
    train_and_save_final_model()
