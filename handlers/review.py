import re
from telegram import (
    Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import save_review
from handlers.start import MAIN_MENU, start as cmd_start

# ────────── Константы ──────────
ASKING, CONFIRM = range(2)

_CONFIRM_KB = ReplyKeyboardMarkup(
    [["Да", "Нет", "Назад"]], resize_keyboard=True, one_time_keyboard=True
)

_VALID_CODES = {
    "700","701","702","703","704","705","706","707","708","709",
    "747","750","751","760","761","762","763","764",
    "771","775","776","777","778","727",
}

# ────────────────────────────────────────────────────────────────
# Entry
# ────────────────────────────────────────────────────────────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = {}
    context.user_data["q_idx"] = 0
    await _ask_next_question(update, context)
    return ASKING

# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────

def _build_markup(options: list[str] | None, allow_back: bool) -> ReplyKeyboardMarkup | None:
    rows: list[list[str]] = []
    if options:
        rows.append(options)
    if allow_back:
        rows.append(["Назад"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True) if rows else None

# ────────────────────────────────────────────────────────────────
# Ask / answer core
# ────────────────────────────────────────────────────────────────
async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]

    if idx >= len(config.QUESTIONS):
        a = context.user_data["answers"]
        summary = "\n".join([
            f"📱 Телефон: {a.get('phone')}",
            f"🏙️ Город: {a.get('city')}",
            f"🏘️ ЖК: {a.get('complex_name')}",
            f"👤 Статус: {a.get('status')}",
            f"🔥 Отопление: {a.get('heating')}/5",
            f"⚡ Электро: {a.get('electricity')}/5",
            f"🛢️ Газ: {a.get('gas')}/5",
            f"💧 Вода: {a.get('water')}/5",
            f"🔊 Шум: {a.get('noise')}/5",
            f"🏢 УК: {a.get('mgmt')}/5",
            f"💰 Аренда: {a.get('rent_price')}",
            f"👍 Нравится: {a.get('likes')}",
            f"👎 Раздражает: {a.get('annoy')}",
            f"✅ Рекомендация: {'Да' if a.get('recommend') else 'Нет'}",
        ])
        await update.message.reply_text(summary + "\n\nПодтверждаете отзыв?", reply_markup=_CONFIRM_KB)
        return CONFIRM

    q = config.QUESTIONS[idx]
    allow_back = idx > 0
    markup = _build_markup(q.get("options") if q["type"] == "choice" else None, allow_back)
    await update.message.reply_text(q["text"], reply_markup=markup)
    return ASKING

async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    idx = context.user_data.get("q_idx", 0)
    q   = config.QUESTIONS[idx]

    # ------ Назад ------
    if text.lower() == "назад":
        if idx == 0:
            await update.message.reply_text("Вы уже на первом вопросе.")
            return ASKING
        context.user_data["q_idx"] -= 1
        return await _ask_next_question(update, context)

    # ------ Валидация телефона ------
    if q["key"] == "phone":
        ok, err = _validate_phone(text)
        if not ok:
            await update.message.reply_text(err)
            return ASKING
        context.user_data["answers"][q["key"]] = text

    # ------ Рейтинг ------
    elif q["type"] == "rating":
        try:
            val = int(text)
            if not 1 <= val <= 5:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Введите число от 1 до 5.")
            return ASKING
        context.user_data["answers"][q["key"]] = val

    # ------ Choice ------
    elif q["type"] == "choice":
        if text not in q["options"]:
            await update.message.reply_text("Пожалуйста, выберите вариант из клавиатуры.")
            return ASKING
        context.user_data["answers"][q["key"]] = text

    # ------ Plain text ------
    else:
        context.user_data["answers"][q["key"]] = text

    context.user_data["q_idx"] += 1
    return await _ask_next_question(update, context)

# ────────────────────────────────────────────────────────────────
# Validation helpers
# ────────────────────────────────────────────────────────────────

def _validate_phone(num: str):
    if num.startswith("+7") and len(num) == 12 and num[1:].isdigit():
        code = num[2:5]
    elif num.startswith("8") and len(num) == 11 and num.isdigit():
        code = num[1:4]
    else:
        return False, "❗️ Неверный формат. Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
    if code not in _VALID_CODES:
        return False, "❗️ Неверный формат. Введите действительный номер"
    return True, None

# ────────────────────────────────────────────────────────────────
# Confirm
# ────────────────────────────────────────────────────────────────
async def _confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()

    if text == "назад":
        context.user_data["q_idx"] = len(config.QUESTIONS) - 1
        return await _ask_next_question(update, context)

    if text == "да":
        answers = context.user_data["answers"]
        answers["recommend"] = answers.get("recommend") == "Да"
        await save_review(answers)
        await update.message.reply_text("Спасибо! Отзыв принят ✅", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    if text == "нет":
        await update.message.reply_text("Ок, возвращаюсь в меню. Выберите действие:", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await update.message.reply_text("Пожалуйста, нажмите 'Да', 'Нет' или 'Назад'.")
    return CONFIRM

# ────────────────────────────────────────────────────────────────
# Fallbacks
# ────────────────────────────────────────────────────────────────
async def _restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await cmd_start(update, context)
    return ConversationHandler.END

async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ────────────────────────────────────────────────────────────────
# ConversationHandler
# ────────────────────────────────────────────────────────────────
review_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("review", entry_start_review),
        MessageHandler(filters.Regex(r"^📝 Оставить отзыв$"), entry_start_review),
    ],
    states={
        ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, _collect_answer)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, _confirm)],
    },
    fallbacks=[
        CommandHandler("cancel", _cancel),
        CommandHandler("start", _restart),
    ],
)