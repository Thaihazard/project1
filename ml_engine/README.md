# AI CompHub ML Engine

This folder contains the reproducible salary-model training pipeline and versioned artifacts. No model or training data is checked in. Until a model passes evaluation and is installed, the backend uses its clearly labeled demo baseline.

## Layout

- `artifacts/`: trained XGBoost model, SHAP TreeExplainer, fitted preprocessing pipeline, and quality report.
- `config/`: model hyperparameters, quality gates, and input/engineered feature definitions.
- `data/raw/`: place approved, de-identified source extracts here; this folder is git-ignored.
- `data/processed/`: optional held-out test data and processed extracts; this folder is git-ignored.
- `src/`: PostgreSQL/CSV loader, preprocessing, feature engineering, training, evaluation, and explanation code.
- `tests/`: model quality gate checks.
- `train_pipeline.py`: training entrypoint.

## Train from a CSV extract

CSV files must include `current_salary`, `kpi_score`, `soft_skill_score`, `years_experience`, `certification_count`, and `target_salary`. Use an approved, de-identified extract; do not include employee names or IDs.

```powershell
python -m pip install -r ml_engine/requirements.txt
python -m ml_engine.train_pipeline --data ml_engine/data/raw/payroll_training.csv --enforce-quality
```

To tune parameters with Optuna, add `--tune`. Artifacts are written only after data validation; `--enforce-quality` prevents replacing artifacts when configured MAE/R2 gates fail.

## Train from PostgreSQL

```powershell
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/comphub"
python -m ml_engine.train_pipeline --enforce-quality
```

The loader reads only approved/paid payroll outcomes and does not select employee names or IDs. The current employee schema has no verified years-of-experience or certification fields, so DB extracts use configured zero defaults for those inputs. Add verified source fields before relying on those features for production decisions.

After reviewing the quality report, restart the API to load artifacts. The backend reads `xgboost_salary_v1.pkl`, `scaler_pipeline_v1.pkl`, and `shap_explainer_v1.pkl` from this folder's `artifacts/` directory. Never commit artifacts or payroll data to source control.

To run the quality checks, place a held-out CSV in `data/processed/test.csv` with the same columns as the training extract, then run `python -m pytest ml_engine/tests` from the repository root. Without a real held-out dataset and trained artifacts, the artifact quality test is skipped; the deterministic quality-gate unit check still runs.
