from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
import joblib
import pandas as pd
import numpy as np
import os
import shutil
import tempfile
from src.parse_apple_health import parse_health_data

app = FastAPI(title="SleepInsight AI API")

# Load model pipeline
MODEL_PATH = "models/sleep_model_pipeline.pkl"
model = None
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded successfully from {MODEL_PATH}")
    else:
        print(f"WARNING: Model file not found at {MODEL_PATH}")
except Exception as e:
    print(f"ERROR: Failed to load model: {str(e)}")
    # We don't raise an exception here to let the app start and listen on the port,
    # which avoids a Cloud Run 'container failed to start' error.

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
    if dur >= 7 and dur <= 9:
        interp = "Ideal sleep duration for cognitive function and physical health."
    elif dur < 7:
        interp = f"Duration ({dur}h) is below the recommended 7-9 hours. This can lead to sleep debt."
    else:
        interp = "Oversleeping detected. Occasionally normal, but chronic oversleeping may be linked to underlying issues."
    
    analysis.append(MetricAnalysis(
        metric="Sleep Duration",
        user_value=f"{dur} hours",
        normal_range="7–9 hours",
        interpretation=interp
    ))
    
    # 2. Deep Sleep
    if data.deep_percent is not None:
        val = data.deep_percent
        if val >= 18:
            interp = "Excellent deep sleep percentage. This is crucial for physical recovery and growth hormone release."
        elif val >= 13:
            interp = "Deep sleep is within the normal range for physical restoration."
        else:
            interp = "Deep sleep is low. You may feel physically unrefreshed or have muscle soreness."
        
        analysis.append(MetricAnalysis(
            metric="Deep Sleep",
            user_value=f"{val}%",
            normal_range="13–23%",
            interpretation=interp
        ))

    # 3. REM Sleep
    if data.rem_percent is not None:
        val = data.rem_percent
        if val >= 20:
            interp = "Healthy REM sleep. Essential for memory consolidation and emotional processing."
        else:
            interp = "REM sleep is slightly below average. This might affect your mood or mental clarity."
        
        analysis.append(MetricAnalysis(
            metric="REM Sleep",
            user_value=f"{val}%",
            normal_range="20–25%",
            interpretation=interp
        ))

    # 4. Heart Rate (Resting/Avg during sleep)
    if data.heart_rate is not None:
        hr = data.heart_rate
        if hr < 60:
            interp = "Heart rate is low (Athletic range). Generally a sign of good cardiovascular fitness."
        elif hr <= 80:
            interp = "Heart rate is in the healthy resting range."
        else:
            interp = "Elevated sleeping heart rate. Could be due to stress, late meals, or lack of recovery."
        
        analysis.append(MetricAnalysis(
            metric="Sleeping Heart Rate",
            user_value=f"{hr} bpm",
            normal_range="60–100 bpm",
            interpretation=interp
        ))

    # 5. Stress Level
    if data.stress_level is not None:
        sl = data.stress_level
        if sl <= 3:
            interp = "Low stress levels detected. Your nervous system is well-regulated."
        elif sl <= 6:
            interp = "Moderate stress. Consider relaxation techniques before bed."
        else:
            interp = "High physiological stress. This significantly impacts sleep quality and recovery."
        
        analysis.append(MetricAnalysis(
            metric="Stress Level",
            user_value=f"{sl}/10",
            normal_range="< 4.0",
            interpretation=interp
        ))

    # 6. Overall Performance
    analysis.append(MetricAnalysis(
        metric="Overall Performance",
        user_value=f"Score: {score:.1f}",
        normal_range="70–100",
        interpretation=f"Based on your metrics, your sleep quality is {get_quality_tier(score)}."
    ))
        
    return analysis

@app.post("/analyze_sleep", response_model=SleepAnalysisResponse)
async def analyze_sleep(data: SleepInput, api_key: str = Depends(verify_api_key)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Prepare input for model
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
    
    # Dynamic Recommendations
    recs = ["Maintain a consistent sleep schedule"]
    
    if data.sleep_duration_hr < 7:
        recs.append("Prioritize an earlier bedtime to meet the 7-hour minimum requirement.")
    
    if data.deep_percent is not None and data.deep_percent < 15:
        recs.append("To boost deep sleep, ensure your bedroom is cool (around 18°C) and completely dark.")
        
    if data.rem_percent is not None and data.rem_percent < 20:
        recs.append("Improve REM sleep by avoiding alcohol and heavy meals 3 hours before bed.")
        
    if data.heart_rate is not None and data.heart_rate > 75:
        recs.append("Your sleeping HR is slightly high; try magnesium or a warm bath before sleep.")
        
    if data.stress_level is not None and data.stress_level > 5:
        recs.append("Incorporate 10 minutes of deep breathing or meditation to lower pre-sleep stress.")

    if data.awakenings is not None and data.awakenings > 2:
        recs.append("Multiple awakenings detected; check for environmental noise or try white noise.")

    # Medical Triggers
    summary = f"Your SleepInsight Score is {score:.1f} ({tier})."
    if data.breathing_disturbances_elevated or data.apnea_notification_received:
        summary += " WARNING: Abnormal breathing patterns or apnea alerts detected."
        recs.append("URGENT: Based on breathing signals, we strongly recommend a formal clinical sleep study (Polysomnography).")
    
    return SleepAnalysisResponse(
        sleep_score=score,
        quality_tier=tier,
        key_insights={
            "duration_hr": data.sleep_duration_hr,
            "deep_pct": data.deep_percent,
            "rem_pct": data.rem_percent,
            "hr_bpm": data.heart_rate
        },
        detailed_analysis=analysis,
        summary_opinion=summary,
        recommendations=recs,
        disclaimer="SleepInsight AI is an informational tool. These findings are NOT a medical diagnosis. Consult a doctor for health concerns."
    )

@app.post("/upload_health", response_model=SleepAnalysisResponse)
async def upload_health(file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    import zipfile
    
    # Create a temporary file to store the upload
    suffix = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        file_path = tmp.name

    try:
        final_path = file_path
        tmp_dir = None
        
        # If it's a zip, extract it
        if suffix == ".zip":
            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            
            # Find the export.xml (usually in apple_health_export/export.xml)
            # We look for any .xml file recursively
            xml_found = False
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    if f.lower() == "export.xml":
                        final_path = os.path.join(root, f)
                        xml_found = True
                        break
                if xml_found: break
            
            if not xml_found:
                raise HTTPException(status_code=400, detail="No export.xml found in the uploaded ZIP file")

        # Handle CSV files
        if suffix == ".csv":
            try:
                df_upload = pd.read_csv(final_path)
                if df_upload.empty:
                    raise HTTPException(status_code=400, detail="Uploaded CSV is empty")
                
                # Take the first row if multiple exist
                row = df_upload.iloc[0].to_dict()
                
                # Map CSV columns to SleepInput fields
                metrics = {
                    "age": int(row.get("age", 30)),
                    "gender": str(row.get("gender", "Other")),
                    "sleep_duration_hr": float(row.get("sleep_duration_hr", 7.0)),
                    "heart_rate": float(row.get("heart_rate")) if pd.notnull(row.get("heart_rate")) else None,
                    "stress_level": float(row.get("stress_level", 3.0)),
                    "rem_percent": float(row.get("rem_percent")) if pd.notnull(row.get("rem_percent")) else None,
                    "deep_percent": float(row.get("deep_percent")) if pd.notnull(row.get("deep_percent")) else None,
                    "awakenings": float(row.get("awakenings", 0)),
                    "breathing_disturbances_elevated": bool(row.get("breathing_disturbances_elevated", False)),
                    "apnea_notification_received": bool(row.get("apnea_notification_received", False))
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error parsing CSV data: {str(e)}")
        else:
            # Parse the health data
            metrics = parse_health_data(final_path)
            
        if not metrics:
            raise HTTPException(status_code=400, detail="Could not parse health data from file")
        
        # Convert parsed metrics to SleepInput model
        sleep_data = SleepInput(**metrics)
        
        # Reuse analyze_sleep logic by calling the function directly or duplicating
        # Here we duplicate for simplicity/clarity in this chunk
        input_df = pd.DataFrame([{
            'age': sleep_data.age,
            'gender': sleep_data.gender,
            'sleep_duration_hr': sleep_data.sleep_duration_hr,
            'heart_rate': sleep_data.heart_rate,
            'stress_level': sleep_data.stress_level,
            'rem_percent': sleep_data.rem_percent,
            'deep_percent': sleep_data.deep_percent,
            'awakenings': sleep_data.awakenings
        }])
        
        score = model.predict(input_df)[0]
        score = max(0, min(100, score))
        tier = get_quality_tier(score)
        analysis = generate_detailed_analysis(sleep_data, score)
        
        recs = ["Maintain a consistent sleep schedule", "Reduce blue light exposure 1 hour before bed"]
        if sleep_data.sleep_duration_hr < 7:
            recs.append("Try going to bed 30 minutes earlier to increase total duration")
        
        summary = f"Your sleep score is {score:.1f}, categorized as {tier}."
        if sleep_data.breathing_disturbances_elevated or sleep_data.apnea_notification_received:
            summary += " Note: Abnormal breathing disturbance signals detected; consulting a medical professional is recommended."
            recs.append("Strongly consider consulting a sleep specialist.")
            
        return SleepAnalysisResponse(
            sleep_score=score,
            quality_tier=tier,
            key_insights={
                "duration": sleep_data.sleep_duration_hr,
                "deep": sleep_data.deep_percent,
                "rem": sleep_data.rem_percent
            },
            detailed_analysis=analysis,
            summary_opinion=summary,
            recommendations=recs,
            disclaimer="This analysis is based on uploaded Apple Health data."
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    # Use the PORT environment variable if available (default for Cloud Run)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
