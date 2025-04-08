import logging
import os
import requests
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread
from googletrans import Translator
import datetime
import yfinance as yf

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Setup
BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
translator = Translator()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Helper Functions
def get_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    price = data.get(symbol, {}).get("usd")
    return price

def get_news():
    if not NEWS_API_KEY:
        return "🛑 News API Key not set."
    url = f"https://newsapi.org/v2/top-headlines?q=stock+OR+crypto&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url).json()
    articles = response.get("articles", [])[:5]
    return "\n\n".join([f"📰 {a['title']}\n{a['url']}" for a in articles])

def predict_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        closing = hist['Close']
        recent_price = closing[-1]
        average = closing.mean()
        if recent_price > average:
            return f"📊 Prediction: Price may drop soon.\nCurrent: ${recent_price:.2f} | 30d Avg: ${average:.2f}"
        else:
            return f"📈 Prediction: Price may rise.\nCurrent: ${recent_price:.2f} | 30d Avg: ${average:.2f}"
    except:
        return "❌ Couldn't retrieve historical data. Try a valid stock/crypto ticker."

# AI-style Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    lang = translator.detect(user_input).lang
    if lang == "fa":
        user_input = translator.translate(user_input, src="fa", dest="en").text

    text = user_input.lower()
    response = "🤖 I didn't understand that. Try asking about a crypto or stock."

    if "price" in text:
        words = text.split()
        for word in words:
            price = get_crypto_price(word.lower())
            if price:
                response = f"💰 {word.upper()} price: ${price:.2f}"
                break
    elif "news" in text:
        response = get_news()
    elif "predict" in text:
        words = text.split()
        for word in words:
            prediction = predict_price(word.upper())
            if "Prediction" in prediction:
                response = prediction
                break
    elif any(w in text for w in ["hi", "hello", "salam"]):
        response = "👋 Hi! Ask me about any crypto or stock, or say 'news' or 'predict BTC'."

    if lang == "fa":
        response = translator.translate(response, src="en", dest="fa").text

    await update.message.reply_text(response)

# Bot Setup
if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running...")
    app_bot.run_polling()
