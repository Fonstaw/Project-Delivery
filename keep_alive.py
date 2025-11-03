import requests
import time
import os

def keep_alive():
    """Ping the app periodically to keep it awake"""
    url = os.getenv('APP_URL', 'https://your-app-name.koyeb.app')
    
    try:
        response = requests.get(f"{url}/health")
        print(f"Keep-alive ping: {response.status_code}")
    except Exception as e:
        print(f"Keep-alive failed: {e}")

if __name__ == "__main__":
    while True:
        keep_alive()
        time.sleep(300)  # Ping every 5 minutes