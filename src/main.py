from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import joblib
import pandas as pd
import numpy as np
import os

app = FastAPI(title="SleepInsight AI API")

# Load model pipeline
MODEL_PATH = "models/sleep_model_pipeline.pkl"
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None

# Simple API Key Authentication
API_KEY = os.getenv("SLEEPINSIGHT_API_KEY", "dev-key-12345")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

class SleepInput(BaseModel):
    age: int
    gender: str # 'Male', 'Female', 'Other'
    sleep_duration_hr: float
    heart_rate: Optional[float] = None
    stress_level: Optional[float] = None
    rem_percent: Optional[float] = None
    deep_percent: Optional[float] = None
    awakenings: Optional[float] = None
    # Medical flags
    breathing_disturbances_elevated: bool = False
    apnea_notification_received: bool = False

class MetricAnalysis(BaseModel):
    metric: str
    user_value: str
    normal_range: str
    interpretation: str

class SleepAnalysisResponse(BaseModel):
    sleep_score: float
    quality_tier: str
    key_insights: dict
    detailed_analysis: List[MetricAnalysis]
    summary_opinion: str
    recommendations: List[str]
    disclaimer: str

def get_quality_tier(score: float) -> str:
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 50: return "Fair"
    return "Poor"

def generate_detailed_analysis(data: SleepInput, score: float) -> List[MetricAnalysis]:
    analysis = []
    
    # 1. Sleep Duration
    dur = data.sleep_duration_hr
    interp = "Ideal sleep duration." if 7 <= dur <= 9 else "Duration is short; consider increasing sleep." if dur < 7 else "Duration is longer than average."
    analysis.append(MetricAnalysis(
        metric="Sleep Duration",
        user_value=f"{dur} hours",
        normal_range="7–9 hours",
        interpretation=interp
    ))
    
    # 2. Efficiency / Score-based
    analysis.append(MetricAnalysis(
        metric="Overall Score",
        user_value=f"{score:.1f}",
        normal_range=">70 (Good)",
        interpretation=f"Current quality is {get_quality_tier(score)}."
    ))
    
    # 3. Deep Sleep (if provided)
    if data.deep_percent is not None:
        val = data.deep_percent
        interp = "Deep sleep percentage is ideal for recovery." if val >= 18 else "Deep sleep percentage is slightly low, which may affect physical recovery."
        analysis.append(MetricAnalysis(
            metric="Deep Sleep Percentage",
            user_value=f"{val}%",
            normal_range="13–23%",
            interpretation=interp
        ))
        
    return analysis

@app.post("/analyze_sleep", response_model=SleepAnalysisResponse)
async def analyze_sleep(data: SleepInput, api_key: str = Depends(verify_api_key)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Prepare input for model
    # Features: ['age', 'sleep_duration_hr', 'heart_rate', 'stress_level', 'rem_percent', 'deep_percent', 'awakenings', 'gender']
    input_df = pd.DataFrame([{
        'age': data.age,
        'gender': data.gender,
        'sleep_duration_hr': data.sleep_duration_hr,
        'heart_rate': data.heart_rate,
        'stress_level': data.stress_level,
        'rem_percent': data.rem_percent,
        'deep_percent': data.deep_percent,
        'awakenings': data.awakenings
    }])
    
    # Prediction
    score = model.predict(input_df)[0]
    score = max(0, min(100, score)) # Clip to 0-100
    
    tier = get_quality_tier(score)
    analysis = generate_detailed_analysis(data, score)
    
    # Recommendations
    recs = ["Maintain a consistent sleep schedule", "Reduce blue light exposure 1 hour before bed"]
    if data.sleep_duration_hr < 7:
        recs.append("Try going to bed 30 minutes earlier to increase total duration")
    
    # Medical Triggers
    summary = f"Your sleep score is {score:.1f}, categorized as {tier}."
    if data.breathing_disturbances_elevated or data.apnea_notification_received:
        summary += " Note: Abnormal breathing disturbance signals detected; consulting a medical professional is recommended."
        recs.append("Strongly consider consulting a sleep specialist, especially if you experience excessive daytime sleepiness.")
    
    return SleepAnalysisResponse(
        sleep_score=score,
        quality_tier=tier,
        key_insights={
            "duration": data.sleep_duration_hr,
            "deep": data.deep_percent,
            "rem": data.rem_percent
        },
        detailed_analysis=analysis,
        summary_opinion=summary,
        recommendations=recs,
        disclaimer="This analysis is based on Apple Health (Apple Watch) data and is for informational purposes only, not for medical diagnosis."
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
