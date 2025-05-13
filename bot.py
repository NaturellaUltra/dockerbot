import os
import threading
import sqlite3
import datetime
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from openpyxl import Workbook
from io import BytesIO

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

REGISTER_NAME, REGISTER_DEPARTMENT, WAIT_REASON = range(3)
ADMIN_IDS = {717329852, 653756588}
DEPARTMENTS = [
    "Управление по выявлению административных правонарушений",
    "Отдел центральных районов",
    "Отдел северных районов",
    "Отдел южных районов",
    "Отдел правобережных районов",
    "Отдел координации"
]

departments_keyboard = [[KeyboardButton(dept)] for dept in DEPARTMENTS]
main_button = [[KeyboardButton("🚪 Сообщить об убытии с рабочего места")]]
admin_button = [[KeyboardButton("📊 Получить отчёт")]]

conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, full_name TEXT, department TEXT, is_admin INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS departures (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, reason TEXT, timestamp DATETIME)")
conn.commit()

def is_registered(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        is_admin = cursor.fetchone()[0]
        keyboard = main_button.copy()
        if is_admin:
            keyboard += admin_button
        await update.message.reply_text("✅ Вы уже зарегистрированы.", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return ConversationHandler.END
    await update.message.reply_text("👋 Здравствуйте! Пожалуйста, введите ваше полное ФИО (например: Иванов Сергей Петрович):")
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name.split()) < 3:
        await update.message.reply_text("⚠️ Пожалуйста, укажите ФИО полностью (Фамилия Имя Отчество).")
        return REGISTER_NAME
    context.user_data["full_name"] = name
    await update.message.reply_text("✅ Теперь выберите ваш отдел:", reply_markup=ReplyKeyboardMarkup(departments_keyboard, resize_keyboard=True))
    return REGISTER_DEPARTMENT

async def register_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    department = update.message.text
    user_id = update.effective_user.id
    full_name = context.user_data["full_name"]
    is_admin = 1 if user_id in ADMIN_IDS else 0
    cursor.execute("INSERT OR REPLACE INTO users (user_id, full_name, department, is_admin) VALUES (?, ?, ?, ?)", (user_id, full_name, department, is_admin))
    conn.commit()
    keyboard = main_button.copy()
    if is_admin:
        keyboard += admin_button
    await update.message.reply_text("🎉 Регистрация завершена.", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ConversationHandler.END

async def handle_departure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("⚠️ Сначала необходимо пройти регистрацию. Напишите /start.")
        return ConversationHandler.END
    await update.message.reply_text("✏️ Напишите, куда вы уходите и во сколько планируете вернуться (например: «в МФЦ, вернусь в 14:30»):")
    return WAIT_REASON

async def save_departure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    if now.weekday() >= 5 or not (9 <= now.hour < 18):
        await update.message.reply_text("⏰ Вне рабочего времени — бот завершает работу.")
        return ConversationHandler.END
    user_id = update.effective_user.id
    reason = update.message.text
    timestamp = datetime.datetime.now()
    cursor.execute("INSERT INTO departures (user_id, reason, timestamp) VALUES (?, ?, ?)", (user_id, reason, timestamp))
    conn.commit()
    cursor.execute("SELECT full_name, department FROM users WHERE user_id = ?", (user_id,))
    full_name, department = cursor.fetchone()
    with open("departures_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp.strftime('%Y-%m-%d %H:%M')}] {full_name} | {department} | {reason}\n")
    await update.message.reply_text("✅ Информация сохранена и передана руководству Управления.")
    return ConversationHandler.END

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Неизвестная команда. Пожалуйста, используйте кнопки.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM departures WHERE user_id = ?", (user_id,))
    conn.commit()
    await update.message.reply_text("🔁 Регистрация сброшена. Напишите /start для новой регистрации.")

# Flask-заглушка для Timeweb
flask_app = Flask(__name__)
@flask_app.route("/")
def health():
    return "Бот работает"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

def run_bot():
    try:
        print("BOT_TOKEN:", BOT_TOKEN)
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex("🚪 Сообщить об убытии с рабочего места"), handle_departure)
            ],
            states={
                REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
                REGISTER_DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_department)],
                WAIT_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_departure)],
            },
            fallbacks=[],
            allow_reentry=True
        )
        app.add_handler(conv_handler)
        app.add_handler(CommandHandler("reset", reset))
        app.add_handler(MessageHandler(filters.ALL, unknown))
        app.run_polling()
    except Exception as e:
        print("Ошибка запуска бота:", e)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
