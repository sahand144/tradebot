# main.py
import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests
import yfinance as yf
from datetime import datetime

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
    try:
        if symbol.upper() in ['BTC', 'ETH', 'DOGE']:  # Crypto symbols
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            res = requests.get(url).json()
            return f"💰 {symbol.upper()} Price: ${res[symbol.lower()]['usd']}"
        else:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"].iloc[-1]
            return f"📈 {symbol.upper()} Stock Price: ${round(price, 2)}"
    except:
        return "⚠️ Could not fetch the price. Please check the symbol."

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

# Helper: Get Free News from Coingecko
async def get_news():
    try:
        url = "https://api.coingecko.com/api/v3/status_updates"
        res = requests.get(url).json()
        updates = res.get("status_updates", [])[:5]
        if not updates:
            return "❌ No news available."
        return "🗞 Latest Crypto/Stock News:\n" + "\n\n".join([f"➡️ {u['project']['name']}: {u['description']}" for u in updates if u.get("project")])
    except:
        return "⚠️ Failed to fetch news."

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to AI MarketBot!\nI can give you prices, predictions, and news.\n\nTry typing:\n- BTC\n- AAPL\n- Predict BTC\n- News"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Help Menu:\n\nCommands you can try:\n- AAPL or BTC (for prices)\n- Predict AAPL or Predict BTC (for future price)\n- News (latest headlines)\nJust talk to me like a real person, no need for special commands!"
    )

# Chat Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith("predict"):
        symbol = text.split("predict")[-1].strip()
        msg = await predict_price(symbol)
        await update.message.reply_text(msg)
    elif "news" in text:
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
    from threading import Thread

    async def main():
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await application.run_polling()

    def telegram_bot():
        import asyncio
        asyncio.run(main())

    Thread(target=telegram_bot).start()
    app.run(host='0.0.0.0', port=8080)
