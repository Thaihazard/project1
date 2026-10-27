import pandas as pd
import numpy as np
import os
import joblib
import pytest
from sklearn.linear_model import LinearRegression
from preprocessing import SalaryCleaner, SalaryPipelineFactory
from preprocessing import MODEL_FEATURES
from run_pipeline import SalaryModelTrainer
from predict_salary import SalaryPredictor

def test_salary_cleaner():
    df = pd.DataFrame({
        'Age': [25, 30],
        'Gender': ['Male', 'Female'],
        'Education Level': ["bachelor's", "Master's"],
        'Job Title': ['Software Engineer', 'Data Scientist'],
        'Salary': [50000, 80000]
    })
    cleaner = SalaryCleaner(rare_threshold=2)
    cleaned = cleaner.fit_transform(df)
    assert len(cleaned) == 2
    assert cleaned.iloc[0]['Education Level'] == "Bachelor's"
    assert cleaned.iloc[1]['Job Title'] == 'Other' # Data Scientist occurs < 2 times

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
    artifact = joblib.load(model_path)
    assert artifact["training_rows"] > artifact["evaluation_training_rows"]
    assert artifact["evaluation_pipeline"] is not artifact["pipeline"]

def test_salary_predictor(tmp_path):
    model_path = tmp_path / "best_salary_model.pkl"
    trainer = SalaryModelTrainer(model_output_path=model_path)
    trainer.train()
    predictor = SalaryPredictor(model_path=str(model_path))
    sample = {
        'Age': 28,
        'Gender': 'Female',
        'Education Level': "Bachelor's",
        'Job Title': 'Software Engineer',
        'Years of Experience': 3.0,
        'Education_Ordinal': 1,
        'Career_Start_Age': 25,
        'Seniority_Level': 2,
        'Job_Family': 'Engineering',
        'sim_avg_hours_per_week': 40,
        'sim_projects_completed': 3,
        'sim_years_at_company': 1.5,
        'sim_num_job_changes': 1,
        'sim_employment_type': 'Full-time',
        'sim_work_mode': 'Hybrid',
        'sim_absence_days_per_month': 0.5,
        'sim_location_cost_level': 2,
        'sim_company_size': '51-500',
        'sim_industry': 'Technology',
    }
    assert set(MODEL_FEATURES).issubset(sample)
    pred = predictor.predict_single(sample)
    assert isinstance(pred, float)
    assert pred > 0

    inconsistent = sample.copy()
    inconsistent["Career_Start_Age"] += 1
    with pytest.raises(ValueError, match="Career_Start_Age"):
        predictor.predict_single(inconsistent)

    invalid_range = sample.copy()
    invalid_range["sim_avg_hours_per_week"] = 200
    with pytest.raises(ValueError, match="sim_avg_hours_per_week"):
        predictor.predict_single(invalid_range)

    inconsistent_family = sample.copy()
    inconsistent_family["Job_Family"] = "Data"
    with pytest.raises(ValueError, match="Job_Family"):
        predictor.predict_single(inconsistent_family)

    unseen_category = sample.copy()
    unseen_category["sim_industry"] = "New Industry"
    with pytest.raises(ValueError, match="sim_industry"):
        predictor.predict_single(unseen_category)

def test_model_benchmarker():
    from benchmark_salary_models import ModelBenchmarker
    benchmarker = ModelBenchmarker(data_path="archive/Salary_Data.csv", n_splits=2)
    summary_df = benchmarker.evaluate()
    assert isinstance(summary_df, pd.DataFrame)
    assert 'Model' in summary_df.columns
    assert 'MAE' in summary_df.columns

