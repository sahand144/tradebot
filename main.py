# main.py
import os
import logging
import requests
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Helper: Get Crypto or Stock Price
async def get_price(symbol):
    try:
        if symbol.upper() in ['BTC', 'ETH', 'DOGE']:  # Crypto
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            res = requests.get(url).json()
            price = res[symbol.lower()]['usd']
            return f"💰 {symbol.upper()} Price: ${price}"
        else:  # Stock
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"].iloc[-1]
            return f"📈 {symbol.upper()} Stock Price: ${round(price, 2)}"
    except:
        return f"⚠️ Could not get price for '{symbol}'"

# Helper: Predict Price
async def predict_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="30d")
        if len(hist) < 2:
            return "❌ Not enough data to predict."
        last_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        predicted = last_price + (last_price - prev_price)
        return f"🔮 Estimated tomorrow price for {symbol.upper()}: ${round(predicted, 2)}"
    except:
        return "⚠️ Prediction failed. Invalid symbol?"

# Helper: Free News from Reddit RSS
async def get_news():
    url = "https://www.reddit.com/r/investing/.rss"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return "❌ Could not fetch news."
        items = res.text.split("<title>")[2:7]
        return "🗞 Top Finance News:\n" + "\n\n".join([f"➡️ {i.split('</title>')[0]}" for i in items])
    except:
        return "⚠️ Failed to fetch news."

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! I can show prices, predictions & news.\nExamples:\n- BTC\n- AAPL\n- predict BTC\n- news")

# Command: /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n- BTC, ETH, AAPL etc. for prices\n- predict BTC / AAPL\n- news")

# Natural chat handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith("predict"):
        symbol = text.replace("predict", "").strip()
        msg = await predict_price(symbol)
        await update.message.reply_text(msg)
    elif "news" in text:
        msg = await get_news()
        await update.message.reply_text(msg)
    else:
        symbol = text.strip().upper()
        msg = await get_price(symbol)
        await update.message.reply_text(msg)

# Run bot directly (NO Flask!)
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
