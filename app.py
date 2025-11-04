import os
import asyncio
from flask import Flask
from bot import Application as application  # ← Grab the real one!
from flask import Flask, request
from telegram import Update
from bot import setup_bot
from threading import Thread
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Reduce httpx logging to WARNING to prevent bot token leakage in logs
logging.getLogger("httpx").setLevel(logging.WARNING)

app = Flask(__name__)
bot_application = None
# Webhook route (for future)
@app.post("/webhook")
def webhook():
    # Optional: Add secret token check later
    
    global bot_application
    if bot_application is None:
        bot_application = setup_bot()
    
    update_data = request.get_json()
    update = Update.de_json(update_data, bot_application.bot)
    # Process update synchronously using asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot_application.process_update(update))
    finally:
        loop.close()
        
    return "OK"
# Health check
-5
+7
def index():
    return "Bot is alive! 🚀"

# Run Flask in background
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
if __name__ == "__main__":
    
# Start Flask in a thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot polling in main thread
    bot_application = setup_bot()
    bot_application.run_polling()
