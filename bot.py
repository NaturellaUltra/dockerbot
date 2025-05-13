import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram-бот с диагностикой
def run_bot():
    try:
        print("BOT_TOKEN:", BOT_TOKEN)
        print("Запуск Telegram-бота...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.run_polling()
    except Exception as e:
        print("Ошибка запуска Telegram-бота:", e)

# Flask-заглушка для Timeweb
flask_app = Flask(__name__)
@flask_app.route("/")
def health():
    return "Бот работает"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
