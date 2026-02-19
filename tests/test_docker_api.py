import requests
import json

BASE_URL = "http://localhost:8001" # Running in Docker on 8001
API_KEY = "prod-key-98765" # Production key defined in Dockerfile
HEADERS = {"X-API-KEY": API_KEY}

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Health Check Failed: {e}")

def test_analyze_sleep():
    payload = {
        "age": 23,
        "gender": "Female",
        "sleep_duration_hr": 6.2,
        "heart_rate": 72,
        "stress_level": 6,
        "rem_percent": 15,
        "deep_percent": 12,
        "awakenings": 3,
        "breathing_disturbances_elevated": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze_sleep", headers=HEADERS, json=payload)
        print(f"\nAnalyze Sleep Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(response.text)
    except Exception as e:
        print(f"Analyze Sleep Failed: {e}")

if __name__ == "__main__":
    test_health()
    test_analyze_sleep()
