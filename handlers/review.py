from telegram import (
    Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import save_review

# Состояния диалога
ASKING, CONFIRM = range(2)

# Клавиатура подтверждения
_CONFIRM_KB = ReplyKeyboardMarkup(
    [["Да", "Нет"]], resize_keyboard=True, one_time_keyboard=True
)

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

    # все вопросы заданы — показываем сводку и просим подтверждение
    if idx >= len(config.QUESTIONS):
        answers = context.user_data["answers"]
        summary_lines = [
            f"📱 Телефон: {answers.get('phone')}",
            f"🏙️ Город: {answers.get('city')}",
            f"🏘️ ЖК: {answers.get('complex_name')}",
            f"👤 Статус: {answers.get('status')}",
            f"🔥 Отопление: {answers.get('heating')}/5",
            f"⚡ Электро: {answers.get('electricity')}/5",
            f"🛢️ Газ: {answers.get('gas')}/5",
            f"💧 Вода: {answers.get('water')}/5",
            f"🔊 Шум: {answers.get('noise')}/5",
            f"🏢 УК: {answers.get('mgmt')}/5",
            f"💰 Аренда: {answers.get('rent_price')}",
            f"👍 Нравится: {answers.get('likes')}",
            f"👎 Раздражает: {answers.get('annoy')}",
            f"✅ Рекомендация: {answers.get('recommend')}",
        ]
        summary = "\n".join(summary_lines)
        await update.message.reply_text(
            summary + "\n\nПодтверждаете отзыв?", reply_markup=_CONFIRM_KB
        )
        return CONFIRM

    # иначе — задаём очередной вопрос
    q = config.QUESTIONS[idx]

    if q["type"] == "choice":
        markup = ReplyKeyboardMarkup(
            [q["options"]], one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(q["text"], reply_markup=markup)
    else:
        await update.message.reply_text(q["text"])

    return ASKING


# ────────── Принимаем ответ пользователя ──────────
async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]
    q   = config.QUESTIONS[idx]
    text = (update.message.text or "").strip()

    # Валидация
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


# ────────── Обрабатываем подтверждение ──────────
async def _confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()
    if text == "да":
        await save_review(context.user_data["answers"])
        await update.message.reply_text(
            "Спасибо! Отзыв принят ✅", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    elif text == "нет":
        # перезапускаем опрос с нуля
        return await entry_start_review(update, context)
    else:
        await update.message.reply_text("Пожалуйста, нажмите 'Да' или 'Нет'.")
        return CONFIRM


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ────────── ConversationHandler ──────────
review_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("review", entry_start_review),
        MessageHandler(filters.Regex(r"^📝 Оставить отзыв$"), entry_start_review),
    ],
    states={
        ASKING:  [MessageHandler(filters.TEXT & ~filters.COMMAND, _collect_answer)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, _confirm)],
    },
    fallbacks=[CommandHandler("cancel", _cancel)],
)
