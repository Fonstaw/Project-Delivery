import os
import threading
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def home():
    return "🍕 Campus Delivery Bot is running! Send /start in Telegram."

@app.route('/health')
def health():
    return "OK", 200

def start_bot():
    """Start the Telegram bot in polling mode"""
    try:
        logging.info("🤖 Starting Telegram bot...")
        from bot import setup_bot
        
        bot_app = setup_bot()
        logging.info("✅ Bot setup complete, starting polling...")
        bot_app.run_polling()
        
    except Exception as e:
        logging.error(f"❌ Bot failed to start: {e}")

# Start the bot when the app loads (for Gunicorn)
if not os.environ.get("WERKZEUG_RUN_MAIN"):  # This prevents double-starting in reloader
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    logging.info("🚀 Bot thread started!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
