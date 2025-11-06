import os
import logging
from flask import Flask
from threading import Thread
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

@app.route('/')
def index():
    return "Campus Delivery Bot is alive! 🚀"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/debug')
def debug():
    return f"""
    Debug Info:
    - BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'MISSING'}
    - SUPABASE_URL: {'SET' if os.getenv('SUPABASE_URL') else 'MISSING'}
    - SUPABASE_KEY: {'SET' if os.getenv('SUPABASE_KEY') else 'MISSING'}
    - PORT: {os.getenv('PORT', '5000')}
    """

def run_bot():
    try:
        print("🔄 Attempting to import bot module...")
        from bot import setup_bot
        
        print("✅ Bot module imported successfully")
        bot_application = setup_bot()
        print("🤖 Bot setup complete, starting polling...")
        bot_application.run_polling()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    print("🚀 Starting application...")
    
    # Check environment variables
    required_vars = ['BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Missing environment variable: {var}")
    
    # Start bot in a separate thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started")
    
    # Give bot time to start
    time.sleep(3)
    
    # Start Flask
    run_flask()
