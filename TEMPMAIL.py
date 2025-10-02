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

# Store user membership status to avoid repeated checks
user_membership_cache = {}

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is a member of the required group with better error handling"""
    user_id = update.effective_user.id
    
    # Check cache first
    if user_id in user_membership_cache:
        return user_membership_cache[user_id]
    
    try:
        member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
        user_membership_cache[user_id] = is_member
        return is_member
    except Exception as e:
        print(f"Error checking membership: {e}")
        # If we can't check membership, assume user is not member for security
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

async def send_force_subscription_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = None):
    """Send force subscription message with improved styling"""
    if message_text is None:
        message_text = (
            f"🔒 **Subscription Required**\n\n"
            f"To use this bot, you need to join our official group first!\n\n"
            f"📢 **Group:** {GROUP_USERNAME}\n"
            f"👥 **Members:** Active community\n"
            f"💬 **Content:** Latest updates & support\n\n"
            f"👉 Join now and get access to all features!"
        )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Join Group Now", url=GROUP_LINK)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error editing force sub message: {e}")
            # If editing fails, send a new message
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear any cached membership for this user
    user_id = update.effective_user.id
    user_membership_cache.pop(user_id, None)
    
    # Check if user is admin (admins bypass membership check)
    if is_authorized(update):
        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/SmartEdith_Bot"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/Tech_Shreyansh1")
            ]
        ]
        await update.message.reply_text(
            "🤖 **Welcome to TempGmail Bot!**\n\n"
            "📧 *Generate temporary Gmail variations*\n"
            "📄 Only Gmail addresses supported\n\n"
            "📝 **Please enter your Gmail address:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return GMAIL
    
    # For regular users, check membership
    is_member = await check_membership(update, context)
    
    if not is_member:
        await send_force_subscription_message(update, context)
        return ConversationHandler.END
    
    # User is member, proceed
    keyboard = [
        [
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/SmartEdith_Bot"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/Tech_Shreyansh1")
        ]
    ]
    await update.message.reply_text(
        "🎉 **Welcome to TempGmail Bot!**\n\n"
        "📧 *Generate temporary Gmail variations*\n"
        "📄 Only Gmail addresses supported\n\n"
        "📝 **Please enter your Gmail address:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return GMAIL

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        user_id = query.from_user.id
        # Clear cache for this user to force fresh check
        user_membership_cache.pop(user_id, None)
        
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
                    "✅ **Subscription Verified!**\n\n"
                    "🎉 Thanks for joining our group!\n\n"
                    "🤖 **Welcome to TempGmail Bot!**\n"
                    "📄 Only Gmail addresses supported\n\n"
                    "📝 **Please enter your Gmail address:**",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error editing message: {e}")
                # Send new message if editing fails
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="✅ **Subscription Verified!**\n\n"
                         "🎉 Thanks for joining our group!\n\n"
                         "🤖 **Welcome to TempGmail Bot!**\n"
                         "📄 Only Gmail addresses supported\n\n"
                         "📝 **Please enter your Gmail address:**",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            return GMAIL
        else:
            # User hasn't joined yet
            await send_force_subscription_message(
                update, 
                context,
                "❌ **Subscription Not Verified**\n\n"
                "We couldn't verify your membership in our group.\n\n"
                "⚠️ Please make sure you've:\n"
                "• Actually joined the group\n"
                "• Not left immediately after joining\n"
                "• Are using the same Telegram account\n\n"
                "Click the button below to join and try again!"
            )
            return ConversationHandler.END

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check membership for regular users (admins bypass)
    if not is_authorized(update):
        is_member = await check_membership(update, context)
        if not is_member:
            await send_force_subscription_message(update, context)
            return ConversationHandler.END
    
    user_gmail = update.message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', user_gmail):
        await update.message.reply_text(
            "❌ **Invalid Gmail Format**\n\n"
            "Please enter a valid Gmail address.\n"
            "Example: `yourname@gmail.com`",
            parse_mode="Markdown"
        )
        return GMAIL
    
    context.user_data['gmail'] = user_gmail
    
    keyboard = [
        [
            InlineKeyboardButton("🔹 Dot Variations", callback_data="method_dot"),
            InlineKeyboardButton("🔸 Plus Variations", callback_data="method_plus")
        ]
    ]
    
    await update.message.reply_text(
        f"✅ **Gmail Saved:** `{user_gmail}`\n\n"
        "🎯 **Choose Generation Method:**\n\n"
        "🔹 **Dot Variations**\n"
        "   *Adds dots between characters*\n"
        "   Example: `t.e.s.t@gmail.com`\n\n"
        "🔸 **Plus Variations**\n"
        "   *Adds random text after plus sign*\n"
        "   Example: `test+random@gmail.com`\n\n"
        "Click a button below to generate:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return METHOD

async def handle_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Check membership for regular users
    if not is_authorized(update):
        is_member = await check_membership(update, context)
        if not is_member:
            await send_force_subscription_message(update, context)
            return ConversationHandler.END
    
    method = query.data.replace("method_", "")
    gmail = context.user_data.get('gmail')
    
    if not gmail:
        await query.edit_message_text("❌ No Gmail found. Please /start again.")
        return ConversationHandler.END
    
    try:
        # Show generating message
        await query.edit_message_text("🔄 **Generating variations...**", parse_mode="Markdown")
        
        # Generate variations
        if method == 'dot':
            variations = generate_dot_variations(gmail)
            method_name = "Dot"
        else:
            variations = generate_plus_variations(gmail)
            method_name = "Plus"
        
        # Format response
        response = f"📧 **{method_name} Variations for:** `{gmail}`\n\n"
        response += '\n'.join([f"`{escape_markdown(v)}`" for v in variations])
        
        # Add usage tip
        response += f"\n\n💡 **Usage Tip:** All emails will deliver to `{gmail}`"
        
        # Send results
        await query.edit_message_text(response, parse_mode='MarkdownV2')
        
    except Exception as e:
        await query.edit_message_text(f"❌ **Error:** {str(e)}")
    
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

async def clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear membership cache (admin only)"""
    if is_authorized(update):
        user_membership_cache.clear()
        await update.message.reply_text("✅ Membership cache cleared!")
    else:
        await update.message.reply_text("❌ Admin only command.")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gmail)],
            METHOD: [CallbackQueryHandler(handle_method_selection, pattern="^method_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^check_membership$"))
    app.add_handler(CommandHandler("speed", speed_test))
    app.add_handler(CommandHandler("admin", admin_check))
    app.add_handler(CommandHandler("clearcache", clear_cache))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
