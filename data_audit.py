import pandas as pd
import numpy as np
from pathlib import Path

def audit_data(filepath=None):
    project_root = Path(__file__).resolve().parent
    if filepath is None:
        filepath = project_root / "archive" / "Salary_Data.csv"
    else:
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = project_root / filepath

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

    df_clean = df.drop_duplicates().dropna(subset=['Salary'])
    print(f"\nRows after duplicate removal and dropping missing Salary: {df_clean.shape}")

    print("\n--- 6. CORRELATION WITH SALARY ---")
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    print(df_clean[numeric_cols].corr()['Salary'])

if __name__ == "__main__":
    audit_data()
