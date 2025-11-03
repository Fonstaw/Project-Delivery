# app.py
import os
import asyncio
from flask import Flask
from bot import application  # Your Telegram bot app

app = Flask(__name__)

# Webhook route (for future)
@app.post("/webhook")
async def webhook():
    # Optional: Add secret token check later
    update = await request.json()
    await application.process_update(Update.de_json(update, application.bot))
    return "OK"

# Health check
@app.get("/")
def index():
    return "Bot is alive! 🚀"

# <<< ADD THIS: Start polling in background >>>
def run_polling():
    asyncio.run(application.run_polling())

if __name__ == "__main__":
    # For Render: Start polling in a thread + Flask
    from threading import Thread
    Thread(target=run_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
