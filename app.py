import os
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

# Import and start bot directly in main process
try:
    logging.info("🤖 Starting Telegram bot...")
    from bot import setup_bot
    bot_app = setup_bot()
    
    # Start bot in background
    import threading
    def run_bot():
        bot_app.run_polling()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logging.info("✅ Bot started in background thread!")
    
except Exception as e:
    logging.error(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
