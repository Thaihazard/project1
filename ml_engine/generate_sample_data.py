"""Generate realistic payroll dataset for training AI CompHub salary prediction model."""
from pathlib import Path
import numpy as np
import pandas as pd

def generate_payroll_data(n_samples: int = 600, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)

    # Base features
    years_experience = np.clip(np.random.exponential(scale=4.5, size=n_samples), 0.5, 25.0)
    
    # Current salary is correlated with experience
    base_salary_mean = 12_000_000 + years_experience * 2_500_000
    noise_salary = np.random.normal(0, 2_000_000, size=n_samples)
    current_salary = np.clip(np.round((base_salary_mean + noise_salary) / 500_000) * 500_000, 8_000_000, 95_000_000)

    # Performance & skills
    kpi_score = np.clip(np.random.normal(loc=85, scale=12, size=n_samples), 50.0, 130.0)
    soft_skill_score = np.clip(np.random.normal(loc=3.8, scale=0.6, size=n_samples), 1.0, 5.0)
    certification_count = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=[0.4, 0.3, 0.18, 0.09, 0.03])

    # Target salary calculation with realistic market adjustments:
    # KPI adjustment: +/- 0.3% per point above/below 80
    # Soft skills: +/- 3% per point above/below 3.5
    # Experience adjustment: +1.5% per year
    # Certifications: +2.5% per cert
    kpi_factor = (kpi_score - 80) * 0.0035
    skill_factor = (soft_skill_score - 3.5) * 0.03
    cert_factor = certification_count * 0.025
    growth_rate = 0.05 + kpi_factor + skill_factor + cert_factor
    growth_rate = np.clip(growth_rate, -0.05, 0.35)

    noise_target = np.random.normal(0, 500_000, size=n_samples)
    target_salary = np.round((current_salary * (1 + growth_rate) + noise_target) / 100_000) * 100_000
    target_salary = np.clip(target_salary, 9_000_000, 120_000_000)

    df = pd.DataFrame({
        "current_salary": current_salary.astype(int),
        "kpi_score": np.round(kpi_score, 1),
        "soft_skill_score": np.round(soft_skill_score, 1),
        "years_experience": np.round(years_experience, 1),
        "certification_count": certification_count.astype(int),
        "target_salary": target_salary.astype(int),
    })

    return df

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    output_dir = root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "payroll_training.csv"

    data = generate_payroll_data(n_samples=600)
    data.to_csv(csv_path, index=False)
    print(f"Generated {len(data)} payroll records -> {csv_path}")
    print(data.head())
