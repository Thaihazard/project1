# 📊 Báo Cáo Chi Tiết Dự Án: Salary Prediction ML Pipeline

Dự án này là một hệ thống Machine Learning End-to-End được thiết kế theo tiêu chuẩn công nghiệp (Production-grade), áp dụng kiến trúc **Hướng Đối Tượng (OOP)**, **Scikit-Learn Pipeline**, cấu hình động qua biến môi trường (`.env`), kiểm định chất lượng dữ liệu, đánh giá đa mô hình (Model Bake-off), giải thích mô hình (SHAP Explainability) và kiểm tra công bằng (Fairness Audit).

---

## 📁 1. Cấu Trúc Thư Mục & Vai Trò Từng File

```text
ML_Project/
├── archive/
│   └── Salary_Data.csv         # Tập dữ liệu thô (Raw dataset)
├── model_registry/
│   └── best_salary_model.pkl   # Artifact mô hình tốt nhất sau khi train & serialize (chứa pipeline, cleaner, metrics)
├── tests/
│   ├── test_pipeline.py        # Kiểm thử tích hợp (Integration tests) & kiểm thử suy luận
│   └── test_ml_oop.py          # Kiểm thử đơn vị (Unit tests) cho các OOP classes & transformers
├── docs/
│   └── project_explanation_report.md # Báo cáo giải thích chi tiết dự án
├── .env                        # File cấu hình biến môi trường (Config-driven architecture)
├── preprocessing.py            # Định nghĩa custom transformer, pipeline factory & data loader
├── run_pipeline.py             # Script điều phối chính: Huấn luyện động, auto bake-off, đánh giá & đóng gói model
├── predict_salary.py           # Script suy luận (Inference) cho dữ liệu nhân sự mới (hỗ trợ single & batch)
├── data_audit.py               # Script kiểm tra chất lượng dữ liệu (EDA, schema audit, phân phối & tương quan)
├── benchmark_salary_models.py  # Cross-validation và so sánh 4 mô hình hồi quy
├── explainability.py           # Script giải thích mô hình bằng SHAP values & kiểm tra thiên vị (Fairness Check)
└── requirements.txt            # Danh sách thư viện phụ thuộc Python
```

---

## 🔬 2. Giải Thích Chi Tiết Từng Module & Đoạn Code

### A. `preprocessing.py` (Tiền Xử Lý Dữ Liệu & Xây Dựng Pipeline)
Module này đóng vai trò nền tảng. Cleaner, imputer, scaler và encoder được đặt trong pipeline nên chỉ học thống kê từ phần dữ liệu huấn luyện của mỗi fold hoặc lần chia train/test.

1. **`SalaryCleaner` (Class kế thừa `BaseEstimator`, `TransformerMixin`)**:
   - **`_clean_education(series)`**: Chuẩn hóa các biến thể chính tả của trình độ học vấn (ví dụ: `"Bachelor'S"`, `"Bachelor'S Degree"`, `"phD"`, `"Ph.D."`) về các nhãn chuẩn thống nhất (`"Bachelor's"`, `"Master's"`, `"PhD"`). Đồng thời bảo toàn giá trị thiếu (`NaN`) để bộ điền khuyết (`Imputer`) xử lý phía sau.
   - **`fit(X, y)`**: Quét toàn bộ tập dữ liệu huấn luyện để:
     - Làm sạch cột `Education Level`.
     - Thống kê tần suất xuất hiện (`value_counts()`) của từng chức danh (`Job Title`). Xác định tập hợp các chức danh hiếm (có số lần xuất hiện nhỏ hơn ngưỡng `rare_threshold`, mặc định là 20) và lưu vào `self.rare_job_titles_`.
     - Lưu lại danh sách các chức danh được ghi nhận trong tập train vào `self.known_job_titles_`.
   - **`transform(X)`**: Áp dụng quy tắc học được từ `fit()` lên dữ liệu mới:
     - Chuẩn hóa học vấn.
     - Gom nhóm các chức danh hiếm hoặc chức danh hoàn toàn mới chưa từng thấy khi train (`unseen categories`) thành nhãn chung `"Other"`. Điều này ngăn chặn hiện tượng bùng nổ số chiều (dimensionality explosion) khi One-Hot Encoding.

2. **`load_and_clean_data(filepath)`**:
   - Đọc file CSV, loại bỏ dòng trùng lặp và dòng không có nhãn `Salary`.
   - Giữ lại các đặc trưng thiếu để imputer trong pipeline xử lý sau khi chia dữ liệu; trả về `X` và `y` mà không fit cleaner trên toàn bộ dữ liệu.

3. **`build_preprocessor()`**:
   - Sử dụng `ColumnTransformer` của Scikit-Learn để xử lý riêng biệt 2 nhóm cột:
     - **Numerical features (`Age`, `Years of Experience`)**: Điền giá trị thiếu bằng giá trị trung vị (`median`), sau đó chuẩn hóa tỉ lệ bằng `StandardScaler` (đưa về mean=0, variance=1).
     - **Categorical features (`Gender`, `Education Level`, `Job Title`)**: Điền giá trị thiếu bằng giá trị xuất hiện nhiều nhất (`most_frequent`), sau đó mã hóa nhãn dạng One-Hot với `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`.

4. **`SalaryPipelineFactory.create_pipeline(regressor, rare_threshold)`**:
   - Sử dụng **Factory Method Pattern** để tự động đóng gói toàn bộ quy trình thành một Pipeline hoàn chỉnh gồm 3 lớp lồng nhau:
     ```python
     full_pipeline = Pipeline([
         ('cleaner', SalaryCleaner(rare_threshold=rare_threshold)),
         ('model', TransformedTargetRegressor(
             regressor=Pipeline([
                 ('preprocessor', build_preprocessor()),
                 ('regressor', regressor)
             ]),
             func=np.log1p,
             inverse_func=np.expm1
         ))
     ])
     ```
   - **Giải thích chi tiết cấu trúc & Cơ chế hoạt động**:
     - **Lớp 1 (`cleaner`)**: Chạy đầu tiên khi nhận dữ liệu thô, làm sạch học vấn và gom nhóm chức danh hiếm.
     - **Lớp 2 (`model` / `TransformedTargetRegressor`)**: Giải quyết bài toán phân phối lương bị lệch phải (skewed right - nhân viên lương thấp rất nhiều, nhân viên lương cực cao ít nhưng kéo dài). 
       - Khi `.fit(X, y)`: Tự động biến đổi nhãn lương $y$ thành $\ln(y + 1)$ (`np.log1p`), giúp mô hình học trên không gian logarit ổn định hơn.
       - Khi `.predict(X)`: Mô hình dự đoán ra giá trị ở không gian log, sau đó hàm `np.expm1` ($e^{\text{pred}} - 1$) sẽ tự động dịch ngược kết quả về đúng đơn vị tiền tệ thực tế ($).
     - **Lớp 3 (Inner `Pipeline` - `preprocessor` + `regressor`)**: Xử lý đặc trưng đầu vào (`Age`, `Experience` qua Imputer + StandardScaler; `Gender`, `Education`, `Job Title` qua Imputer + OneHotEncoder) rồi đưa vào thuật toán hồi quy (`regressor`).

   - **🎯 Minh họa trực quan quy trình**:
     ```text
     [ Dữ liệu thô (Raw DataFrame) ]
                   │
                   ▼ (Bước 1: cleaner)
     [ Dữ liệu đã sạch văn bản & gom nhóm Job Title ]
                   │
                   ▼ (Bước 2: preprocessor)
     [ Đặc trưng X (Scaled/One-Hot) ] ──► [ Regressor học dự đoán ]
                   ▲                                    │
                   │ (Lúc Fit: log1p(y))                │ (Dự đoán ra log-salary)
               [ y_train ] ◄────────────────────────────┘
                                                        │
                                                        ▼ (Lúc Predict: expm1)
                                         [ Trả về Lương thực tế ($) ]
     ```

---

### B. `run_pipeline.py` (Pipeline Động & Cấu Hình Tập Trung)
Script điều phối toàn bộ chu trình huấn luyện thông qua tệp cấu hình `.env`.

1. **Cấu hình Động qua `.env`**:
   - Đọc các tham số: `DATA_PATH`, `MODEL_TYPE` (`auto`, `ridge`, `random_forest`, `xgboost`, `catboost`), `RARE_THRESHOLD`, `TEST_SIZE`, `RANDOM_STATE`.

2. **`get_model_instance(name)`**:
   - Hàm Factory trả về instance của mô hình tương ứng dựa trên tên cấu hình (Ridge, Random Forest, XGBoost hoặc CatBoost).

3. **Hàm `main()` (Quy trình thực thi chuẩn)**:
   - Đọc dữ liệu, lọc bỏ dòng trùng lặp và dòng thiếu nhãn `Salary`; các giá trị thiếu ở đặc trưng được imputer trong pipeline xử lý.
   - Chia tập dữ liệu thành `train` và `test` (tỷ lệ 80/20 theo `TEST_SIZE`).
   - **Chế độ `auto` (Model Bake-off tự động)**: Nếu cấu hình `MODEL_TYPE=auto`, script sử dụng **5-Fold Cross Validation** trên tập `train` để đánh giá 4 mô hình (`ridge`, `random_forest`, `xgboost`, `catboost`) dựa trên **MAE**, rồi chọn mô hình có MAE trung bình thấp nhất. Mỗi fold fit lại toàn bộ pipeline.
   - Huấn luyện mô hình chiến thắng trên toàn bộ tập huấn luyện.
   - Đánh giá trên tập kiểm tra độc lập (`X_test`, `y_test`), tính toán các chỉ số: **MAE**, **RMSE**, và **$R^2$ Score**.
   - **Huấn luyện cuối và đóng gói Artifact**: Sau khi chọn mô hình, fit mô hình mới trên toàn bộ tập train, đánh giá một lần trên holdout, rồi lưu pipeline, cleaner, tên mô hình, metrics và metadata holdout vào `model_registry/best_salary_model.pkl` bằng `joblib`.

---

### C. `predict_salary.py` (Suy Luận Dự Đoán)
1. **`SalaryPredictor` Class**:
   - **`__init__`**: Tự động nạp file artifact `best_salary_model.pkl` từ thư mục `model_registry/`.
   - **`_validate_input(df)`**: Kiểm tra tính hợp lệ của schema dữ liệu đầu vào (phải chứa đủ các cột bắt buộc: `Age`, `Gender`, `Education Level`, `Job Title`, `Years of Experience`).
   - **`predict_single(data_dict)`**: Nhận vào một từ điển thông tin nhân sự và trả về mức lương dự đoán dưới dạng số thực (`float`).
   - **`predict_batch(df)`**: Dự đoán hàng loạt cho một pandas DataFrame chứa danh sách nhân sự.

---

### D. Các Script Hỗ Trợ (`benchmark_salary_models.py`, `explainability.py`, `data_audit.py`)

- **`benchmark_salary_models.py`**: Cung cấp cross-validation cho `run_pipeline.py` để chọn mô hình chỉ từ tập train; khi chạy độc lập, so sánh 4 thuật toán (`Ridge`, `RandomForest`, `XGBoost`, `CatBoost`) và báo cáo MAE, RMSE, $R^2$, MAPE dưới dạng trung bình ± độ lệch chuẩn.
- **`explainability.py` (`SalaryExplainer`)**:
  - **SHAP Analysis**: Tính SHAP trên các dòng holdout đã lưu trong artifact. SHAP hiện biểu diễn đóng góp trên đầu ra `log1p(Salary)` của regressor, không phải đơn vị tiền lương.
  - **Phân tích sai số theo nhóm**: Báo số lượng mẫu, MAE và residual trung bình trên holdout theo `Gender` và `Education Level`. Đây là chẩn đoán mô tả, không phải chứng nhận công bằng.
- **`data_audit.py`**: Khảo sát nhanh cấu trúc DataFrame, kiểm tra giá trị khuyết thiếu, phát hiện bản ghi trùng lặp, thống kê mô tả phân phối lương và tính toán ma trận tương quan Pearson.
- **`SalaryModelTrainer` trong `run_pipeline.py`**: Điều phối việc chọn mô hình, huấn luyện mô hình cuối, đánh giá holdout và lưu artifact. Không còn trainer Random Forest riêng để tránh hai luồng cùng ghi đè một artifact.

---

### E. Hệ Thống Kiểm Thử (`tests/test_pipeline.py` & `tests/test_ml_oop.py`)
- Sử dụng framework **pytest** để kiểm tra tự động:
  - `test_preprocessing()`: Xác thực cơ chế làm sạch dữ liệu, loại bỏ trùng lặp và chuẩn hóa học vấn của `SalaryCleaner`.
  - `test_model_inference()`: Kiểm tra tính toàn vẹn của mô hình đã serialize, đảm bảo pipeline nạp thành công và trả về giá trị dự đoán hợp lệ (`> 0`).
  - `test_salary_pipeline_factory()` & `test_model_benchmarker()`: Đảm bảo tính đúng đắn của các factory và bộ benchmark.

---

## 🔄 3. Sơ Đồ Luồng Dữ Liệu (Data Flow Architecture)

```text
[ Raw CSV Data ]
       │
       ▼ (drop_duplicates & drop rows without Salary)
[ Data with feature missingness retained ]
       │
       ├──────────────────────────┐ (Train / Test Split - 80/20)
       ▼                          ▼
 [ X_train, y_train ]      [ X_test, y_test ]
       │                          │
       ▼                          │
 [ SalaryCleaner (fit on train only) ]
       │                          │
       ▼                          │
 [ TransformedTargetRegressor ]   │
   ├── log1p (Target Transform)   │
   └── Pipeline (Preprocessor)    │
         ├── Numerical Imputer + StandardScaler    │
         └── Categorical Imputer + OneHotEncoder   │
       │                          │
       ▼                          │
 [ Regressor Training ]           │
       │                          │
       ▼                          ▼
 [ Serialized Artifact (.pkl) ] ◄─ [ Evaluation Metrics (MAE, RMSE, R²) ]
       │
       ▼
 [ Inference (predict_salary.py) ] ──► [ Final Salary Prediction ($) ]
```

---

## 🚀 4. Hướng Dẫn Tái Tạo Toàn Bộ Dự Án (Reproduction Guide)

1. **Bước 1: Khởi tạo môi trường ảo Python & Cài đặt thư viện**
   ```bash
   python -m venv venv
   # Kích hoạt trên PowerShell:
   .\venv\Scripts\Activate.ps1
   # Cài đặt các gói phụ thuộc:
   pip install -r requirements.txt
   ```

2. **Bước 2: Kiểm định chất lượng dữ liệu (Data Audit)**
   ```bash
   python data_audit.py
   ```

3. **Bước 3: So sánh các thuật toán học máy (Model Bake-off Benchmark)**
   ```bash
   python benchmark_salary_models.py
   ```

4. **Bước 4: Huấn luyện động và đóng gói mô hình**
   - Tùy chỉnh tệp `.env` nếu cần (ví dụ: `MODEL_TYPE=auto` hoặc `MODEL_TYPE=random_forest`).
   - Chạy lệnh:
     ```bash
     python run_pipeline.py
     ```

5. **Bước 5: Chạy bộ kiểm thử tự động (Unit & Integration Tests)**
   ```bash
   python -m pytest
   ```

6. **Bước 6: Chạy suy luận dự đoán lương cho nhân sự mới**
   ```bash
   python predict_salary.py
   ```

---
