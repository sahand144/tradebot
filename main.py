# main.py
import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests
import yfinance as yf
from datetime import datetime, timedelta

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# App
app = Flask(__name__)

# Helper: Get Price
async def get_price(symbol):
    if symbol.upper() in ['BTC', 'ETH', 'DOGE']:  # Crypto symbols
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
        res = requests.get(url).json()
        return f"💰 {symbol.upper()} Price: ${res[symbol.lower()]['usd']}"
    else:
        stock = yf.Ticker(symbol)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return f"📈 {symbol.upper()} Stock Price: ${round(price, 2)}"

# Helper: Predict Future Price
async def predict_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="30d")
        if len(hist) < 2:
            return "Not enough data to predict."
        last_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        predicted = last_price + (last_price - prev_price)
        return f"🔮 Tomorrow's estimated price of {symbol.upper()}: ${round(predicted, 2)}"
    except:
        return "Prediction failed. Check the symbol."

# Helper: Get News (fallback without API key)
async def get_news():
    try:
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        res = requests.get(url)
        if res.status_code != 200:
            return "❌ No news available."
        import xml.etree.ElementTree as ET
        root = ET.fromstring(res.content)
        items = root.findall(".//item")[:5]
        return "🗞 Top Business News:\n" + "\n\n".join([f"➡️ {item.find('title').text}\n{item.find('link').text}" for item in items])
    except:
        return "❌ Unable to fetch news."

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! I can give you prices, predictions, and news. Just type anything like:\n- BTC\n- AAPL\n- Predict BTC\n- News")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n- Get price: BTC, ETH, AAPL, etc.\n- Predict: Predict BTC, Predict AAPL\n- News: Get latest financial news\nMore coming soon!")

# Chat Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith("predict"):
        symbol = text.split("predict")[-1].strip()
        msg = await predict_price(symbol)
        await update.message.reply_text(msg)
    elif text.startswith("news"):
        msg = await get_news()
        await update.message.reply_text(msg)
    else:
        symbol = text.strip().upper()
        msg = await get_price(symbol)
        await update.message.reply_text(msg)

# Flask route to keep bot alive
@app.route("/")
def index():
    return "Bot is running!"

# Main Bot Function
if __name__ == '__main__':
    import asyncio
    import threading

    async def main():
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await application.initialize()
        await application.start()
        print("Bot polling...")
        await application.updater.start_polling()

    def run_telegram():
        asyncio.run(main())

    thread = threading.Thread(target=run_telegram, daemon=True)
    thread.start()

    app.run(host='0.0.0.0', port=8080)
