# Electricity Demand Forecasting (EDF)

**Product Requirements Document**
**Version:** 3.0
**Date:** December 13, 2023

## 1. Project Overview

### 1.1 Executive Summary
The Electricity Demand Forecasting (EDF) is a standalone, local analytical tool designed for national electricity utilities. It enables energy planners to generate accurate, multi-temporal forecasts (Hourly, Daily, Monthly) by integrating historical consumption data with meteorological, economic, and technological drivers (EVs, Solar).

The platform bridges the gap between short-term operational dispatch and long-term strategic planning in a single, unified interface.

### 1.2 Deployment Environment & Constraints
*   **Infrastructure:** Single Laptop (Windows 10/11).
*   **Distribution:** Python Source Code + Virtual Environment (`venv` managed by `uv`). **No Docker containers** allowed due to possible IT restrictions.
*   **Connectivity:** Capable of running offline (using cached data) but requires internet for fetching fresh weather data.

## 2. Technical Architecture

### 2.1 Architectural Pattern: "Modular Monolith"
The application uses a **FastAPI** core to serve both the backend logic and the **NiceGUI** frontend. It follows a strict separation of concerns:

*   **Frontend (NiceGUI):** Handles UI rendering, user state, and visualization. It communicates with the backend via direct **Service Layer** calls (not HTTP requests) to maximize local performance.
*   **Backend (Service Layer):** Handles data processing, DuckDB interactions, and Darts model execution. It is stateless regarding the UI.

### 2.2 Tech Stack
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language** | Python 3.12 | Core Runtime. |
| **Frontend** | **NiceGUI** | Web-based UI framework (running locally on `localhost`). |
| **Forecasting** | **Darts** / PyTorch | Unified API for statistical (ARIMA) and Deep Learning (Transformer) models. |
| **Database** | **DuckDB** | Primary persistent storage ("Source of Truth") for aligned time-series data. |
| **Data Proc** | **Pandas** | In-memory manipulation for training data preparation. |
| **Caching** | **Requests-Cache** | Persistence for External APIs (OpenMeteo) to prevent rate limits. |
| **Caching** | **DiskCache** | Local file caching for heavy intermediate calculations. |
| **Async** | `asyncio` | Manages non-blocking UI during model training. |

### 2.3 Proposed Project Structure
```text
EDF_Project/
├── data/                       # Stores .duckdb, .sqlite (cache), and logs
├── src/
│   ├── backend/                # THE LOGIC
│   │   ├── database/           # DuckDB schemas and connection logic
│   │   ├── services/           # Business Logic (Ingestion, Training, Forecasting)
│   │   ├── models/             # Pydantic models (Data validation)
│   │   └── utils/              # Async executors, logging
│   │
│   ├── frontend/               # THE UI
│   │   ├── components/         # Reusable widgets (Spinners, Charts)
│   │   ├── pages/              # UI Layouts (Home, Ingestion, Modeling)
│   │   └── main.py             # NiceGUI entry point
│   │
│   └── main_app.py             # Application Bootstrapper
├── requirements.txt
├── pyproject.toml              # Managed by uv
└── run.bat
```

## 3. Functional Requirements

### 3.1 Data Architecture & Ingestion
*   **Inputs:** Support for Excel (`.xlsx`) and CSV files.
*   **Ingestion Logic:**
    *   Validate schema (Date, Value columns).
    *   Detect duplicates and gaps (reporting them to the user, no auto-imputation).
    *   Store cleaned raw data into DuckDB tables (`master_load`, `master_weather`).
*   **Weather Integration:**
    *   Fetch historical weather via OpenMeteo API.
    *   **Strict Caching:** All API responses must be cached permanently (`expire_after=-1`) in a local SQLite file to ensure reproducibility and offline access.

### 3.2 Feature Engineering & Dataset Management
*   **Philosophy:** "Select, Don't Build." The platform provides a library of pre-coded, standardized feature transformers. Users mix and match these verified features to create immutable **"Prepared Datasets"** for training.
*   **Feature Catalog:**  The system maintains a registry of available transformations defined in the codebase. Examples include:lags, Heat-Index, is_weekend, holidays, etc. Registry can be develop using decorator.
*   **User Capabilities:** A UI allowing the user to select multiple feature groups from the catalog via checkboxes/switches.

### 3.3 Core Forecasting Engine
*   **Model Zoo:** The platform must support:
    1.  **Statistical:** ARIMA, Exponential Smoothing.
    2.  **ML:** XGBoost, LightGBM (via Darts).
    3.  **Deep Learning:** N-BEATS, N-HiTS, TFT (Temporal Fusion Transformer).
*   **Configuration:**
    *   Users can tweak simple integer/float parameters: `Epochs`, `Batch Size`, `Learning Rate`, `Attention Heads`, `Dropout`.
    *   **Hardware:** Support CPU training by default; detect CUDA (GPU) if available.
*   **Inference Scenarios:**
    *   Ability to swap "Future Covariates" sources (e.g., switch from `GDP_Baseline` to `GDP_High_Growth`) during the prediction phase to generate different forecast scenarios without retraining model weights.
*   **Async Execution:** Long-running training jobs (`model.fit()`) must run in a separate thread/process so the NiceGUI interface remains responsive (does not freeze).

### 3.4 Backtesting & Reporting
*   **Backtesting:** Rolling window evaluation.
    *   Configurable start date and stride.
    *   Metrics: MAPE, RMSE, MAE.
*   **Model Comparison:**
    *   Interface to overlay forecasts from multiple different models (e.g., ARIMA vs N-BEATS) on a single chart against Ground Truth.
    *   **Leaderboard:** Summary table ranking models by metric (e.g., Lowest MAPE) for the selected period.
*   **Reporting:**
    *   Interactive Plotly charts (Zoom/Pan).
    *   Export results to Excel (Raw numbers) and PNG (Charts).


### 3.5 Specialized "Bottom-Up" Modules
These act as post-processors on top of the baseline forecast.
1.  **EV Module:** Calculates load addition based on Year + Number of EVs + Charging Profile.
2.  **PV Module:** Calculates load subtraction based on Installed Capacity + Historical Irradiance.
3.  **Large Projects:** Step-change load additions based on start date and capacity.


## 4. User Interface (NiceGUI)

### 4.1 Navigation
*   **Sidebar:** Permanent navigation menu.
*   **Pages:**
    1.  **Home:** System Status.
    2.  **Data:** Uploads and Table Views (AG Grid).
    3.  **Model Lab:** Configuration, Training, and Validation.
    4.  **Forecast:** Scenario selection, Model Comparison, and Final Visualization.
    5.  **Settings:** Global configurations.

### 4.2 UX Requirements
*   **Feedback:** Toast notifications for success/failure.
*   **Progress:** Spinners or Progress Bars for async operations (Training/Ingestion).
*   **State:** User selections (e.g., "Selected Model") must persist when switching tabs.

## 5. Non-Functional Requirements

### 5.1 Performance
*   **Database:** DuckDB must handle queries on 20 years of hourly data (<200ms for standard aggregations).
*   **Memory:** Application must explicitly manage memory (delete Pandas dataframes after use) to prevent crashing on 8GB/16GB RAM laptops.

### 5.2 Reliability
*   **Error Handling:** "Graceful Degradation." If a model fails to converge (NaN loss), the app catches the error and suggests parameter changes, rather than crashing to desktop.
*   **Reproducibility:** Every forecast run is logged in the database with its configuration snapshot.
*   **Logging:** Implementation of rotating file logging (`app.log`) in the `/data` directory to capture stack traces (e.g., "DuckDB Locked", "CUDA OOM") for debugging support. Logs must not contain sensitive grid data.

## 6. Engineering Standards & Quality Assurance

### 6.1 Development Environment
*   **Package Manager:** `uv` (for deterministic dependency resolution and speed).
*   **Python Version:** 3.12 
*   **Code Style:**
    *   **Linter/Formatter:** `ruff` enforcing PEP-8 and standard conventions.
    *   **Type Checking:** `ty`  to prevent type-related runtime errors and ensure high-performance static analysis.

### 6.2 Testing Strategy (Regression Prevention)
*   **Automated Test Suite:** A `pytest` suite must accompany the source code.
*   **Coverage Requirements:**
    *   **Unit Tests:** High coverage (>80%) for Data Ingestion logic, Metric Calculations, and Scenario Math (EV/PV logic).
    *   **Integration Tests:** "Smoke tests" for the Training Pipeline (ensuring data flows from DB -> Model -> Result without crashing).
    *   **Data Validation:** Tests to ensure the system correctly flags invalid Excel inputs (e.g., negative demand, missing timestamps).
*   **CI/CD Workflow:** Local `pre-commit` hooks must run `ruff`, `ty`, and `pytest` before any code is committed to the main branch.
