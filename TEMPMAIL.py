import os
import random
import string
import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)

# Conversation states
GMAIL, METHOD = range(2)

# Configuration from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", "-1002512312056"))
GROUP_USERNAME = os.getenv("GROUP_USERNAME", "@MrGhostsx")
GROUP_LINK = f"https://t.me/{GROUP_USERNAME[1:]}" if GROUP_USERNAME.startswith('@') else GROUP_USERNAME
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is a member of the required group"""
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def is_authorized(update: Update) -> bool:
    """Check if user is admin"""
    user_id = update.effective_user.id
    return user_id in ADMIN_IDS

def generate_random_name(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def escape_markdown(text: str) -> str:
    escape_chars = r'\.\-+\@\_'
    return re.sub(f'([{escape_chars}])', r'\\\1', text)

def generate_dot_variations(gmail: str, count=50):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', gmail):
        return ["❌ Invalid Gmail format"]
    
    local, domain = gmail.split('@')
    variations = set()
    
    for i in range(1, len(local)):
        for j in range(i+1, len(local)+1):
            if len(variations) >= count:
                break
            variation = f"{local[:i]}.{local[i:j]}.{local[j:]}@{domain}"
            variations.add(variation)
    
    return list(variations)[:count]

def generate_plus_variations(gmail: str, count=50):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', gmail):
        return ["❌ Invalid Gmail format"]
    
    local, domain = gmail.split('@')
    variations = set()
    
    while len(variations) < count:
        variation = f"{local}+{generate_random_name()}@{domain}"
        variations.add(variation)
    
    return list(variations)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user is admin (admins bypass membership check)
    if is_authorized(update):
        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/SmartEdith_Bot"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/Tech_Shreyansh1")
            ]
        ]
        await update.message.reply_text(
            "🤖 Welcome to TempGmail Bot!\n"
            "📄 Only Gmail addresses supported\n"
            "📝 Please enter your Gmail address:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return GMAIL
    
    # For regular users, check membership
    is_member = await check_membership(update, context)
    
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("☘ Join Group", url=GROUP_LINK)],
            [InlineKeyboardButton("🍀 I've Joined", callback_data="check_membership")]
        ]
        await update.message.reply_text(
            f"❌ To use this bot, you must join our group {GROUP_USERNAME} first.\n"
            "Please join the group and then click 'I've Joined' button.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    # User is member, proceed
    keyboard = [
        [
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/SmartEdith_Bot"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/Tech_Shreyansh1")
        ]
    ]
    await update.message.reply_text(
        "🤖 Welcome to TempGmail Bot!\n"
        "📄 Only Gmail addresses supported\n"
        "📝 Please enter your Gmail address:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return GMAIL

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        is_member = await check_membership(update, context)
        
        if is_member:
            keyboard = [
                [
                    InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/SmartEdith_Bot"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/Tech_Shreyansh1")
                ]
            ]
            try:
                await query.edit_message_text(
                    "🍀 Thanks for joining!\n"
                    "🤖 Welcome to TempGmail Bot!\n"
                    "📄 Only Gmail addresses supported\n"
                    "📝 Please enter your Gmail address:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                print(f"Error editing message: {e}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="🍀 Thanks for joining!\n"
                         "🤖 Welcome to TempGmail Bot!\n"
                         "📄 Only Gmail addresses supported\n"
                         "📝 Please enter your Gmail address:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return GMAIL
        else:
            keyboard = [
                [InlineKeyboardButton("☘ Join Group", url=GROUP_LINK)],
                [InlineKeyboardButton("🍀 I've Joined", callback_data="check_membership")]
            ]
            try:
                await query.edit_message_text(
                    f"❌ You haven't joined {GROUP_USERNAME} yet.\n"
                    "Please join the group and then click 'I've Joined' button.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                print(f"Error editing message: {e}")
            return ConversationHandler.END

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check membership for regular users (admins bypass)
    if not is_authorized(update):
        is_member = await check_membership(update, context)
        if not is_member:
            keyboard = [
                [InlineKeyboardButton("☘ Join Group", url=GROUP_LINK)],
                [InlineKeyboardButton("🍀 I've Joined", callback_data="check_membership")]
            ]
            await update.message.reply_text(
                f"❌ To continue using this bot, you must join our group {GROUP_USERNAME} first.\n"
                "Please join the group and then click 'I've Joined' button.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END
    
    user_gmail = update.message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', user_gmail):
        await update.message.reply_text("❌ Invalid Gmail format. Please enter a valid Gmail address.")
        return GMAIL
    
    context.user_data['gmail'] = user_gmail
    await update.message.reply_text(
        "🍀 Gmail saved! Choose generation method:\n"
        "1️⃣ Type 'dot' for dot variations\n"
        "2️⃣ Type '+' for random name variations\n"
        "3️⃣ /start to reselect Gmail"
    )
    return METHOD

async def handle_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check membership for regular users (admins bypass)
    if not is_authorized(update):
        is_member = await check_membership(update, context)
        if not is_member:
            keyboard = [
                [InlineKeyboardButton("☘ Join Group", url=GROUP_LINK)],
                [InlineKeyboardButton("🍀 I've Joined", callback_data="check_membership")]
            ]
            await update.message.reply_text(
                f"❌ To continue using this bot, you must join our group {GROUP_USERNAME} first.\n"
                "Please join the group and then click 'I've Joined' button.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END
    
    method = update.message.text.lower().strip()
    
    if method not in ['dot', '+']:
        await update.message.reply_text("❌ Invalid method. Please enter 'dot' or '+'")
        return METHOD
    
    gmail = context.user_data.get('gmail')
    if not gmail:
        await update.message.reply_text("❌ No Gmail found. Please /start again.")
        return ConversationHandler.END
    
    try:
        variations = generate_dot_variations(gmail) if method == 'dot' else generate_plus_variations(gmail)
        response = '\n'.join(f"`{escape_markdown(v)}`" for v in variations)
        await update.message.reply_text(response, parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

async def speed_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("⏱ Testing speed...")
    end_time = time.time()
    elapsed = end_time - start_time
    try:
        await msg.edit_text(f"⚡ Bot response time: {elapsed:.3f} seconds")
    except Exception as e:
        print(f"Error editing speed test message: {e}")

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("🍀 You are an admin!")
    else:
        await update.message.reply_text("❌ You are not an admin.")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gmail)],
            METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_method)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("speed", speed_test))
    app.add_handler(CommandHandler("admin", admin_check))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
