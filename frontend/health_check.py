import requests

BACKEND_URL = "http://localhost:8000/health"

if __name__ == "__main__":
    try:
        resp = requests.get(BACKEND_URL)
        print("Status code:", resp.status_code)
        print("Response:", resp.json())
    except Exception as e:
        print("Error contacting backend:", e) 