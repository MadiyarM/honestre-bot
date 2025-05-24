from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import save_review
from handlers.start import MAIN_MENU

ASKING, CONFIRM = range(2)

_CONFIRM_KB = ReplyKeyboardMarkup(
    [["Да", "Нет"], ["Назад", "Отменить"]], resize_keyboard=True, one_time_keyboard=True
)

# Убираем вопрос о телефоне, если он ещё остался в config
QUESTIONS = [q for q in config.QUESTIONS if q.get("key") != "phone"]

# ────────────────────────────────────────────────────────────────
# Entry
# ────────────────────────────────────────────────────────────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = {"user_id": update.effective_user.id}
    context.user_data["q_idx"] = 0
    await _ask_next_question(update, context)
    return ASKING

# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────

def _build_markup(options, allow_back):
    rows = []
    if options:
        rows.append(options)
    extra = ["Отменить"]
    if allow_back:
        extra.insert(0, "Назад")
    rows.append(extra)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

async def _ask_next_question(update, context):
    idx = context.user_data["q_idx"]
    if idx >= len(QUESTIONS):
        return await _show_summary(update, context)
    q = QUESTIONS[idx]
    markup = _build_markup(q.get("options") if q["type"] == "choice" else None, idx > 0)
    await update.message.reply_text(q["text"], reply_markup=markup)
    return ASKING

async def _show_summary(update, context):
    a = context.user_data["answers"]
    summary = "\n".join([
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

# ────────────────────────────────────────────────────────────────
# Collect / Confirm
# ────────────────────────────────────────────────────────────────
async def _collect_answer(update, context):
    text = (update.message.text or "").strip()
    if text.lower() == "отменить":
        return await _cancel(update, context)

    idx = context.user_data["q_idx"]
    q = QUESTIONS[idx]

    if text.lower() == "назад":
        if idx == 0:
            await update.message.reply_text("Вы уже на первом вопросе.")
            return ASKING
        context.user_data["q_idx"] -= 1
        return await _ask_next_question(update, context)

    # rating / choice / text processing
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

async def _confirm(update, context):
    text = (update.message.text or "").strip().lower()
    if text == "отменить":
        return await _cancel(update, context)
    if text == "назад":
        context.user_data["q_idx"] = len(QUESTIONS) - 1
        return await _ask_next_question(update, context)
    if text == "да":
        a = context.user_data["answers"]
        a["recommend"] = a.get("recommend") == "Да"
        await save_review(a)
        await update.message.reply_text(
            "Спасибо! Отзыв принят ✅\n\nВыберите дальнейшее действие:",
            reply_markup=MAIN_MENU
        )
        return ConversationHandler.END
    if text == "нет":
        await update.message.reply_text(
            "Ок, возвращаюсь в меню. Выберите действие:", reply_markup=MAIN_MENU
        )
        return ConversationHandler.END
    await update.message.reply_text("Пожалуйста, нажмите 'Да', 'Нет', 'Назад' или 'Отменить'.")
    return CONFIRM

# ────────────────────────────────────────────────────────────────
# Cancel
# ────────────────────────────────────────────────────────────────
async def _cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("Операция отменена.", reply_markup=MAIN_MENU)
    return ConversationHandler.END

# ────────────────────────────────────────────────────────────────
# Handler
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
        CommandHandler("start", _cancel),
    ],
)
