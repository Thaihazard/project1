import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

class SalaryCleaner(BaseEstimator, TransformerMixin):
    def __init__(self, rare_threshold=20):
        self.rare_threshold = rare_threshold
        self.rare_job_titles_ = set()

    def fit(self, X, y=None):
        X_ = X.copy()
        # Standardize Education Level
        X_['Education Level'] = X_['Education Level'].str.strip().str.title()
        mapping = {
            "Bachelor'S": "Bachelor's",
            "Bachelor'S Degree": "Bachelor's",
            "Master'S": "Master's",
            "Master'S Degree": "Master's",
            "Phd": "PhD",
            "Ph.D.": "PhD"
        }
        X_['Education Level'] = X_['Education Level'].replace(mapping)
        
        # Identify rare job titles
        if 'Job Title' in X_.columns:
            vc = X_['Job Title'].value_counts()
            self.rare_job_titles_ = set(vc[vc < self.rare_threshold].index)
        return self

    def transform(self, X):
        X_ = X.copy()
        # Drop duplicates & missing
        X_ = X_.drop_duplicates()
        X_ = X_.dropna()
        
        # Standardize Education Level
        X_['Education Level'] = X_['Education Level'].str.strip().str.title()
        mapping = {
            "Bachelor'S": "Bachelor's",
            "Bachelor'S Degree": "Bachelor's",
            "Master'S": "Master's",
            "Master'S Degree": "Master's",
            "Phd": "PhD",
            "Ph.D.": "PhD"
        }
        X_['Education Level'] = X_['Education Level'].replace(mapping)
        
        # Group rare job titles
        if 'Job Title' in X_.columns:
            X_['Job Title'] = X_['Job Title'].apply(
                lambda x: 'Other' if x in self.rare_job_titles_ else x
            )
            
        return X_

def load_and_clean_data(filepath="archive/Salary_Data.csv"):
    df = pd.read_csv(filepath)
    cleaner = SalaryCleaner(rare_threshold=20)
    df_clean = cleaner.fit_transform(df)
    
    X = df_clean.drop(columns=['Salary'])
    y = df_clean['Salary']
    return X, y

def build_preprocessor(numeric_features=['Age', 'Years of Experience'], categorical_features=['Gender', 'Education Level', 'Job Title']):
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    return preprocessor

if __name__ == "__main__":
    X, y = load_and_clean_data()
    print(f"Cleaned X shape: {X.shape}, y shape: {y.shape}")
    print("Education levels:", X['Education Level'].unique())
    print("Sample job titles:", list(X['Job Title'].unique())[:5])
