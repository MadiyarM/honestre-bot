from telegram import (
    Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import save_review

ASKING = 0  # единственное состояние диалога


# ────────── Точка входа ──────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = {}
    context.user_data["q_idx"] = 0
    await _ask_next_question(update, context)
    return ASKING


# ────────── Задаём вопросы по очереди ──────────
async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]

    # все вопросы заданы — сохраняем
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

    return ASKING


# ────────── Принимаем ответ ──────────
async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]
    q   = config.QUESTIONS[idx]
    text = (update.message.text or "").strip()

    if q["type"] == "rating":
        try:
            val = int(text)
            if not 1 <= val <= 5:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Введите число от 1 до 5.")
            return ASKING
        context.user_data["answers"][q["key"]] = val

    elif q["type"] == "choice":
        if text not in q["options"]:
            await update.message.reply_text("Пожалуйста, выберите вариант из клавиатуры.")
            return ASKING
        context.user_data["answers"][q["key"]] = text

    else:
        context.user_data["answers"][q["key"]] = text

    context.user_data["q_idx"] += 1
    return await _ask_next_question(update, context)


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ────────── ConversationHandler ──────────
review_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("review", entry_start_review),
        MessageHandler(filters.Regex(r"^📝 Оставить отзыв$"), entry_start_review),
    ],
    states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, _collect_answer)]},
    fallbacks=[CommandHandler("cancel", _cancel)],
)
