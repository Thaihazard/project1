import os
import joblib
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from preprocessing import SalaryCleaner, build_preprocessor
from run_pipeline import SalaryModelTrainer

def test_preprocessing():
    df = pd.DataFrame({
        'Age': [30, 30, 40, None],
        'Gender': ['Male', 'Female', 'Male', 'Male'],
        'Education Level': ["Bachelor's Degree", "Master's", "phD", "Bachelor's"],
        'Job Title': ['Software Engineer', 'Data Analyst', 'RareJobTitle', 'Software Engineer'],
        'Years of Experience': [5, 3, 15, 5],
        'Salary': [90000, 65000, 150000, 90000]
    })

    df = df.drop_duplicates().dropna()
    cleaner = SalaryCleaner(rare_threshold=2)
    df_clean = cleaner.fit_transform(df)

    # Check deduplication & missing removal
    assert len(df_clean) == 3
    # Let's verify education normalization
    assert "Bachelor's" in df_clean['Education Level'].values
    assert "PhD" in df_clean['Education Level'].values

def test_model_inference():
    project_root = Path(__file__).resolve().parent.parent
    model_path = project_root / "model_registry" / "best_salary_model.pkl"

    # Train if doesn't exist
    if not model_path.exists():
        trainer = SalaryModelTrainer()
        trainer.train()

    assert model_path.exists(), "Model artifact not found!"

    artifact = joblib.load(model_path)
    pipe = artifact["pipeline"]

    sample = pd.DataFrame({
        'Age': [32],
        'Gender': ['Male'],
        'Education Level': ["Bachelor's"],
        'Job Title': ['Software Engineer'],
        'Years of Experience': [5]
    })

    pred_salary = pipe.predict(sample)[0]

    assert isinstance(pred_salary, (float, np.floating))
    assert pred_salary > 0
    print(f"Sample prediction test passed: ${pred_salary:,.2f}")

if __name__ == "__main__":
    pytest.main([__file__])
