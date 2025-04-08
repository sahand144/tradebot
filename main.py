import os
import logging
import requests
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackContext
)
from googletrans import Translator

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Optional, can skip news if not available

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Railway hosting
webapp = Flask(__name__)

# Translator
translator = Translator()

# Telegram Bot App
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Strategy options
STRATEGIES = ["Scalping", "Swing Trading", "Long-Term Investing"]

# Menu keyboard
menu_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔍 Search Asset"), KeyboardButton("📈 Set Strategy")],
    [KeyboardButton("📰 Get News"), KeyboardButton("⚠️ Price Alert (coming soon)")],
], resize_keyboard=True)

# --- Command Handlers --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to your AI Trading Assistant!\nHow can I help you today?",
        reply_markup=menu_keyboard
    )

async def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text

    # Translate Persian to English if needed
    lang = translator.detect(user_input).lang
    if lang == 'fa':
        user_input = translator.translate(user_input, src='fa', dest='en').text

    # Parse and respond
    if "search" in user_input.lower() or any(char.isalpha() for char in user_input):
        await get_asset_info(update, context, user_input)
    elif "strategy" in user_input.lower():
        await update.message.reply_text("Choose your preferred strategy: " + ", ".join(STRATEGIES))
    elif "news" in user_input.lower():
        await get_market_news(update)
    elif "price alert" in user_input.lower():
        await update.message.reply_text("⚠️ Price alert feature coming soon!")
    else:
        await update.message.reply_text("I didn't get that, can you rephrase?")

# --- Features --- #

async def get_asset_info(update: Update, context: CallbackContext, symbol: str):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
        r = requests.get(url).json()
        price = r.get(symbol.lower(), {}).get("usd")

        if price:
            await update.message.reply_text(f"💰 Current price of {symbol.upper()} is ${price}")
        else:
            await update.message.reply_text(f"❌ Couldn't find price for {symbol.upper()}.")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Error fetching asset info.")

async def get_market_news(update: Update):
    if not NEWS_API_KEY:
        await update.message.reply_text("News feature requires a NEWS_API_KEY. Add it to your .env file.")
        return

    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        headlines = [a['title'] for a in res.get("articles", [])[:5]]

        if headlines:
            await update.message.reply_text("📰 Top News:\n\n" + "\n\n".join(headlines))
        else:
            await update.message.reply_text("No news found.")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Error getting news.")

# --- Flask Route for Webhook --- #

@webapp.route("/")
def home():
    return "Bot is running!"

# --- Main Execution --- #
if __name__ == '__main__':
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
