import os
import joblib
import pandas as pd
import numpy as np
import pytest

from preprocessing import SalaryCleaner, build_preprocessor

def test_preprocessing():
    df = pd.DataFrame({
        'Age': [30, 30, 40, None],
        'Gender': ['Male', 'Female', 'Male', 'Male'],
        'Education Level': ["Bachelor's Degree", "Master's", "phD", "Bachelor's"],
        'Job Title': ['Software Engineer', 'Data Analyst', 'RareJobTitle', 'Software Engineer'],
        'Years of Experience': [5, 3, 15, 5],
        'Salary': [90000, 65000, 150000, 90000]
    })
    
    cleaner = SalaryCleaner(rare_threshold=2)
    df_clean = cleaner.fit_transform(df)
    
    # Check deduplication & missing removal
    assert len(df_clean) == 3 # Row 0 and 3 are identical duplicates in Age, Gender, Education, Job Title, Experience, Salary. Wait, row 0 and 3 have same values except index. Let's check exact duplicate: row 0 and row 3 have identical columns.
    # Let's verify education normalization
    assert "Bachelor's" in df_clean['Education Level'].values
    assert "PhD" in df_clean['Education Level'].values

def test_model_inference():
    model_path = "model_registry/best_salary_model.pkl"
    assert os.path.exists(model_path), "Model artifact not found!"
    
    artifact = joblib.load(model_path)
    pipe = artifact["pipeline"]
    
    sample = pd.DataFrame({
        'Age': [32],
        'Gender': ['Male'],
        'Education Level': ["Bachelor's"],
        'Job Title': ['Software Engineer'],
        'Years of Experience': [5]
    })
    
    pred_log = pipe.predict(sample)
    pred_salary = np.expm1(pred_log[0])
    
    assert isinstance(pred_salary, float)
    assert pred_salary > 0
    print(f"Sample prediction test passed: ${pred_salary:,.2f}")

if __name__ == "__main__":
    pytest.main([__file__])
