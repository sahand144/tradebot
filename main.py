# main.py

import os
import logging
import asyncio
import requests
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# Logging
logging.basicConfig(level=logging.INFO)

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask App (keep alive on Railway)
app = Flask(__name__)

@app.route('/')
def index():
    return "🚀 Telegram AI Trading Bot is running!"

# 🔹 LSTM Prediction
async def lstm_predict(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d")
        if len(df) < 30:
            return "⚠️ Not enough data to predict."
        
        scaler = MinMaxScaler()
        data = scaler.fit_transform(df["Close"].values.reshape(-1, 1))

        x, y = [], []
        for i in range(30, len(data)):
            x.append(data[i-30:i])
            y.append(data[i])

        x, y = np.array(x), np.array(y)
        x = x.reshape(x.shape[0], x.shape[1], 1)

        model = Sequential()
        model.add(LSTM(50, return_sequences=False, input_shape=(30, 1)))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')
        model.fit(x, y, epochs=5, batch_size=1, verbose=0)

        last_30 = data[-30:]
        future = model.predict(last_30.reshape(1, 30, 1))[0][0]
        predicted_price = scaler.inverse_transform([[future]])[0][0]
        return f"🔮 LSTM Predicted Price for {symbol.upper()}: ${round(predicted_price, 2)}"

    except Exception as e:
        return f"❌ LSTM Prediction Error: {e}"

# 🔹 Price Fetch
async def get_price(symbol):
    try:
        if symbol.upper() in ['BTC', 'ETH', 'DOGE']:
            res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd").json()
            price = res[symbol.lower()]['usd']
            return f"💰 {symbol.upper()} Price: ${price}"
        else:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"].iloc[-1]
            return f"📈 {symbol.upper()} Stock Price: ${round(price, 2)}"
    except:
        return "⚠️ Could not fetch price."

# 🔹 Market Trend
async def market_trend(symbol):
    try:
        df = yf.download(symbol, period="7d", interval="1d")
        if len(df) < 2:
            return "⚠️ Not enough data for trend."
        change = df["Close"].iloc[-1] - df["Close"].iloc[0]
        if change > 0:
            return f"📊 Market Trend for {symbol.upper()}: 📈 UP (${round(change, 2)} gain)"
        else:
            return f"📉 Market Trend for {symbol.upper()}: DOWN (${round(change, 2)} loss)"
    except:
        return "❌ Trend analysis failed."

# 🔹 AI Suggestion
async def ai_suggest(symbol):
    try:
        df = yf.download(symbol, period="10d")
        close = df["Close"]
        if close.iloc[-1] > close.mean():
            return f"✅ AI Suggestion: Consider Buying {symbol.upper()}"
        else:
            return f"❌ AI Suggestion: Avoid Buying {symbol.upper()} for now"
    except:
        return "❌ Suggestion failed."

# 🔹 Start Menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [KeyboardButton("💰 Price"), KeyboardButton("🔮 Predict")],
        [KeyboardButton("📊 Trend"), KeyboardButton("🧠 AI Suggest")],
        [KeyboardButton("ℹ️ Help")]
    ]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome to AI Trading Bot!\nChoose an option below:", reply_markup=markup)

# 🔹 Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = ("📘 Commands:\n"
           "- 💰 Price: Enter a symbol (e.g., BTC, AAPL)\n"
           "- 🔮 Predict: Trains LSTM model and forecasts next price\n"
           "- 📊 Trend: Analyzes last 7 days\n"
           "- 🧠 AI Suggest: Simple buy/sell idea")
    await update.message.reply_text(msg)

# 🔹 Handle Messages
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    if text == "💰 price":
        await update.message.reply_text("Send the symbol (e.g., BTC, AAPL):")
        return
    elif text == "🔮 predict":
        await update.message.reply_text("Send symbol to train LSTM and predict:")
        return
    elif text == "📊 trend":
        await update.message.reply_text("Send symbol to check trend:")
        return
    elif text == "🧠 ai suggest":
        await update.message.reply_text("Send symbol for AI recommendation:")
        return
    elif text == "ℹ️ help":
        await help_command(update, context)
        return

    # Handle user input symbols dynamically
    if len(text) <= 6:
        price = await get_price(text.upper())
        trend = await market_trend(text.upper())
        prediction = await lstm_predict(text.upper())
        suggestion = await ai_suggest(text.upper())
        msg = f"{price}\n\n{trend}\n\n{prediction}\n\n{suggestion}"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❓ Invalid input. Type /start to choose again.")

# 🔹 Main
async def main():
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    await bot.run_polling()

# 🔹 Start Everything
if __name__ == "__main__":
    asyncio.run(main())
