import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask-заглушка для Timeweb
flask_app = Flask(__name__)
@flask_app.route("/")
def health():
    return "Бот работает"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Бот работает.")

# Telegram-бот
def run_bot():
    try:
        print("BOT_TOKEN:", BOT_TOKEN)
        print("Запуск Telegram-бота...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.run_polling()
    except Exception as e:
        print("Ошибка запуска Telegram-бота:", e)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
