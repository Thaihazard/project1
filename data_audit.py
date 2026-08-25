import pandas as pd
import numpy as np

def audit_data(filepath="archive/Salary_Data.csv"):
    df = pd.read_csv(filepath)
    print("--- 1. SCHEMA & BASIC INFO ---")
    print(df.info())
    print("\n--- 2. MISSING VALUES ---")
    print(df.isnull().sum())
    print("\n--- 3. DUPLICATE ROWS ---")
    print(f"Duplicates before cleaning: {df.duplicated().sum()}")
    
    print("\n--- 4. TARGET DISTRIBUTION (Salary) ---")
    print(df['Salary'].describe())
    
    print("\n--- 5. CATEGORICAL VALUE COUNTS ---")
    for col in ['Gender', 'Education Level']:
        if col in df.columns:
            print(f"\n{col}:\n{df[col].value_counts(dropna=False)}")
            
    print(f"\nUnique Job Titles: {df['Job Title'].nunique() if 'Job Title' in df.columns else 'N/A'}")
    
    # Clean duplicates for signal check
    df_clean = df.drop_duplicates().dropna()
    print(f"\nCleaned dataset shape: {df_clean.shape}")
    
    # Correlation for numeric features
    print("\n--- 6. CORRELATION WITH SALARY ---")
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    print(df_clean[numeric_cols].corr()['Salary'])

if __name__ == "__main__":
    audit_data()
