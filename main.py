import os
import logging
import requests
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from googletrans import Translator

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App (for Railway hosting)
app = Flask(__name__)

translator = Translator()
user_strategies = {}

# Constants for conversation flow
ASKING_STRATEGY, CHAT_MODE = range(2)

@app.route('/')
def home():
    return "Bot is running!"

# Utility: Translate if Persian
async def translate_if_needed(text):
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return translator.translate(text, src='fa', dest='en').text
    return text

# Utility: Get real-time crypto/stock price
async def get_price(query):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={query}&vs_currencies=usd"
        r = requests.get(url).json()
        if query in r:
            return f"Price of {query.title()}: ${r[query]['usd']}"
        else:
            return "Sorry, couldn't find price info. Try full lowercase crypto ID like 'bitcoin'."
    except Exception as e:
        return f"Error fetching price: {str(e)}"

# Utility: Get latest news
async def get_news():
    if not NEWS_API_KEY:
        return "No NewsAPI key set. Skipping news."
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&q=crypto&apiKey={NEWS_API_KEY}"
        r = requests.get(url).json()
        articles = r.get("articles", [])[:5]
        news = "\n\n".join([f"{a['title']}\n{a['url']}" for a in articles])
        return f"📰 Latest Market News:\n\n{news}" if news else "No news found."
    except Exception as e:
        return f"Error fetching news: {str(e)}"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [["💹 Recommend"], ["💬 Chat with AI"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome! I’m your AI trading assistant 🤖. Choose an option:", reply_markup=markup)
    return CHAT_MODE

# Recommend command
async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Which trading strategy do you prefer? (e.g., RSI, MACD, Bollinger, Momentum, etc.)")
    return ASKING_STRATEGY

# Save strategy and proceed
async def handle_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    strategy = await translate_if_needed(update.message.text)
    user_strategies[user_id] = strategy
    await update.message.reply_text(f"Got it! Strategy set to: {strategy}\n\nNow tell me any crypto or stock you want to analyze:")
    return CHAT_MODE

# Main chatbot mode
async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = await translate_if_needed(update.message.text.lower())

    response_parts = []

    # Try to get price
    price = await get_price(query)
    response_parts.append(price)

    # Simulate prediction (mocked)
    response_parts.append(f"📈 AI prediction: Based on {user_strategies.get(user_id, 'default')} strategy, {query.title()} may rise in the next 24h 🚀")

    # Get news
    news = await get_news()
    response_parts.append(news)

    final_response = "\n\n".join(response_parts)
    await update.message.reply_text(final_response)
    return CHAT_MODE

# Fallback
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Session ended. Type /start to begin again.")
    return ConversationHandler.END

if __name__ == '__main__':
    app_builder = ApplicationBuilder().token(BOT_TOKEN)
    app = app_builder.build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex("^💹 Recommend"), recommend)],
        states={
            ASKING_STRATEGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_strategy)],
            CHAT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)

    # Run polling
    app.run_polling()
