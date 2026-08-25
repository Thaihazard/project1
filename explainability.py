import joblib
import pandas as pd
import numpy as np
import shap

def run_explainability_and_fairness():
    print("--- GIAI DOAN 5: EXPLAINABILITY & FAIRNESS ---")
    data = joblib.load("model_registry/best_salary_model.pkl")
    pipe = data["pipeline"]
    cleaner = data["cleaner"]
    
    df = pd.read_csv("archive/Salary_Data.csv")
    df_clean = cleaner.transform(df)
    X = df_clean.drop(columns=['Salary'])
    y = df_clean['Salary']
    
    # Preprocessor transform
    preprocessor = pipe.named_steps['preprocessor']
    regressor = pipe.named_steps['regressor']
    
    X_transformed = preprocessor.transform(X)
    
    # SHAP TreeExplainer
    print("\nComputing SHAP values...")
    explainer = shap.TreeExplainer(regressor)
    shap_values = explainer.shap_values(X_transformed)
    
    print(f"SHAP values shape: {np.shape(shap_values)}")
    
    # Fairness / Residual analysis
    preds_log = pipe.predict(X)
    preds = np.expm1(preds_log)
    residuals = y - preds
    
    df_clean['Prediction'] = preds
    df_clean['Residual'] = residuals
    df_clean['AbsError'] = np.abs(residuals)
    
    print("\n--- FAIRNESS CHECK: Mean Absolute Error by Gender ---")
    print(df_clean.groupby('Gender')['AbsError'].mean())
    
    print("\n--- FAIRNESS CHECK: Mean Absolute Error by Education Level ---")
    print(df_clean.groupby('Education Level')['AbsError'].mean())

if __name__ == "__main__":
    run_explainability_and_fairness()
