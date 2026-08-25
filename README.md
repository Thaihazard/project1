# Salary Prediction Project

## Problem Statement (Giai đoạn 0)

- **Problem Type:** Regression (Predicting `Salary` continuous target variable).
- **Primary Metric:** MAE (Mean Absolute Error — easily interpretable: "average error in currency units"). Secondary metrics: RMSE and $R^2$.
- **Constraints & Requirements:** Explainability (SHAP required due to sensitive salary predictions); offline training with serialized artifact serving.
- **Success Criteria:** $R^2 > 0.7$ and $\text{MAE} < 15\%$ of average salary.

---

## 📂 Project Directory Structure

```text
ML_Project/
├── archive/
│   └── Salary_Data.csv         # Raw dataset
├── model_registry/
│   └── best_salary_model.pkl   # Serialized best pipeline & metadata artifact
├── tests/
│   └── test_pipeline.py        # Unit and integration test suite
├── .env                        # Environment variables configuration
├── preprocessing.py            # Data cleaning & ColumnTransformer pipeline builder
├── run_pipeline.py             # Dynamic config-driven training & packaging pipeline
├── predict_salary.py           # Inference script using serialized model artifact
├── data_audit.py               # EDA & schema audit script
├── benchmark_salary_models.py  # 5-model cross-validation bake-off script
├── train_final_model.py        # Final model training script
├── explainability.py           # SHAP analysis & fairness check script
└── requirements.txt            # Project dependencies
```

---

## 🛠️ Script Overview

- **`run_pipeline.py`**: Configures, trains, evaluates, and saves the machine learning pipeline (supports automatic model selection via `.env`).
- **`benchmark_salary_models.py`**: Performs cross-validation bake-off across multiple regressors.
- **`explainability.py`**: Generates SHAP values and feature importance plots to interpret model predictions.
- **`data_audit.py`**: Conducts exploratory data analysis (EDA) and checks schema constraints.
- **`predict_salary.py`**: Inference script for making predictions using the saved model artifact.

---

## 📥 Installation

1. Clone the repository and navigate to the project directory.
2. Create and activate a virtual environment:
   ```bash
   py -m venv venv
   # On Windows:
   .\.venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration (`.env`)

You can fully customize the pipeline behavior by editing the `.env` file in the root directory without modifying any source code:

- `DATA_PATH`: Path to your CSV dataset (default: `archive/Salary_Data.csv`)
- `MODEL_TYPE`: Training mode (`auto` to benchmark and pick the best performer, or specify `xgboost`, `random_forest`, `ridge`, `fnn`)
- `RARE_THRESHOLD`: Minimum frequency to keep a job title before grouping into `"Other"` (default: `20`)
- `TEST_SIZE`: Proportion of dataset reserved for the hold-out test set (default: `0.2`)
- `RANDOM_STATE`: Seed for reproducible random splitting (default: `42`)

---

## 🚀 Usage Guide

1. **Run Training Pipeline (Dynamic & Config-driven):**

   ```bash
   python run_pipeline.py
   ```

   _(This will read `.env`, clean data, optionally run the bake-off if `MODEL_TYPE=auto`, train the model, evaluate on the test set, and save the artifact to `model_registry/best_salary_model.pkl`)_

2. **Run Inference / Predict Salary for New Employees:**

   ```bash
   python predict_salary.py
   ```

3. **Run Automated Test Suite:**
   ```bash
   pytest tests/test_pipeline.py
   ```
