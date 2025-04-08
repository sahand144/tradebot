import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from googletrans import Translator
from flask import Flask
from threading import Thread

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize translator
translator = Translator()

# Flask app for keeping bot alive
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ----- Feature Functions ----- #

# Get price of any crypto or stock (basic public API)
def get_price(query):
    query = query.lower().replace(" ", "-")
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={query}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    if query in data:
        return f"💰 {query.capitalize()} price: ${data[query]['usd']:,}"
    else:
        return "🚫 رمز ارز یا سهم مورد نظر یافت نشد. لطفا دوباره تلاش کنید."

# Get technical analysis - dummy logic for now
def get_analysis(query, strategy):
    query = query.capitalize()
    analysis = f"📊 تحلیل {strategy.upper()} برای {query}:
"
    if strategy.lower() == "rsi":
        analysis += "شاخص RSI در ناحیه اشباع فروش است. احتمال صعودی بودن بازار وجود دارد."
    elif strategy.lower() == "macd":
        analysis += "سیگنال MACD به تازگی کراس کرده است. احتمال بازگشت روند وجود دارد."
    else:
        analysis += "استراتژی تعریف نشده. لطفا RSI یا MACD وارد کنید."
    return analysis

# Get news headlines

def get_news(query):
    if not NEWS_API_KEY:
        return "📰 برای اخبار نیاز به API Key از newsapi.org داریم."
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en"
    response = requests.get(url)
    articles = response.json().get("articles", [])[:3]
    if not articles:
        return "❌ خبری یافت نشد."
    result = f"📰 آخرین اخبار درباره {query}:
"
    for art in articles:
        result += f"🔹 {art['title']}\n🔗 {art['url']}\n\n"
    return result

# Detect Persian and translate

def translate_if_needed(text):
    detected_lang = translator.detect(text).lang
    if detected_lang == 'fa':
        return translator.translate(text, src='fa', dest='en').text, 'fa'
    return text, 'en'

# --- Bot Handlers --- #

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['💹 استعلام قیمت', '📈 تحلیل تکنیکال'], ['🗞️ اخبار', '🔮 پیش‌بینی']]
    await update.message.reply_text(
        "سلام! من دستیار معاملاتی تو هستم. هر چیزی درباره ارز دیجیتال یا بورس بپرس یا از منوی زیر انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    )

# Main Message Handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    translated, lang = translate_if_needed(user_input)

    # Check for menu text
    if "قیمت" in user_input or "price" in translated.lower():
        await update.message.reply_text("نام ارز یا سهم را وارد کن:")
        return
    if "تحلیل" in user_input or "analysis" in translated.lower():
        await update.message.reply_text("نام ارز/سهم و استراتژی مورد نظر را بنویس. مثلا: bitcoin RSI")
        return
    if "خبر" in user_input or "news" in translated.lower():
        await update.message.reply_text("درباره چی میخوای خبر بخونی؟ اسم ارز یا سهم رو بفرست.")
        return
    if "پیش‌بینی" in user_input or "predict" in translated.lower():
        await update.message.reply_text("🔮 در حال توسعه! به زودی میتونی آینده بازار رو هم از من بپرسی!")
        return

    words = translated.split()
    if len(words) == 1:
        price = get_price(words[0])
        await update.message.reply_text(price)
        news = get_news(words[0])
        await update.message.reply_text(news)
    elif len(words) == 2:
        asset, strategy = words
        analysis = get_analysis(asset, strategy)
        await update.message.reply_text(analysis)
    else:
        await update.message.reply_text("❓ لطفا فقط نام ارز/سهم یا استراتژی رو دقیق وارد کن.")

# --- Start Bot --- #
def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    from telegram.ext import ApplicationBuilder
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
