import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from flask import request
import config
from database import db
from utils import extract_numbers_from_text, validate_place_input, get_channel_for_order, format_order_preview
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_USER_TYPE, SELECTING_CAFE, CUSTOM_CAFE, ORDERING, NAME, GENDER, PHONE, TIME, FOOD, PLACE, CONFIRM_ORDER = range(11)

# User data keys
USER_TYPE = 'user_type'
CAFE = 'cafe'
ORDER_DATA = 'order_data'

# Global variable for bot application
bot_application = None

def setup_bot():
    """Setup and return the bot application"""
    global bot_application
    
    bot_application = Application.builder().token(config.BOT_TOKEN).build()
    setup_handlers(bot_application)
    
    return bot_application

def setup_handlers(application):
    """Setup all handlers for the bot"""
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("add_user", add_user))
    
    # Conversation handler for ordering process
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_user_type, pattern='^(contract_user|single_user)$')],
        states={
            SELECTING_USER_TYPE: [
                CallbackQueryHandler(select_cafe, pattern='^(ሸዊት|ፍቄ|አስኳል|መሲ|ኤ.ኤም|ሻሽ|custom_cafe)$'),
                CallbackQueryHandler(custom_cafe_input, pattern='^custom_cafe_input$')
            ],
            SELECTING_CAFE: [
                CallbackQueryHandler(start_ordering, pattern='^order_now$')
            ],
            CUSTOM_CAFE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_cafe)
            ],
            ORDERING: [
                CallbackQueryHandler(start_ordering, pattern='^order_now$')
            ],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            GENDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gender)
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time)
            ],
            FOOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_food)
            ],
            PLACE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_place)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern='^confirm_order$'),
                CallbackQueryHandler(restart_order, pattern='^restart_order$')
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    # Other callback handlers
    application.add_handler(CallbackQueryHandler(handle_single_user, pattern='^single_user$'))
    application.add_handler(CallbackQueryHandler(handle_cafe_selection, pattern='^(ሸዊት|ፍቄ|አስኳል|መሲ|ኤ.ኤም|ሻሽ|custom_cafe)$'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user_id = update.effective_user.id
    
    if not db.is_user_authorized(user_id):
        await update.message.reply_text(
            "❎ይህን ቦት ለመጠቀም አስቀድመው ይመዝገቡ!!\n"
            "🧾ለመመዝገብ @campusdeliveryy ያናግሩ።\n"
            "☎️ስልክ: 0923889620 ይደውሉ\n"
            "                0964180001 ይደውሉ"
        )
        return
    
    welcome_text = (
        "👋እንኳን ወደ ካምፓስ ዴሊቨሪ Bot በደህና መጡ።\n"
        "♥️እኛን ምርጫዎ ስላደረጉ ከልብ እናመሰግናለን።\n"
        "🍕 እባኮን የአገልግሎት ምርጫዎን ከስር ይምረጡ።"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("የ ኮንትራት ተጠቃሚ", callback_data="contract_user"),
            InlineKeyboardButton("ሲንግል order ተጠቃሚ", callback_data="single_user")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def select_user_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user type selection"""
    query = update.callback_query
    await query.answer()
    
    user_type = query.data
    context.user_data[USER_TYPE] = user_type
    
    if user_type == 'single_user':
        await handle_single_user(update, context)
        return ConversationHandler.END
    else:
        return await show_cafe_selection(update, context)

async def handle_single_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle single user order"""
    message_text = (
        "✅ሲንግል order በ Bot coming soon!!\n"
        "✅እስከዛ በዚ @campusdeliveryy ይዘዙ!\n"
        "☎️ስልክ: 0923889620 ይደውሉ\n"
        "                0964180001 ይደውሉ"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text)
    else:
        await update.message.reply_text(message_text)

async def show_cafe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cafe selection menu"""
    intro_text = (
        "🍝እባኮ የምርጫዎን ካፌ ከስር  ይምረጡ!!\n"
        "⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
    )
    
    keyboard = [
        [InlineKeyboardButton("አስኳል", callback_data="አስኳል")],
        [InlineKeyboardButton("ፍቄ", callback_data="ፍቄ")],
        [InlineKeyboardButton("ሸዊት", callback_data="ሸዊት")],
        [InlineKeyboardButton("መሲ", callback_data="መሲ")],
        [InlineKeyboardButton("ኤ.ኤም", callback_data="ኤ.ኤም")],
        [InlineKeyboardButton("ሻሽ", callback_data="ሻሽ")],
        [InlineKeyboardButton("የካፌውን ሰም ያስገቡ", callback_data="custom_cafe_input")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(intro_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(intro_text, reply_markup=reply_markup)
    
    return SELECTING_USER_TYPE

async def select_cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cafe selection"""
    query = update.callback_query
    await query.answer()
    
    cafe = query.data
    context.user_data[CAFE] = cafe
    
    return await show_ordering_page(update, context, cafe)

async def handle_cafe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cafe selection (alias for select_cafe)"""
    return await select_cafe(update, context)

async def custom_cafe_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for custom cafe name"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("👩‍🍳የመረጡትን ካፌ ስም ያስገቡ")
    return CUSTOM_CAFE

async def handle_custom_cafe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom cafe input"""
    cafe = update.message.text
    context.user_data[CAFE] = cafe
    
    return await show_ordering_page(update, context, cafe)

async def show_ordering_page(update: Update, context: ContextTypes.DEFAULT_TYPE, cafe: str):
    """Show ordering page"""
    intro_text = (
        f"🍝የ **{cafe}** ምግብ ቤት          ሜኑ ለማየት የስረኛውን ሊንክ ይጫኑ!!⬇️⬇️⬇️\n\n"
        "🍕ከመረጡ በኋላ ወደኋላ በመመለስ ከስር ያለውን\n"
        "⬇️⬇️ ይዘዙ በመምረጥ የሚጠየቁትን መረጀ\n"
        "በቅደም ተከተል ያስገቡ!!"
    )
    
    keyboard = [[InlineKeyboardButton("እዘዝ/Order now", callback_data="order_now")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(intro_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(intro_text, reply_markup=reply_markup)
    
    return ORDERING

async def start_ordering(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the ordering process"""
    query = update.callback_query
    await query.answer()
    
    # Initialize order data
    context.user_data[ORDER_DATA] = {
        'cafe': context.user_data.get(CAFE, ''),
        'order_number': db.get_next_order_number(),
        'user_id': update.effective_user.id
    }
    
    await query.edit_message_text("📄እባኮን ስም እስከነ አባት ያስገቡ:")
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    name = update.message.text
    context.user_data[ORDER_DATA]['name'] = name
    
    await update.message.reply_text("🧒👧ፆታ ምረጥ: ለወንድ M ለ ሴት F ይላኩ")
    return GENDER

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender input"""
    gender = update.message.text.upper()
    
    if gender not in ['M', 'F']:
        await update.message.reply_text("❊እባኮ M ወይም F ብቻ ይላኩ")
        return GENDER
    
    context.user_data[ORDER_DATA]['gender'] = gender
    
    await update.message.reply_text("☎️እባኮን ስልክ ቁጥር ያስገቡ:")
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    phone = update.message.text
    context.user_data[ORDER_DATA]['phone'] = phone
    
    await update.message.reply_text("⏰ሚፈለጉት ለምሳ ወይንስ ለ እራት ነዉ?")
    return TIME

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time input"""
    time = update.message.text
    context.user_data[ORDER_DATA]['time'] = time
    
    await update.message.reply_text("🍜 እባኮን የመረጡትን የምግብ ብዛት እና አይነት ያስገቡ:")
    return FOOD

async def handle_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle food input"""
    food = update.message.text
    
    # Extract numbers and calculate total
    success, total_items, total_price = extract_numbers_from_text(food)
    
    if not success:
        await update.message.reply_text(
            "❎እባኮ የምግቡን መጠን በ አሀዝ(1-9) ያካትቱ\n"
            "✅ምሳሌ:1 አይነት እና 1አትክልት"
        )
        return FOOD
    
    context.user_data[ORDER_DATA]['food'] = food
    context.user_data[ORDER_DATA]['total_items'] = total_items
    context.user_data[ORDER_DATA]['total_price'] = total_price
    
    await update.message.reply_text(
        "🏢በመጨረሻም ያሉበትን ግቢ ከነ Dorm Block number በዚህ Form መሰረት ያስገቡ:\n"
        "Main: Block number\n"
        "Tecno: Block number\n"
        "Agri: Block number"
    )
    return PLACE

async def handle_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle place input"""
    place = update.message.text
    
    if not validate_place_input(place):
        await update.message.reply_text(
            "🛡እባኮን ያሉበትን ግቢ በስርዐት በዚ መሰረት\n"
            "Main, Agri እና Tecno ማስገባቶን ያረጋግጡ!!"
        )
        return PLACE
    
    context.user_data[ORDER_DATA]['place'] = place
    
    # Show order preview
    return await show_order_preview(update, context)

async def show_order_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show order preview for confirmation"""
    order_data = context.user_data[ORDER_DATA]
    preview_text = format_order_preview(order_data)
    
    keyboard = [
        [
            InlineKeyboardButton("✅አረጋግጥ", callback_data="confirm_order"),
            InlineKeyboardButton("እንደገና ያስገቡ", callback_data="restart_order")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(preview_text, reply_markup=reply_markup)
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and process order"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    order_data = context.user_data[ORDER_DATA]
    
    # Check user balance
    user_balance = db.get_user_balance(user_id)
    if user_balance < order_data['total_price']:
        await query.edit_message_text(
            "🛡አሁን ያሎት ቀሪ ሒሳብ ማዘዝ አያስችሎትም!!\n"
            "🛡እባኮን ሂሳቦን ሞልተው በድጋሚ ይዘዙ።\n"
            "✅ሒሳብ ለመሙላት @campusdeliveryy ያናግሩ!"
        )
        return ConversationHandler.END
    
    # Deduct balance
    new_balance = user_balance - order_data['total_price']
    db.update_user_balance(user_id, new_balance)
    
    # Save order to database
    order_data['user_telegram_id'] = user_id
    order_data['created_at'] = datetime.now().isoformat()
    db.create_order(order_data)
    
    # Post to appropriate channel
    channel = get_channel_for_order(order_data['gender'], order_data['place'])
    channel_id = config.CHANNELS.get(channel)
    
    if channel_id:
        order_message = format_order_message(order_data)
        await context.bot.send_message(chat_id=channel_id, text=order_message)
    
    # Send success message to user
    await query.edit_message_text(
        "ትዕዛዞ በተሰካ ሁኔታ ተከናውኗል✅\n"
        "Campus ዴሊቨሪን ምርጫዎ ስላረጉ እናመሰግናለን"
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

async def restart_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the ordering process"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("📄እባኮን ስም እስከነ አባት ያስገቡ:")
    return NAME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text("ትዕዛዝ ተሰርዟል።")
    
    # Clear user data
    if ORDER_DATA in context.user_data:
        del context.user_data[ORDER_DATA]
    
    return ConversationHandler.END

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user balance"""
    user_id = update.effective_user.id
    
    if not db.is_user_authorized(user_id):
        await update.message.reply_text(
            "❎ይህን ቦት ለመጠቀም አስቀድመው ይመዝገቡ!!"
        )
        return
    
    balance = db.get_user_balance(user_id)
    await update.message.reply_text(f"💰የአሁኑ ቀሪ ሒሳብዎ: {balance:.2f} ETB")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to add user"""
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❎ይህ ትዕዛዝ ለአስተዳዳሪዎች ብቻ ነው።")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❎አጠቃቀም: /add_user <Telegram ID> <Fund>")
        return
    
    try:
        telegram_id = int(context.args[0])
        fund = float(context.args[1])
        
                success, error_msg = db.add_user(telegram_id, f"User_{telegram_id}", fund)
        if success
            await update.message.reply_text(f"✅ተጠቃሚ {telegram_id} በ {fund} ETB ተጨምሯል።")
        else:
            
            # Provide more detailed error message
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                await update.message.reply_text(f"❎ተጠቃሚ {telegram_id} ቀደም ብሎ ተጨምሯል። (User already exists)")
            else:
                await update.message.reply_text(f"❎ተጠቃሚን ማክበር አልተቻለም።\nError: {error_msg}")
    except ValueError:
        await update.message.reply_text("❎ትክክለኛ ያልሆነ ቁጥር።\n\nUsage: /add_user <Telegram_ID> <Balance>\nExample: /add_user 123456789 100")

def format_order_message(order_data: dict) -> str:
    """Format order message for channel posting"""
    return f"""📦 **አዲስ ትዕዛዝ #{order_data['order_number']}**

👩‍🍳 **ካፌ:** {order_data['cafe']}
👤 **ስም:** {order_data['name']}
🧒 **ፆታ:** {'ሴት' if order_data['gender'] == 'F' else 'ወንድ'}
☎️ **ስልክ:** {order_data['phone']}
⏰ **ሰዓት:** {order_data['time']}
🍜 **ምግብ:** {order_data['food']}
🏢 **ቦታ:** {order_data['place']}
💰 **ጠቅላላ:** {order_data['total_price']:.2f} ETB
🔢 **ብዛት:** {order_data['total_items']} እቃዎች

⏱ **ጊዜ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

def webhook_handler(flask_request):
    """Handle incoming webhook requests"""
    global bot_application
    
    if bot_application is None:
        bot_application = setup_bot()
    
    try:
        # Process the update
        update = Update.de_json(flask_request.get_json(), bot_application.bot)
        bot_application.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return 'Error', 500

def set_webhook():
    """Set webhook URL for the bot (run this once)"""
    import requests
    
    webhook_url = f"{config.APP_URL}/webhook"
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "drop_pending_updates": True
    }
    
    response = requests.post(url, json=payload)
    logger.info(f"Webhook setup response: {response.json()}")

def delete_webhook():
    """Delete webhook (use if switching back to polling)"""
    import requests
    
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook"
    response = requests.post(url)
    logger.info(f"Webhook delete response: {response.json()}")

# For backward compatibility - if you want to run with polling
def run_polling():
    """Run the bot with polling (alternative to webhook)"""
    application = setup_bot()
    application.run_polling()

