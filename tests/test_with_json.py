import requests
import json
import os

# Configuration
URL = "http://localhost:8000/analyze_sleep"
API_KEY = "dev-key-12345" # Use 'prod-key-98765' if testing against Docker default
PAYLOAD_PATH = "tests/example_payload.json"

def test_api():
    if not os.path.exists(PAYLOAD_PATH):
        print(f"Error: {PAYLOAD_PATH} not found.")
        return

    with open(PAYLOAD_PATH, "r") as f:
        payload = json.load(f)

    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    print(f"Sending request to {URL}...")
    try:
        response = requests.post(URL, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Output:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Connection Error: Is the API server running at {URL}?")

if __name__ == "__main__":
    test_api()
