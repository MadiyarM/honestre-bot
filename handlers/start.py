from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# Главное меню, отображаемое по /start
MAIN_MENU = ReplyKeyboardMarkup(
    [["📝 Оставить отзыв", "🔍 Найти ЖК"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветственное сообщение и клавиатура с вариантами действий."""
    await update.message.reply_text(
        "Здравствуйте! Выберите действие:",
        reply_markup=MAIN_MENU
    )
