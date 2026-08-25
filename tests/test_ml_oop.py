import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
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

def test_salary_pipeline_factory():
    factory = SalaryPipelineFactory()
    pipeline = factory.create_pipeline(LinearRegression(), rare_threshold=2)
    assert pipeline is not None
