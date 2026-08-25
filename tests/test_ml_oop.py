import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from preprocessing import SalaryCleaner, SalaryPipelineFactory
from train_final_model import SalaryModelTrainer
from predict_salary import SalaryPredictor

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

def test_salary_model_trainer(tmp_path):
    model_path = tmp_path / "best_salary_model.pkl"
    trainer = SalaryModelTrainer(data_path="archive/Salary_Data.csv", model_output_path=str(model_path))
    metrics = trainer.train()
    assert os.path.exists(model_path)
    assert 'MAE' in metrics
    assert 'R2' in metrics

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

