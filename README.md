# SleepInsight AI

SleepInsight AI is a machine learning-powered REST API that specifically analyzes sleep data from **Apple Health (Apple Watch)** to provide sleep scores, quality assessments, and personalized health recommendations.

## Project Overview

- **Task**: Regression (Sleep Score Prediction 0-100)
- **Framework**: FastAPI
- **Model**: RandomForestRegressor (trained on Kaggle Sleep Health & Efficiency datasets)
- **Deployment**: Dockerized + GCP Cloud Run (Planned)

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
   Default development key is `dev-key-12345`. Pass it in the `X-API-KEY` header.

### Docker

1. **Build the image**:
   ```bash
   docker build -t sleepinsight-ai .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 -e SLEEPINSIGHT_API_KEY=your-secret-key sleepinsight-ai
   ```

## API Usage

### `POST /analyze_sleep`

**Headers**:
- `X-API-KEY`: Your API Key

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

**Output**:
- `sleep_score`: Quantitative score.
- `quality_tier`: Categorical quality.
- `detailed_analysis`: Breakdown of metrics.
- `recommendations`: Actionable advice.
- `disclaimer`: Medical disclaimer.

## Real-World Usage Example (Apple Health)

The system includes a parser for Apple Health XML exports. To test with your data:
1. Export your Health data from the Health app (Profile -> Export All Health Data).
2. Use `src/parse_apple_health.py` to get your metrics.
3. Call the API with the resulting JSON.

### Sample Real-World Result:
- **Input**: Sleep Duration: 7.93h, Deep Sleep: 12.5%
- **Analysis**: "Deep sleep percentage is slightly low, which may affect physical recovery."

## Data Sources
...
