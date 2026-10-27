# Dự án dự đoán lương

## Bài toán

- **Loại bài toán:** Hồi quy, dự đoán giá trị liên tục trong cột `Salary`.
- **Chỉ số chính:** MAE (sai số tuyệt đối trung bình, tính theo đơn vị tiền lương). Chỉ số bổ sung: RMSE và $R^2$.
- **Yêu cầu:** Có thể giải thích dự đoán bằng SHAP vì dữ liệu lương nhạy cảm; hỗ trợ huấn luyện ngoại tuyến và nạp lại mô hình đã lưu để dự đoán.
- **Tiêu chí mục tiêu:** $R^2 > 0.7$ và $\text{MAE} < 15\%$ mức lương trung bình.

---

## 📂 Cấu trúc dự án

```text
ML_Project/
├── archive/                    # Thư mục dữ liệu đầu vào lưu trên máy, không đưa lên Git
├── model_registry/             # Thư mục chứa model artifact được tạo khi huấn luyện
├── tests/
│   ├── test_pipeline.py        # Kiểm thử pipeline và dự đoán
│   └── test_ml_oop.py          # Kiểm thử các thành phần và bước huấn luyện
├── .env.example                # Tệp mẫu cấu hình an toàn để chia sẻ
├── preprocessing.py            # Làm sạch dữ liệu và tạo pipeline ColumnTransformer
├── run_pipeline.py             # Điều phối chọn mô hình, huấn luyện, đánh giá và lưu artifact
├── predict_salary.py           # Nạp model artifact và dự đoán
├── data_audit.py               # Phân tích khám phá dữ liệu và kiểm tra schema
├── benchmark_salary_models.py  # Cross-validation và so sánh mô hình
├── explainability.py           # Phân tích SHAP và sai số theo nhóm
└── requirements.txt            # Danh sách thư viện cần cài
```

---

## 🛠️ Vai trò các script

- **`run_pipeline.py`**: Chọn mô hình, huấn luyện mô hình cuối, đánh giá trên holdout và lưu artifact `.pkl`. Có chế độ tự động cấu hình qua `.env`.
- **`benchmark_salary_models.py`**: Cung cấp điểm cross-validation cho bước chọn mô hình; cũng có thể chạy riêng để in bảng so sánh.
- **`explainability.py`**: Tính giá trị SHAP và phân tích sai số trên holdout theo từng nhóm.
- **`data_audit.py`**: Phân tích khám phá dữ liệu (EDA) và kiểm tra schema.
- **`predict_salary.py`**: Nạp model artifact đã lưu để dự đoán lương.

## Đưa dự án lên GitHub

Nên đưa lên Git các file mã nguồn Python, test, `requirements.txt`, README này, báo cáo trong `docs/`, `.gitignore` và `.env.example`. Không đưa môi trường ảo, `.env`, model artifact được tạo ra, cache hoặc log CatBoost lên Git.

Dữ liệu CSV về lương mặc định chỉ lưu trên máy vì cần xác nhận giấy phép và quyền riêng tư trước khi chia sẻ. Đặt bản dữ liệu được phép sử dụng tại `archive/Salary_Data.csv` hoặc cấu hình `DATA_PATH` trong `.env`. File `.pkl` được tạo khi huấn luyện và có thể tạo lại bằng `python run_pipeline.py`.

`.gitignore` chỉ ngăn Git theo dõi file trong các commit tiếp theo; nó không xóa file khỏi lịch sử commit trước đó. Nếu thông tin đăng nhập từng được commit, hãy thay mới thông tin đó.

---

## 📥 Cài đặt

1. Tải repository về máy và mở thư mục dự án.
2. Tạo và kích hoạt môi trường ảo:
   ```bash
   py -m venv venv
   # Trên Windows:
   .\venv\Scripts\Activate.ps1
   # Trên macOS/Linux:
   source venv/bin/activate
   ```
3. Cài các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

4. Thêm dữ liệu vào máy tại `archive/Salary_Data.csv` hoặc cấu hình `DATA_PATH` trỏ đến vị trí dữ liệu. Git bỏ qua các file dữ liệu; hãy kiểm tra giấy phép và điều khoản quyền riêng tư trước khi chia sẻ.

5. Tạo file cấu hình cục bộ từ tệp mẫu:
   ```powershell
   Copy-Item .env.example .env
   ```
   Trên macOS/Linux, dùng lệnh `cp .env.example .env`.

---

## ⚙️ Cấu hình (`.env`)

Chỉnh `.env` cục bộ ở thư mục gốc dự án. Không commit file này; `.env.example` chứa các giá trị mặc định an toàn:

- `DATA_PATH`: Đường dẫn đến dữ liệu CSV (mặc định: `archive/Salary_Data.csv`).
- `MODEL_TYPE`: Cách chọn mô hình: `auto` để benchmark và tự chọn mô hình tốt nhất, hoặc chỉ định `xgboost`, `catboost`, `random_forest` hay `ridge`.
- `RARE_THRESHOLD`: Tần suất tối thiểu để giữ một chức danh; chức danh ít gặp hơn được gom vào `"Other"` (mặc định: `20`).
- `TEST_SIZE`: Tỷ lệ dữ liệu dành cho tập holdout (mặc định: `0.2`).
- `RANDOM_STATE`: Giá trị khởi tạo để việc chia dữ liệu có thể lặp lại (mặc định: `42`).

## 🚀 Cách sử dụng

1. **Chạy pipeline huấn luyện:**

   ```bash
   python run_pipeline.py
   ```

   Lệnh này đọc `.env`, loại dòng trùng và dòng thiếu nhãn hoặc trường đầu vào, kiểm tra các biến dẫn xuất có nhất quán rồi chia train/holdout. Nếu `MODEL_TYPE=auto`, pipeline benchmark các mô hình trên train và chọn mô hình có MAE thấp nhất. Model đánh giá được giữ riêng để đo holdout; artifact triển khai được fit trên toàn bộ dòng hợp lệ và lưu tại `model_registry/best_salary_model.pkl`. Metadata giữ lại số đo holdout và model dùng cho phân tích SHAP.

   Chạy riêng `python benchmark_salary_models.py` sẽ cross-validation trên toàn bộ dữ liệu để tham khảo. Dùng holdout do `run_pipeline.py` tạo làm đánh giá cuối, tránh chọn và báo cáo model trên cùng kết quả CV.

2. **Dự đoán lương cho dữ liệu mới:**

   ```bash
   python predict_salary.py
   ```

   Mặc định, lệnh đọc `input/predict.csv` và lưu kết quả tại `output/salary_predictions.csv`. Đặt file cần dự đoán theo đường dẫn này hoặc đổi đường dẫn bằng `--input`; có thể đổi file kết quả bằng `--output` và model bằng `--model`:

   ```bash
   python predict_salary.py --input input/people_to_predict.csv --output output/result.csv
   ```

   File dự đoán phải có đủ 19 cột: `Age`, `Gender`, `Education Level`, `Job Title`, `Years of Experience`, `Education_Ordinal`, `Career_Start_Age`, `Seniority_Level`, `Job_Family`, `sim_avg_hours_per_week`, `sim_projects_completed`, `sim_years_at_company`, `sim_num_job_changes`, `sim_employment_type`, `sim_work_mode`, `sim_absence_days_per_month`, `sim_location_cost_level`, `sim_company_size` và `sim_industry`. Mỗi dòng phải có giá trị hợp lệ ở tất cả các cột; pipeline kiểm tra các cặp biến dẫn xuất và một số giới hạn hợp lý trước khi dự đoán. Chỉ nạp model `.pkl` đáng tin cậy do dự án tạo. Kết quả giữ lại các cột đầu vào và thêm `Predicted_Salary`.

3. **Tạo biểu đồ đánh giá và giải thích:**
   ```bash
   python explainability.py
   ```

   Lệnh này dùng holdout đã lưu trong model artifact để tạo `output/predicted_vs_actual.png` và `output/feature_importance_shap.png`.

4. **Chạy bộ test tự động:**
   ```bash
   pytest
   ```

   Các test sử dụng dữ liệu dự án cần có file CSV cục bộ.
