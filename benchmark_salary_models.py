import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import SalaryCleaner, build_preprocessor

def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def evaluate_models():
    df = pd.read_csv("archive/Salary_Data.csv")
    cleaner = SalaryCleaner(rare_threshold=20)
    df_clean = cleaner.fit_transform(df)
    
    X = df_clean.drop(columns=['Salary'])
    y = df_clean['Salary']
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    models = {
        "Ridge": Pipeline([
            ('preprocessor', build_preprocessor()),
            ('regressor', Ridge(alpha=1.0))
        ]),
        "RandomForest": Pipeline([
            ('preprocessor', build_preprocessor()),
            ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
        ]),
        "XGBoost": Pipeline([
            ('preprocessor', build_preprocessor()),
            ('regressor', XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42, n_jobs=1))
        ]),
        "CatBoost": "catboost_special",
        "FNN": Pipeline([
            ('preprocessor', build_preprocessor()),
            ('regressor', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42))
        ])
    }
    
    results = {name: {'MAE': [], 'RMSE': [], 'R2': [], 'MAPE': []} for name in models.keys()}
    
    for train_idx, val_idx in kf.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Log1p target transform
        y_train_log = np.log1p(y_train)
        y_val_log = np.log1p(y_val)
        
        for name, model in models.items():
            if name == "CatBoost":
                # CatBoost native categorical handling
                cb_cleaner = SalaryCleaner(rare_threshold=20)
                # We can use fit_transform on cleaner
                X_tr_cb = cb_cleaner.fit_transform(pd.concat([X_train, y_train], axis=1)).drop(columns=['Salary'])
                y_tr_cb = pd.concat([X_train, y_train], axis=1).drop_duplicates().dropna()['Salary']
                
                X_va_cb = cb_cleaner.transform(pd.concat([X_val, y_val], axis=1)).drop(columns=['Salary'])
                y_va_cb = pd.concat([X_val, y_val], axis=1).drop_duplicates().dropna()['Salary']
                
                cat_features = ['Gender', 'Education Level', 'Job Title']
                for c in cat_features:
                    X_tr_cb[c] = X_tr_cb[c].astype(str)
                    X_va_cb[c] = X_va_cb[c].astype(str)
                    
                reg = CatBoostRegressor(iterations=200, learning_rate=0.1, verbose=0, random_seed=42, cat_features=cat_features)
                reg.fit(X_tr_cb, np.log1p(y_tr_cb))
                preds_log = reg.predict(X_va_cb)
                preds = np.expm1(preds_log)
                actuals = y_va_cb.values
            else:
                # Standard pipeline with TransformedTargetRegressor or manual log1p
                model.fit(X_train, y_train_log)
                preds_log = model.predict(X_val)
                preds = np.expm1(preds_log)
                actuals = y_val.values
                
            mae = mean_absolute_error(actuals, preds)
            rmse = np.sqrt(mean_squared_error(actuals, preds))
            r2 = r2_score(actuals, preds)
            mape = mean_absolute_percentage_error(actuals, preds)
            
            results[name]['MAE'].append(mae)
            results[name]['RMSE'].append(rmse)
            results[name]['R2'].append(r2)
            results[name]['MAPE'].append(mape)
            
    print("\n================ MODEL BAKE-OFF RESULTS (5-Fold CV) ================")
    summary = []
    for name, metrics in results.items():
        summary.append({
            "Model": name,
            "MAE": f"{np.mean(metrics['MAE']):.2f} ± {np.std(metrics['MAE']):.2f}",
            "RMSE": f"{np.mean(metrics['RMSE']):.2f} ± {np.std(metrics['RMSE']):.2f}",
            "R2": f"{np.mean(metrics['R2']):.3f} ± {np.std(metrics['R2']):.3f}",
            "MAPE (%)": f"{np.mean(metrics['MAPE']):.2f}% ± {np.std(metrics['MAPE']):.2f}%"
        })
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))
    return summary_df

if __name__ == "__main__":
    evaluate_models()
