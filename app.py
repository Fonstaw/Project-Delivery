from flask import Flask, request
from bot import setup_bot, webhook_handler
import os

app = Flask(__name__)

# Initialize bot
application = setup_bot()

@app.route('/')
def home():
    return "Campus Delivery Bot is running! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    return webhook_handler(request)

@app.route('/health')
def health_check():
    return {"status": "healthy", "message": "Bot is running"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)