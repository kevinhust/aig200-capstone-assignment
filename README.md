# SleepInsight AI

SleepInsight AI is a machine learning-powered REST API that specifically analyzes sleep data from **Apple Health (Apple Watch)** to provide sleep scores, quality assessments, and personalized health recommendations.

## Project Overview

- **Author**: Zhihuai Wang
- **Task**: Regression (Sleep Score Prediction 0-100)
- **Framework**: FastAPI
- **Model**: RandomForestRegressor (trained on Kaggle Sleep Health & Efficiency datasets)
- **Deployment**: Live on **GCP Cloud Run**
- **CI/CD**: Fully automated via **GitHub Actions**
- **Analysis Engine**: Advanced rule-based interpretation for clinical health metrics
- **Live URL**: [https://sleepinsight-ai-agdeofj7eq-uc.a.run.app](https://sleepinsight-ai-agdeofj7eq-uc.a.run.app)

## Setup & Installation

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API server**:
   ```bash
   uvicorn src.main:app --reload
   ```

3. **API Key**:
   - Local: `dev-key-12345`
   - Production: `prod-key-98765`
   Pass the key in the `X-API-KEY` header.

## How to Demonstrate (Step-by-Step)

To showcase the API's functionality during the presentation, use the built-in **Swagger UI**:

1.  **Open the Interface**: Navigate to `https://sleepinsight-ai-agdeofj7eq-uc.a.run.app/docs`.
2.  **Authenticate**:
    *   Click the **Authorize** button (top right).
    *   Enter `prod-key-98765` in the Value field and click **Authorize**.
3.  **Upload Demo CSV**:
    *   Find **POST `/upload_health`**.
    *   Click **Try it out**.
    *   Click **Choose File** and select `tests/demo_sleep_data.csv`.
    *   Click the blue **Execute** button.
4.  **Analyze Results**: Review the `Responses` body to see the sleep score, insights, and AI recommendations.

## API Documentation

The API supports direct JSON analysis and raw health data uploads. Interactive documentation is available via Swagger UI at the Live URL's `/docs` endpoint.

### 1. `POST /analyze_sleep` (JSON Ingestion)
Analyze pre-parsed sleep metrics.

**Request Body**:
```json
{
  "age": 30,
  "gender": "Male",
  "sleep_duration_hr": 7.5,
  "heart_rate": 65,
  "stress_level": 3,
  "rem_percent": 22,
  "deep_percent": 18,
  "awakenings": 1,
  "breathing_disturbances_elevated": false
}
```

### 2. `POST /upload_health` (File Ingestion)
Directly upload health exports for automatic parsing and analysis.

**Supported Formats**:
- **ZIP**: Original `export.zip` from Apple Health.
- **XML**: Extracted `export.xml`.
- **CSV**: Lightweight pre-processed data (see format in `tests/demo_sleep_data.csv`).

## Real-World Usage Example

1. **Export**: Export your data from the Apple Health app (Profile -> Export All Health Data).
2. **Upload**: Use the `/upload_health` endpoint to upload your `export.zip`.
3. **Analysis**: Receive an instant 0-100 score and physical recovery insights.

### Demo Data
For presentation purposes, a sample CSV is provided at: `tests/demo_sleep_data.csv`. This file can be uploaded to the `/upload_health` endpoint to demo various sleep quality scenarios.

## Project Structure
- `src/main.py`: FastAPI application with endpoint logic and rule-based engine.
- `src/parse_apple_health.py`: XML parsing logic for Apple Watch data.
- `models/`: Trained model artifact (`RandomForestRegressor`).
- `Final_Project_Report.md`: Full assignment report with architecture and results.
- `archive/`: Project development requirements and process documents.
- `dockerfile`: Container configuration for GCP Cloud Run deployment.

## Disclaimer
This analysis is based on wearable device data and general health references. It is for informational purposes only and is not a medical diagnosis. Please consult a qualified health professional.
