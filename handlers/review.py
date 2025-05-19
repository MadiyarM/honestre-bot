from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import save_review

ASKING = 0   # единственное состояние


# ────────── Conversation entry ──────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Точка входа как от команды /review, так и от кнопки меню.
    """
    context.user_data.clear()
    context.user_data["answers"] = {}
    context.user_data["q_idx"]  = 0
    await _ask_next_question(update, context)
    return ASKING


# ────────── Логика задавания вопросов ──────────
async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]

    # Все вопросы пройдены → сохраним
    if idx >= len(config.QUESTIONS):
        await save_review(context.user_data["answers"])
        await update.message.reply_text(
            "Спасибо! Ваш отзыв сохранён ✅",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    q = config.QUESTIONS[idx]

    if q["type"] == "choice":
        markup = ReplyKeyboardMarkup(
            [q["options"]], one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(q["text"], reply_markup=markup)
    else:
        await update.message.reply_text(q["text"])

    # Остаёмся в состоянии ASKING
    return ASKING


# ────────── Приём ответа пользователя ──────────
async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]
    q   = config.QUESTIONS[idx]
    text = (update.message.text or "").strip()

    # Валидация «rating»
    if q["type"] == "rating":
        try:
            val = int(text)
            if not 1 <= val <= 5:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Введите число от 1 до 5.")
            return ASKING
        context.user_data["answers"][q["key"]] = val

    # Выбор из вариантов
    elif q["type"] == "choice":
        if text not in q["options"]:
            await update.message.reply_text("Пожалуйста, выберите вариант из клавиатуры.")
            return ASKING
        context.user_data["answers"][q["key"]] = text

    else:  # простой текст
        context.user_data["answers"][q["key"]] = text

    # Переходим к следующему вопросу
    context.user_data["q_idx"] += 1
    return await _ask_next_question(update, context)


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ────────── Public ConversationHandler ──────────
review_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("review", entry_start_review),
        # Кнопка меню ловится отдельным message‑handler'ом в start.py
    ],
    states={
        ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, _collect_answer)]
    },
    fallbacks=[CommandHandler("cancel", _cancel)],
)
