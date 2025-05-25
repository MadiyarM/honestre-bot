from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
import config
from db import async_session, save_review
from handlers.start import MAIN_MENU
from models import Review

# ────────── Состояния ──────────
ASKING, CONFIRM = range(2)

# Лимит 2 отзыва за 5 минут (для теста)
WINDOW_SECONDS = 86400
MAX_REVIEWS_PER_WINDOW = 2

# Клавиатура подтверждения
_CONFIRM_KB = ReplyKeyboardMarkup(
    [["Да", "Нет"], ["Назад", "Отменить"]], resize_keyboard=True, one_time_keyboard=True
)

# Удаляем устаревший вопрос о телефоне
QUESTIONS = [q for q in config.QUESTIONS if q.get("key") != "phone"]

# ───────────────── Entry ─────────────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = {"user_id": update.effective_user.id}
    context.user_data["q_idx"] = 0
    await _ask_next_question(update, context)
    return ASKING

# ───────────────── Helpers ─────────────────

def _build_markup(options: list[str] | None, allow_back: bool) -> ReplyKeyboardMarkup:
    rows: list[list[str]] = []
    if options:
        rows.append(options)
    extra = ["Отменить"]
    if allow_back:
        extra.insert(0, "Назад")
    rows.append(extra)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]
    if idx >= len(QUESTIONS):
        return await _show_summary(update, context)

    q = QUESTIONS[idx]
    base_opts = q.get("options") if q["type"] == "choice" else None

    # добавляем кнопку «Отсутствует» для вопроса о газе
    if q.get("key") == "gas":
        opts = (base_opts or []) + ["Отсутствует"]
    else:
        opts = base_opts

    markup = _build_markup(opts, idx > 0)
    await update.message.reply_text(q["text"], reply_markup=markup)
    return ASKING

async def _show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a = context.user_data["answers"]
    gas_val = "Отсутствует" if a.get("gas") is None else f"{a.get('gas')}/5"
    summary = "\n".join([
        f"🏙️ Город: {a.get('city')}",
        f"🏘️ ЖК: {a.get('complex_name')}",
        f"👤 Статус: {a.get('status')}",
        f"🔥 Отопление: {a.get('heating')}/5",
        f"⚡ Электро: {a.get('electricity')}/5",
        f"🛢️ Газ: {gas_val}",
        f"💧 Вода: {a.get('water')}/5",
        f"🔊 Шум: {a.get('noise')}/5",
        f"🏢 УК: {a.get('mgmt')}/5",
        f"💰 Аренда: {a.get('rent_price')}",
        f"👍 {a.get('likes')}",
        f"👎 {a.get('annoy')}",
        f"✅ Рекомендация: {'Да' if a.get('recommend') else 'Нет'}",
    ])
    await update.message.reply_text(summary + "\n\nПодтверждаете отзыв?", reply_markup=_CONFIRM_KB)
    return CONFIRM

# ───────────────── Collect ─────────────────
async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text.lower() == "отменить":
        return await _cancel(update, context)

    idx = context.user_data["q_idx"]
    q = QUESTIONS[idx]

    # Назад
    if text.lower() == "назад":
        if idx == 0:
            await update.message.reply_text("Вы уже на первом вопросе.")
            return ASKING
        context.user_data["q_idx"] -= 1
        return await _ask_next_question(update, context)

    # rating / choice / text
    if q["type"] == "rating":
        if q.get("key") == "gas" and text.lower() == "отсутствует":
            context.user_data["answers"]["gas"] = None
        else:
            try:
                val = int(text)
                if not 1 <= val <= 5:
                    raise ValueError
            except ValueError:
                await update.message.reply_text("Введите число от 1 до 5 или нажмите 'Отсутствует'.")
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

# ───────────────── Confirm / Save ─────────────────
async def _confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()

    if text == "отменить":
        return await _cancel(update, context)
    if text == "назад":
        context.user_data["q_idx"] = len(QUESTIONS) - 1
        return await _ask_next_question(update, context)

    if text == "да":
        answers = context.user_data["answers"]
        answers["recommend"] = answers.get("recommend") == "Да"

        # ---- rate‑limit ----
        window_start = datetime.utcnow() - timedelta(seconds=WINDOW_SECONDS)
        async with async_session() as session:
            from sqlalchemy import select, func
            stmt = (
                select(func.count())
                .select_from(Review)
                .where(Review.user_id == answers["user_id"], Review.created_at >= window_start)
            )
            count = (await session.execute(stmt)).scalar() or 0
        if count >= MAX_REVIEWS_PER_WINDOW:
            await update.message.reply_text(
                "❗ Вы уже оставили 2 отзыва за последние 5 минут. Попробуйте позже.",
                reply_markup=MAIN_MENU
            )
            return ConversationHandler.END

        # ---- save ----
        await save_review(answers)
        await update.message.reply_text(
            "Спасибо! Отзыв принят ✅\n\nВыберите дальнейшее действие:",
            reply_markup=MAIN_MENU
        )
        return ConversationHandler.END

    if text == "нет":
        await update.message.reply_text("Ок, возвращаюсь в меню. Выберите действие:", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await update.message.reply_text("Пожалуйста, нажмите 'Да', 'Нет', 'Назад' или 'Отменить'.")
    return CONFIRM

# ───────────────── Cancel ─────────────────
async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Операция отменена.", reply_markup=MAIN_MENU)
    return ConversationHandler.END

# ───────────────── Handler ─────────────────
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
