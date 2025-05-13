import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram-бот
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print("Бот запущен")
    app.run_polling()

# Flask-заглушка для Timeweb
flask_app = Flask(__name__)
@flask_app.route("/")
def health():
    return "Бот работает"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# Параллельный запуск
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
