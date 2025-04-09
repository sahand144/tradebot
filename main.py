import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# === Start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    menu_keyboard = [
        ["📈 Market Trends", "📊 Technical Analysis"],
        ["💡 Buy/Sell Suggestions", "ℹ️ Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to your Trading Assistant Bot!\nChoose an option below:",
        reply_markup=reply_markup
    )

# === Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📈 Market Trends":
        await update.message.reply_text("📈 Market Trends: Bitcoin and Ethereum show upward momentum today.")
    elif text == "📊 Technical Analysis":
        await update.message.reply_text("📊 Simple Technical Analysis: RSI is around 60. Slight bullish signals.")
    elif text == "💡 Buy/Sell Suggestions":
        await update.message.reply_text("💡 Suggestion: Consider buying BTC if price breaks above resistance at $70K.")
    elif text == "ℹ️ Help":
        await update.message.reply_text("ℹ️ Use the menu to explore Market Trends, Technical Analysis, and Suggestions.")
    else:
        await update.message.reply_text("❓ I didn't understand that. Please use the menu options.")

# === Main Function ===
def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    BOT_TOKEN = os.getenv("BOT_TOKEN")  # Load from Railway Secrets or .env

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
