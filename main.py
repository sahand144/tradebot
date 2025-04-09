import os
import logging
from datetime import datetime, timedelta
from threading import Thread

import yfinance as yf
import numpy as np
import torch
import torch.nn as nn
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters, CallbackQueryHandler)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Flask
app = Flask(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram Menu Buttons
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Get Price", callback_data='price')],
        [InlineKeyboardButton("🔮 Predict Price (AI)", callback_data='predict')],
        [InlineKeyboardButton("📊 Market Trends", callback_data='trends')],
        [InlineKeyboardButton("🤖 AI Buy/Sell Suggestions", callback_data='ai_trade')],
        [InlineKeyboardButton("📜 Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

# LSTM Model
def create_lstm_model(input_size=1, hidden_size=50, num_layers=2):
    class LSTMModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])
    return LSTMModel()

async def train_and_predict_lstm(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="60d")['Close'].values
    if len(hist) < 10:
        return "❌ Not enough data to predict."

    seq_len = 10
    X, y = [], []
    for i in range(len(hist) - seq_len):
        X.append(hist[i:i+seq_len])
        y.append(hist[i+seq_len])

    X, y = np.array(X), np.array(y)
    X = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)
    y = torch.tensor(y, dtype=torch.float32)

    model = create_lstm_model()
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(20):
        optimizer.zero_grad()
        out = model(X)
        loss = loss_fn(out.squeeze(), y)
        loss.backward()
        optimizer.step()

    last_seq = torch.tensor(hist[-seq_len:], dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
    model.eval()
    pred = model(last_seq).item()
    return f"🔮 Predicted next price for {symbol.upper()}: ${round(pred, 2)}"

# Price API
async def get_price(symbol):
    try:
        if symbol.upper() in ['BTC', 'ETH', 'DOGE']:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            res = requests.get(url).json()
            return f"💰 {symbol.upper()} Price: ${res[symbol.lower()]['usd']}"
        else:
            price = yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
            return f"📈 {symbol.upper()} Stock Price: ${round(price, 2)}"
    except:
        return "❌ Could not fetch price."

# AI Trade Suggestion
async def ai_trade_suggestion(symbol):
    try:
        hist = yf.Ticker(symbol).history(period="15d")['Close']
        change = hist.pct_change().mean()
        if change > 0.01:
            return f"📈 {symbol.upper()}: Suggestion ➡️ BUY (upward trend)"
        elif change < -0.01:
            return f"📉 {symbol.upper()}: Suggestion ➡️ SELL (downward trend)"
        else:
            return f"➖ {symbol.upper()}: Suggestion ➡️ HOLD (neutral trend)"
    except:
        return "❌ Could not analyze trend."

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to AI Trading Bot!", reply_markup=get_main_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a symbol (like BTC, AAPL) or use the menu.")

# Callback Handler for Menu
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'price':
        await query.edit_message_text("💬 Send the symbol you want to get price for.")
        context.user_data['mode'] = 'price'
    elif action == 'predict':
        await query.edit_message_text("💬 Send the symbol for price prediction (AI powered).")
        context.user_data['mode'] = 'predict'
    elif action == 'trends':
        await query.edit_message_text("💬 Send the symbol for market trend analysis.")
        context.user_data['mode'] = 'trend'
    elif action == 'ai_trade':
        await query.edit_message_text("💬 Send the symbol for AI Buy/Sell Suggestion.")
        context.user_data['mode'] = 'ai_trade'
    elif action == 'help':
        await query.edit_message_text("Send a symbol (like BTC, AAPL) or use the menu.")

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    mode = context.user_data.get('mode', '')

    if mode == 'price':
        msg = await get_price(text)
    elif mode == 'predict':
        msg = await train_and_predict_lstm(text)
    elif mode == 'trend':
        msg = await ai_trade_suggestion(text)
    elif mode == 'ai_trade':
        msg = await ai_trade_suggestion(text)
    else:
        msg = "❓ Please select an option from the menu using /start."

    await update.message.reply_text(msg)

# Flask Route
@app.route('/')
def index():
    return 'Bot is running!'

# Run Bot + Flask
if __name__ == '__main__':
    async def main():
        app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
        app_bot.add_handler(CommandHandler("start", start))
        app_bot.add_handler(CommandHandler("help", help_cmd))
        app_bot.add_handler(CallbackQueryHandler(menu_handler))
        app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await app_bot.run_polling()

    def run_bot():
        import asyncio
        asyncio.run(main())

    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=8080)
