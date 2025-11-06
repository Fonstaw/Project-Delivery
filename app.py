import os
import logging
from flask import Flask
from bot import setup_bot
from threading import Thread

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Reduce httpx logging to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)

app = Flask(__name__)

# Health check routes
@app.route('/')
def index():
    return "Campus Delivery Bot is alive! 🚀"

@app.route('/health')
def health():
    return "OK", 200

# Run Flask server
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def run_bot():
    """Run the bot in polling mode"""
    try:
        bot_application = setup_bot()
        print("🤖 BOT STARTED — POLLING MODE ACTIVE")
        bot_application.run_polling()
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")

if __name__ == "__main__":
    print("🚀 Starting Campus Delivery Bot System...")
    
    # Start bot in main thread (polling needs to be in main thread)
    bot_thread = Thread(target=run_bot, daemon=False)
    bot_thread.start()
    
    # Start Flask in main thread (Koyeb needs web server in main thread)
    print("🌐 Starting Flask web server...")
    run_flask()
