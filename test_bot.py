import os
from bot import setup_bot

print("Testing bot setup...")
try:
    bot_app = setup_bot()
    print("✅ Bot setup successful!")
    print("✅ Handlers registered!")
except Exception as e:
    print(f"❌ Bot setup failed: {e}")
    import traceback
    traceback.print_exc()