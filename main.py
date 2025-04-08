import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

# Get current price of BTC in USD
def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    data = response.json()
    return data["bitcoin"]["usd"]

# Analyze BTC trend - this is a mock example
def analyze_trend():
    # In real life, you'd check past data
    import random
    return "📈 Uptrend" if random.random() > 0.5 else "📉 Downtrend"

# Recommend action based on price
def generate_recommendation(price):
    if price < 25000:
        return "💡 Suggestion: Price is low, consider buying 🟢"
    elif price > 40000:
        return "💡 Suggestion: Price is high, consider selling 🔴"
    else:
        return "💡 Suggestion: Market is stable, consider holding 🟡"

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /price, /trend, or /recommend")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price()
    await update.message.reply_text(f"🪙 Current BTC Price: ${price:,.2f}")

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price()
    recommendation = generate_recommendation(price)
    await update.message.reply_text(recommendation)

async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trend = analyze_trend()
    await update.message.reply_text(f"📊 Market Trend: {trend}")

# --- Main ---

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("recommend", recommend))
app.add_handler(CommandHandler("trend", trend))

if __name__ == '__main__':
    app.run_polling()
