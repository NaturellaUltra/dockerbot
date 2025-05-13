import logging
import sqlite3
import datetime
import os
from dotenv import load_dotenv

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from openpyxl import Workbook
from io import BytesIO

# Flask-заглушка
from flask import Flask
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Бот работает."

# Загрузка токена
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.run_polling()

if __name__ == "__main__":
    main()
