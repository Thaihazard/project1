import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryCleaner, SalaryPipelineFactory

class SalaryModelTrainer:
    def __init__(self, data_path="archive/Salary_Data.csv", model_output_path="model_registry/best_salary_model.pkl"):
        self.data_path = data_path
        self.model_output_path = model_output_path

    def train(self):
        df = pd.read_csv(self.data_path)
        
        # Clean raw dataset (drop duplicates and missing values) before split
        df_clean = df.drop_duplicates().dropna()
        
        train_df, test_df = train_test_split(df_clean, test_size=0.2, random_state=42)
        
        X_train = train_df.drop(columns=['Salary'])
        y_train = train_df['Salary']
        
        X_test = test_df.drop(columns=['Salary'])
        y_test = test_df['Salary']
        
        regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        pipeline = SalaryPipelineFactory.create_pipeline(regressor=regressor, rare_threshold=20)
        pipeline.fit(X_train, y_train)
        
        preds = pipeline.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        os.makedirs(os.path.dirname(self.model_output_path), exist_ok=True)
        joblib.dump({
            "pipeline": pipeline,
            "metrics": {"MAE": mae, "RMSE": rmse, "R2": r2},
            "features": list(X_train.columns)
        }, self.model_output_path)
        
        return {"MAE": mae, "RMSE": rmse, "R2": r2}

if __name__ == "__main__":
    trainer = SalaryModelTrainer()
    metrics = trainer.train()
    print(f"Trained & Saved. Metrics: {metrics}")
