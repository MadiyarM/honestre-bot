from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
from db import get_reviews_by_complex_pg
from handlers.start import MAIN_MENU

ASK_COMPLEX = 0

async def entry_start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название ЖК для поиска (минимум 3 символа):")
    return ASK_COMPLEX

async def _show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if len(query) < 3:
        await update.message.reply_text(
            "Введите минимум 3 символа.", reply_markup=MAIN_MENU
        )
        return ConversationHandler.END

    reviews = await get_reviews_by_complex_pg(query, similarity_threshold=0.8, limit=30)

    if not reviews:
        await update.message.reply_text(
            "Пока нет отзывов по такому ЖК.", reply_markup=MAIN_MENU
        )
        return ConversationHandler.END

    for r in reviews:
        gas_display = "Отсутствует" if r.gas in (0, None) else f"{r.gas}/5"
        text = (
            f"🆔 <b>{r.id}</b>\n"
            f"🏙️ <b>{r.city}</b> — <i>{r.complex_name}</i>\n"
            f"👤 {r.status}\n"
            f"🔥 Отопление: {r.heating}/5 | ⚡ Электро: {r.electricity}/5 | 🛢️ Газ: {gas_display}\n"
            f"💧 Вода: {r.water}/5 | 🎧 Шум: {r.noise}/5 | 🏢 УК: {r.mgmt}/5\n"
            f"💰 Аренда: {r.rent_price}\n"
            f"👍 {r.likes}\n"
            f"👎 {r.annoy}\n"
            f"✅ Рекомендация: {'Да' if r.recommend else 'Нет'}\n"
            f"🕒 {r.created_at:%d.%m.%Y %H:%M}"
        )
        await update.message.reply_html(text, disable_web_page_preview=True)

    # выводим главное меню без лишних сообщений
    await update.message.reply_text("\u200B", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Поиск отменён.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


search_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("search", entry_start_search),
        MessageHandler(filters.Regex(r"^🔍 Найти ЖК$"), entry_start_search),
    ],
    states={
        ASK_COMPLEX: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, _show_results)
        ],
    },
    fallbacks=[CommandHandler("cancel", _cancel)],
)