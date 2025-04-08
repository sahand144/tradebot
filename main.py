import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

# --- Keep-Alive for Render pinging ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Telegram Bot Logic ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = os.getenv("7562519127:AAH5hfhf4kQKt2FMGGNSYArCYMAX1ihDHLs")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I’m your Trading Assistant Bot.\nSend /help to learn what I can do.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 I will soon help you with trading signals and insights.\nTry /suggest for a mock crypto suggestion.")

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🪙 Suggestion: Buy Bitcoin (BTC) - trend looks bullish 📈")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("suggest", suggest))

    app.run_polling()
