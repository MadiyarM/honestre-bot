from telegram import (
    Update, ReplyKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, MessageHandler, filters
)

# Главное меню: две кнопки ровно как раньше
_MENU = ReplyKeyboardMarkup(
    [["📝 Оставить отзыв", "🔍 Найти ЖК"]],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start → показать меню
    """
    await update.message.reply_text(
        "Здравствуйте! Выберите действие:",
        reply_markup=_MENU
    )


# Этот message‑handler перехватывает клик по кнопкам меню
def menu_choice() -> MessageHandler:
    return MessageHandler(
        filters.Regex(r"^(📝 Оставить отзыв|🔍 Найти ЖК)$"),
        _route
    )


# «Маршрутизация»: выбор ветки разговора
async def _route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if txt.startswith("📝"):
        # Запускаем разговор «отзыв» (импорт ленивый, чтобы избежать циклов)
        from handlers.review import entry_start_review
        await entry_start_review(update, context)
    else:
        from handlers.search import entry_start_search
        await entry_start_search(update, context)
