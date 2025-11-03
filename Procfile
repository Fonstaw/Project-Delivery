web: gunicorn app:app --bind 0.0.0.0:$PORT
worker: python -c "from app import app; import requests; requests.get('https://your-app-name.koyeb.app/keep-alive')"