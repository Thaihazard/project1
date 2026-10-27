import joblib
import hashlib
import sys
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class SalaryExplainer:
    """Giải thích mô hình lương bằng SHAP và phân tích sai số theo nhóm."""

    def __init__(self, model_path: str = None, data_path: str = None) -> None:
        """Khởi tạo bộ giải thích mô hình lương.

        Args:
            model_path: Đường dẫn đến artifact mô hình (.pkl).
            data_path: Đường dẫn đến file dữ liệu CSV.
        """
        project_root = Path(__file__).resolve().parent
        self.output_dir = project_root / "output"

        if model_path is None:
            model_path = project_root / "model_registry" / "best_salary_model.pkl"
        else:
            model_path = Path(model_path)
            if not model_path.is_absolute():
                model_path = project_root / model_path
        self.model_path = model_path

        if data_path is None:
            data_path = project_root / "archive" / "Salary_Data.csv"
        else:
            data_path = Path(data_path)
            if not data_path.is_absolute():
                data_path = project_root / data_path
        self.data_path = data_path

        self.artifact = joblib.load(self.model_path)
        self.pipeline = self.artifact["pipeline"]
        self.evaluation_pipeline = self.artifact.get("evaluation_pipeline", self.pipeline)

    def compute_fairness(self) -> pd.DataFrame:
        """Tính residual (sai lệch) và sai số tuyệt đối trên tập holdout.

        Returns:
            DataFrame có thêm các cột dự đoán, residual và sai số tuyệt đối.
        """
        df_clean = self._load_holdout()

        X = df_clean.drop(columns=['Salary'])
        y = df_clean['Salary']

        preds = self.evaluation_pipeline.predict(X)
        residuals = y - preds

        df_clean['Prediction'] = preds
        df_clean['Residual'] = residuals
        df_clean['AbsError'] = np.abs(residuals)
        return df_clean

    def _load_holdout(self) -> pd.DataFrame:
        """Tải đúng các dòng holdout được ghi lại khi huấn luyện artifact."""
        indices = self.artifact.get("evaluation_indices")
        if not indices:
            raise ValueError(
                "Artifact này không có metadata về các dòng holdout. Hãy huấn luyện lại "
                "bằng run_pipeline.py trước khi chạy phân tích."
            )

        expected_hash = self.artifact.get("evaluation_data_sha256")
        actual_hash = hashlib.sha256(self.data_path.read_bytes()).hexdigest()
        if expected_hash and actual_hash != expected_hash:
            raise ValueError(
                "File dữ liệu hiện tại khác với file dùng để tạo artifact này. "
                "Hãy cung cấp đúng file dữ liệu ban đầu hoặc huấn luyện lại mô hình."
            )

        df = pd.read_csv(self.data_path).drop_duplicates().dropna(subset=['Salary'])
        missing_indices = set(indices).difference(df.index)
        if missing_indices:
            raise ValueError(
                "Dữ liệu hiện tại không còn khớp với các dòng holdout đã ghi trong artifact. "
                "Hãy dùng lại dữ liệu ban đầu hoặc huấn luyện lại mô hình."
            )
        return df.loc[indices].copy()


    def compute_shap_values(self) -> Tuple[np.ndarray, np.ndarray]:
        """Tính SHAP trên holdout, theo thang logarit tiền lương của mô hình.

        Returns:
            Cặp (shap_values, ma trận đặc trưng sau biến đổi).
        """
        df = self._load_holdout()
        X = df.drop(columns=['Salary'])
        schema = self.evaluation_pipeline.named_steps.get('schema')
        if schema is not None:
            X = schema.transform(X)
        cleaner = self.evaluation_pipeline.named_steps['cleaner']
        X = cleaner.transform(X)

        # Lấy preprocessor và regressor bên trong TransformedTargetRegressor.
        transformed_model = self.evaluation_pipeline.named_steps['model']
        inner_pipeline = transformed_model.regressor_
        preprocessor = inner_pipeline.named_steps['preprocessor']
        regressor = inner_pipeline.named_steps['regressor']

        X_transformed = preprocessor.transform(X)
        if hasattr(X_transformed, "toarray"):
            X_transformed = X_transformed.toarray()
        feature_names = preprocessor.get_feature_names_out()

        print("Đang tính SHAP trên tập holdout (đầu ra mô hình: log1p(Salary))...")
        class_name = regressor.__class__.__name__
        if "Forest" in class_name or "Tree" in class_name or "XGB" in class_name or "Cat" in class_name:
            explainer = shap.TreeExplainer(regressor)
            shap_values = explainer.shap_values(X_transformed)
        elif "Linear" in class_name or "Ridge" in class_name:
            explainer = shap.LinearExplainer(regressor, X_transformed)
            shap_values = explainer.shap_values(X_transformed)
        else:
            # Dùng KernelExplainer với dữ liệu nền (background) được lấy mẫu để giảm thời gian tính.
            bg_data = shap.sample(X_transformed, min(50, X_transformed.shape[0]))
            explainer = shap.KernelExplainer(regressor.predict, bg_data)
            # Chỉ giải thích tối đa 50 mẫu để giảm thời gian tính.
            X_eval = X_transformed[:50]
            shap_values = explainer.shap_values(X_eval)
            return shap_values, feature_names

        return shap_values, feature_names

    @staticmethod
    def summarize_shap_by_input(shap_values: np.ndarray, feature_names) -> pd.DataFrame:
        """Aggregate encoded-column SHAP values back to the original input fields."""
        values = np.asarray(shap_values)
        if values.ndim == 3:
            values = values[:, :, 0]
        rows = []
        for field in [
            "Age", "Gender", "Education Level", "Job Title", "Years of Experience",
            "Education_Ordinal", "Career_Start_Age", "Seniority_Level", "Job_Family",
            "sim_avg_hours_per_week", "sim_projects_completed", "sim_years_at_company",
            "sim_num_job_changes", "sim_employment_type", "sim_work_mode",
            "sim_absence_days_per_month", "sim_location_cost_level", "sim_company_size", "sim_industry",
        ]:
            if field in ("Age", "Years of Experience", "Education_Ordinal", "Career_Start_Age",
                         "Seniority_Level", "sim_avg_hours_per_week", "sim_projects_completed",
                         "sim_years_at_company", "sim_num_job_changes", "sim_absence_days_per_month",
                         "sim_location_cost_level"):
                matches = [i for i, name in enumerate(feature_names) if name == f"num__{field}"]
            else:
                matches = [i for i, name in enumerate(feature_names) if name.startswith(f"cat__{field}_")]
            if matches:
                grouped = values[:, matches].sum(axis=1)
                rows.append({
                    "Trường": field,
                    "Mean_abs_SHAP_log_salary": float(np.mean(np.abs(grouped))),
                    "Mean_SHAP_log_salary": float(np.mean(grouped)),
                })
        return pd.DataFrame(rows).sort_values("Mean_abs_SHAP_log_salary", ascending=False)

    def plot_predicted_vs_actual(self, holdout: pd.DataFrame) -> Path:
        """Save a holdout scatter plot with the ideal y=x line and regression metrics."""
        actual = holdout["Salary"].to_numpy(dtype=float)
        predicted = holdout["Prediction"].to_numpy(dtype=float)
        mae = mean_absolute_error(actual, predicted)
        rmse = mean_squared_error(actual, predicted) ** 0.5
        r2 = r2_score(actual, predicted)

        low = float(min(actual.min(), predicted.min()))
        high = float(max(actual.max(), predicted.max()))
        padding = max((high - low) * 0.04, 1.0)
        low -= padding
        high += padding

        fig, ax = plt.subplots(figsize=(8, 7))
        ax.scatter(actual, predicted, alpha=0.65, s=28, color="#2878B5", edgecolors="none")
        ax.plot([low, high], [low, high], linestyle="--", linewidth=1.5, color="#D9534F", label="Dự đoán hoàn hảo")
        ax.set_xlim(low, high)
        ax.set_ylim(low, high)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Lương thực tế")
        ax.set_ylabel("Lương dự đoán")
        ax.set_title("Dự đoán so với thực tế trên tập holdout")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="lower right")
        ax.text(
            0.04,
            0.96,
            f"MAE: {mae:,.0f}\nRMSE: {rmse:,.0f}\nR²: {r2:.3f}\nSố dòng: {len(actual)}",
            transform=ax.transAxes,
            va="top",
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.9},
        )
        fig.tight_layout()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "predicted_vs_actual.png"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_feature_importance(self, summary: pd.DataFrame) -> Path:
        """Save grouped mean absolute SHAP importance for the original input fields."""
        labels = {
            "Age": "Tuổi",
            "Gender": "Giới tính",
            "Education Level": "Trình độ học vấn",
            "Job Title": "Chức danh",
            "Years of Experience": "Số năm kinh nghiệm",
            "Education_Ordinal": "Bậc học (mã hóa)",
            "Career_Start_Age": "Tuổi bắt đầu đi làm",
            "Seniority_Level": "Cấp bậc",
            "Job_Family": "Nhóm nghề",
            "sim_avg_hours_per_week": "Giờ làm việc mỗi tuần",
            "sim_projects_completed": "Số dự án hoàn thành",
            "sim_years_at_company": "Số năm tại công ty",
            "sim_num_job_changes": "Số lần đổi việc",
            "sim_employment_type": "Hình thức tuyển dụng",
            "sim_work_mode": "Hình thức làm việc",
            "sim_absence_days_per_month": "Số ngày vắng mặt mỗi tháng",
            "sim_location_cost_level": "Mức chi phí địa phương",
            "sim_company_size": "Quy mô công ty",
            "sim_industry": "Ngành nghề",
        }
        ordered = summary.sort_values("Mean_abs_SHAP_log_salary", ascending=True).copy()
        ordered["Tên trường"] = ordered["Trường"].map(labels).fillna(ordered["Trường"])
        height = max(7, 0.38 * len(ordered))
        fig, ax = plt.subplots(figsize=(10, height))
        ax.barh(
            ordered["Tên trường"],
            ordered["Mean_abs_SHAP_log_salary"],
            color="#4472C4",
        )
        ax.set_xlabel("Mean |SHAP| trên thang log1p(lương)")
        ax.set_ylabel("Biến đầu vào")
        ax.set_title("Tầm quan trọng của các biến đầu vào (SHAP)")
        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)
        fig.text(
            0.01,
            0.01,
            "SHAP được gom từ các cột đã mã hóa về 19 trường gốc; giá trị không phải số tiền cộng trực tiếp vào lương.",
            fontsize=9,
        )
        fig.tight_layout(rect=(0, 0.035, 1, 1))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "feature_importance_shap.png"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        return path

    def run_all(self) -> None:
        """Chạy và in kết quả SHAP cùng phân tích sai số theo nhóm."""
        print("--- GIAI ĐOẠN 5: GIẢI THÍCH MÔ HÌNH VÀ PHÂN TÍCH SAI SỐ ---")

        shap_values, feature_names = self.compute_shap_values()
        print(f"Kích thước mảng SHAP: {np.shape(shap_values)}")
        print("\n--- ĐÓNG GÓP SHAP THEO 19 TRƯỜNG ĐẦU VÀO (thang log1p lương) ---")
        shap_summary = self.summarize_shap_by_input(shap_values, feature_names)
        print(shap_summary.to_string(index=False))

        df_clean = self.compute_fairness()
        predicted_actual_path = self.plot_predicted_vs_actual(df_clean)
        importance_path = self.plot_feature_importance(shap_summary)
        print(f"\nĐã lưu biểu đồ Predicted vs Actual: {predicted_actual_path}")
        print(f"Đã lưu biểu đồ SHAP Feature Importance: {importance_path}")

        print("\n--- SAI SỐ TRÊN HOLDOUT THEO GIỚI TÍNH (thống kê mô tả, không phải chứng nhận công bằng) ---")
        print(df_clean.assign(Gender=df_clean['Gender'].fillna('Thiếu thông tin')).groupby('Gender').agg(
            **{
                'Số mẫu': ('AbsError', 'size'),
                'MAE': ('AbsError', 'mean'),
                'Residual trung bình': ('Residual', 'mean'),
            }
        ))

        print("\n--- SAI SỐ TRÊN HOLDOUT THEO TRÌNH ĐỘ HỌC VẤN (thống kê mô tả, không phải chứng nhận công bằng) ---")
        print(df_clean.assign(**{'Education Level': df_clean['Education Level'].fillna('Thiếu thông tin')}).groupby('Education Level').agg(
            **{
                'Số mẫu': ('AbsError', 'size'),
                'MAE': ('AbsError', 'mean'),
                'Residual trung bình': ('Residual', 'mean'),
            }
        ))

if __name__ == "__main__":
    explainer = SalaryExplainer()
    explainer.run_all()
