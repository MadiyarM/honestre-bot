"""search.py — расширенный поиск ЖК с тайпо-устойчивостью

Алгоритм поиска:
1. Нормализуем ввод (убираем «ЖК», пунктуацию, лишние пробелы, переводим в lower).
2. Формируем список вариантов запроса: оригинал, нормализованный, «жк + нормализованный».
3. Для каждого варианта делаем trigram‑поиск (`pg_trgm`) с порогом 0.7.
4. Склеиваем результаты, убирая дубликаты.
5. Выводим карточки отзывов, где газ = 0/None → «Отсутствует».
"""

from __future__ import annotations

import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from db import get_reviews_by_complex_pg
from handlers.start import MAIN_MENU

# --------- Conversation states
ASK_COMPLEX = 0

# --------- Keyboards
CANCEL_KB = ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True, one_time_keyboard=True)

# --------- Helpers
def _normalize(text: str) -> str:
    """Удалить «жк», пунктуацию, привести к lower, сжать пробелы."""
    txt = re.sub(r"\bжк\b", "", text, flags=re.I)
    txt = re.sub(r"[.,!?;:\-]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip().lower()
    return txt

async def entry_start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите название ЖК для поиска (минимум 3 символа):",
        reply_markup=CANCEL_KB,
    )
    return ASK_COMPLEX

async def _show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_query: str = update.message.text.strip()

    # Отмена
    if raw_query.lower() == "отменить":
        return await _cancel(update, context)

    if len(raw_query) < 3:
        await update.message.reply_text("Введите минимум 3 символа.")
        return ASK_COMPLEX

    norm_q = _normalize(raw_query)

    # Формируем варианты
    variants = [raw_query, norm_q, f"жк {norm_q}"]

    # Собираем отзывы
    collected = []
    seen_ids: set[int] = set()
    for q in variants:
        rows = await get_reviews_by_complex_pg(q, similarity_threshold=0.7, limit=30)
        for r in rows:
            if r.id not in seen_ids:
                collected.append(r)
                seen_ids.add(r.id)

    if not collected:
        await update.message.reply_text(
            "Отзывы не найдены. Попробуйте уточнить название или нажмите «Отменить»."
        )
        return ASK_COMPLEX

    # Печатаем карточки
    for r in collected:
        gas_display = "Отсутствует" if r.gas in (0, None) else f"{r.gas}/5"
        card = (
            f"🆔 <b>{r.id}</b>\n"
            f"🏙️ <b>{r.city}</b> — <i>{r.complex_name}</i>\n"
            f"👤 {r.status}\n"
            f"🔥 Отопление: {r.heating}/5 | ⚡ Электро: {r.electricity}/5 | 🛢️ Газ: {gas_display}\n"
            f"💧 Вода: {r.water}/5 | 🔊 Шум: {r.noise}/5 | 🏢 УК: {r.mgmt}/5\n"
            f"💰 Аренда: {r.rent_price}\n"
            f"👍 {r.likes or '—'}\n"
            f"👎 {r.annoy or '—'}\n"
            f"✅ Рекомендация: {'Да' if r.recommend else 'Нет'}\n"
            f"🕒 {r.created_at:%d.%m.%Y %H:%M}"
        )
        await update.message.reply_html(card, disable_web_page_preview=True)

    await update.message.reply_text("Поиск завершён.", reply_markup=MAIN_MENU)
    return ConversationHandler.END

async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Поиск отменён.", reply_markup=MAIN_MENU)
    return ConversationHandler.END

search_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("search", entry_start_search),
        MessageHandler(filters.Regex(r"^🔍 Найти ЖК$"), entry_start_search),
    ],
    states={
        ASK_COMPLEX: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, _show_results
            )
        ]
    },
    fallbacks=[
        CommandHandler("cancel", _cancel),
        MessageHandler(filters.Regex(r"^Отменить$"), _cancel),
        CommandHandler("start", _cancel),
    ],
)
