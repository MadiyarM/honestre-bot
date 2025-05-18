# handlers/search.py
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    MessageHandler, filters, ContextTypes, ConversationHandler
)
import db
from handlers.start import start  # для возврата в меню

# Состояние для ConversationHandler
SEARCH_QUERY = 0

# Кнопки "Повторить ввод" и "Назад"
BACK_KB = ReplyKeyboardMarkup(
    [["Повторить ввод"], ["Назад"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Триггер: нажатие кнопки "Узнать отзыв о ЖК".
    Спрашиваем у пользователя название ЖК для поиска.
    """
    await update.message.reply_text(
        "🔍 Введите точное название жилого комплекса:",
        reply_markup=ReplyKeyboardRemove()
    )
    return SEARCH_QUERY

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получаем текст запроса, ищем отзывы в БД и выводим их.
    Поддерживает команды "Повторить ввод" и "Назад".
    """
    text = update.message.text.strip()

    # Пользователь хочет выйти в меню
    if text == "Назад":
        await start(update, context)
        return ConversationHandler.END

    # Повторный ввод
    if text == "Повторить ввод":
        await update.message.reply_text(
            "🔍 Введите точное название жилого комплекса:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SEARCH_QUERY

    # Обычный поиск
    reviews = db.get_reviews_by_complex(text)
    if not reviews:
        await update.message.reply_text(
            f"❌ Отзывов по ЖК '{text}' не найдено."
        )
        await update.message.reply_text(
            "Попробовать снова или вернуться в меню:",
            reply_markup=BACK_KB
        )
        return SEARCH_QUERY

    # Если найдено - выводим результаты
    for r in reviews:
        name = r.get('complex_name', '—')
        city = r.get('city', '—')
        await update.message.reply_text(f"🏢 ЖК {name}, {city}")

        # Ключевые показатели
        labels = {
            'water': '💧 Водоснабжение',
            'electricity': '⚡️ Электроснабжение',
            'gas': '🔥 Газоснабжение',
            'noise': '🔊 Шум',
            'heating': '🔥 Отопление',
            'mgmt': '🏢 УК (застройщик)'
        }
        keys = list(labels.keys())
        lines = ["🔑 Ключевые показатели"]
        total = 0
        for key in keys:
            raw = r.get(key, 0)
            try:
                val = int(raw)
            except (TypeError, ValueError):
                val = 0
            stars = '★' * val + '☆' * (5 - val)
            line_label = labels[key]
            lines.append(f"• {line_label}: {stars} ({val}/5)")
            total += val
        avg = total / len(keys) if keys else 0
        lines.append(f"\nВывод: {avg:.1f}")

        await update.message.reply_text("\n".join(lines))

    # После вывода возвращаемся в меню
    await start(update, context)
    return ConversationHandler.END

# ConversationHandler для поиска отзывов
search_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r'^Узнать отзыв о ЖК$'), start_search)
    ],
    states={
        SEARCH_QUERY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)
        ]
    },
    fallbacks=[
        MessageHandler(filters.Regex(r'^Назад$'), handle_search_query)
    ]
)