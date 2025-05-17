from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from handlers.review import start_review  # <-- импортируем


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Узнать отзыв о ЖК"],
        ["Оставить отзыв"],
        ["Сравнить"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Выбери действие:", reply_markup=reply_markup)

# меню
async def menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Узнать отзыв о ЖК":
        return

    elif text == "Оставить отзыв":
        # вместо обращению к context.bot
        return await start_review(update, context)

    elif text == "Сравнить":
        await update.message.reply_text("⚖️ Подготавливаю сравнение...")
        # TODO: здесь вызов сравнения

    else:
        await update.message.reply_text("❓ Пожалуйста, выберите одну из опций.")

# Регистрируем хендлеры
start = CommandHandler("start", start)
menu_choice = MessageHandler(
    filters.Regex('^(Узнать отзыв о ЖК|Оставить отзыв|Сравнить)$'),
    menu_choice
)