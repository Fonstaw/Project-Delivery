import os
import logging
from flask import Flask

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def home():
    return "🍕 Bot running!"

@app.route('/health')
def health():
    return "OK", 200

# Start bot directly (no threading)
try:
    logging.info("🤖 Starting bot...")
    from bot import setup_bot
    bot_app = setup_bot()
    
    # Import this to make run_polling work properly
    import asyncio
    
    # Start bot in background
    def start_bot():
        asyncio.run(bot_app.run_polling())
    
    import threading
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    logging.info("✅ Bot started!")
    
except Exception as e:
    logging.error(f"❌ Bot error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
