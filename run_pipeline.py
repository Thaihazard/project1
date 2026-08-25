import os
import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryCleaner, build_preprocessor

# Load biến môi trường từ file .env
load_dotenv()

DATA_PATH = os.getenv("DATA_PATH", "archive/Salary_Data.csv")
MODEL_TYPE = os.getenv("MODEL_TYPE", "auto").lower()
RARE_THRESHOLD = int(os.getenv("RARE_THRESHOLD", 20))
TEST_SIZE = float(os.getenv("TEST_SIZE", 0.2))
RANDOM_STATE = int(os.getenv("RANDOM_STATE", 42))

def get_model_instance(name):
    """Factory function trả về mô hình tương ứng dựa trên cấu hình"""
    if name == "ridge":
        return Ridge(alpha=1.0)
    elif name == "random_forest":
        return RandomForestRegressor(n_estimators=150, max_depth=15, random_state=RANDOM_STATE, n_jobs=-1)
    elif name == "xgboost":
        return XGBRegressor(n_estimators=150, learning_rate=0.1, random_state=RANDOM_STATE, n_jobs=1)
    elif name == "fnn":
        return MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=RANDOM_STATE)
    else:
        return RandomForestRegressor(n_estimators=150, max_depth=15, random_state=RANDOM_STATE, n_jobs=-1)

def main():
    print(f"--- DYNAMIC ML PIPELINE ---")
    print(f"Loading data from: {DATA_PATH}")
    print(f"Target Model Mode: {MODEL_TYPE}")
    
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Please update DATA_PATH in .env")
        
    df = pd.read_csv(DATA_PATH)
    
    # 1. Tiền xử lý tự động
    cleaner = SalaryCleaner(rare_threshold=RARE_THRESHOLD)
    df_clean = cleaner.fit_transform(df)
    
    X = df_clean.drop(columns=['Salary'])
    y = df_clean['Salary']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    
    # 2. Xử lý chế độ 'auto' (Bake-off tự động chọn model tốt nhất)
    selected_model_name = MODEL_TYPE
    if MODEL_TYPE == "auto":
        print("\n[Auto Mode] Running benchmark across models to select the best performer...")
        models_to_test = {
            "ridge": Ridge(alpha=1.0),
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),
            "xgboost": XGBRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=1),
            "fnn": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=RANDOM_STATE)
        }
        
        best_score = float('inf')
        kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        
        for name, m in models_to_test.items():
            maes = []
            for tr_idx, va_idx in kf.split(X_train):
                X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
                y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
                
                pipe_temp = Pipeline([('preprocessor', build_preprocessor()), ('regressor', m)])
                pipe_temp.fit(X_tr, np.log1p(y_tr))
                preds = np.expm1(pipe_temp.predict(X_va))
                maes.append(mean_absolute_error(y_va, preds))
                
            mean_mae = np.mean(maes)
            print(f"  -> Model {name}: CV MAE = {mean_mae:.2f}")
            if mean_mae < best_score:
                best_score = mean_mae
                selected_model_name = name
                
        print(f"\n>>> [Auto Mode Selected Winner]: {selected_model_name.upper()} (Best CV MAE: {best_score:.2f})")

    # 3. Huấn luyện mô hình chính thức với cấu hình đã chọn
    final_regressor = get_model_instance(selected_model_name)
    final_pipeline = Pipeline([
        ('preprocessor', build_preprocessor()),
        ('regressor', final_regressor)
    ])
    
    print(f"\nTraining final model ({selected_model_name}) on full training set...")
    final_pipeline.fit(X_train, np.log1p(y_train))
    
    # 4. Đánh giá trên tập test độc lập
    preds_log = final_pipeline.predict(X_test)
    preds = np.expm1(preds_log)
    
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    
    print(f"\nTest Set Performance:")
    print(f"  - MAE:  {mae:.2f}")
    print(f"  - RMSE: {rmse:.2f}")
    print(f"  - R²:   {r2:.4f}")
    
    # 5. Đóng gói Artifact tự động
    os.makedirs("model_registry", exist_ok=True)
    model_path = "model_registry/best_salary_model.pkl"
    joblib.dump({
        "pipeline": final_pipeline,
        "cleaner": cleaner,
        "model_type": selected_model_name,
        "metrics": {"MAE": mae, "RMSE": rmse, "R2": r2}
    }, model_path)
    print(f"\nModel artifact successfully saved to {model_path}")

if __name__ == "__main__":
    main()
