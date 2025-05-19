from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

# Главное меню, которое показываем пользователю
MAIN_MENU = ReplyKeyboardMarkup(
    [['📝 Оставить отзыв', '🔍 Найти ЖК']],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — просто выводим приветствие и клавиатуру"""
    await update.message.reply_text(
        'Здравствуйте! Выберите действие:',
        reply_markup=MAIN_MENU
    )


# ────────────────────────── Внутренняя маршрутизация ──────────────────────────
async def _route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вызывается при клике на одну из двух кнопок меню"""
    text = update.message.text or ''

    if text.startswith('📝'):
        # Ленивая импорт‑цепочка, чтобы избежать циклов
        from handlers.review import entry_start_review
        await entry_start_review(update, context)

    elif text.startswith('🔍'):
        from handlers.search import entry_start_search
        await entry_start_search(update, context)


def menu_handler() -> MessageHandler:
    """Возвращает готовый MessageHandler для регистрации в Application"""
    return MessageHandler(
        filters.Regex(r'^(📝 Оставить отзыв|🔍 Найти ЖК)$'),
        _route
    )
