# handlers/review.py
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler,
    MessageHandler, filters, ContextTypes
)
import config
from db import save_review
import re

# Состояния: по числу вопросов + CONFIRM
(
    ASK_PHONE, ASK_CITY, ASK_NAME, ASK_STATUS,
    ASK_HEATING, ASK_ELECTRICITY, ASK_GAS, ASK_WATER,
    ASK_NOISE, ASK_MGMT, ASK_RENT, ASK_LIKES,
    ASK_ANNOY, ASK_RECOMMEND, CONFIRM
) = range(len(config.QUESTIONS) + 1)

# Запуск опроса
async def start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'] = {}
    context.user_data['current_q'] = 0
    q = config.QUESTIONS[0]
    await update.message.reply_text(q['text'], reply_markup=ReplyKeyboardRemove())
    return ASK_PHONE

# Обработка ответов
async def ask_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработка команды "Назад" — возвращаем в меню
    if update.message.text.strip() == 'Назад':
        from handlers.start import start
        await start(update, context)
        return ConversationHandler.END

    idx = context.user_data['current_q']
    q = config.QUESTIONS[idx]
    text = update.message.text.strip()

    # Валидация телефона
    if idx == ASK_PHONE:
        if not re.match(r'^(?:\+7|8)\d{10}$', text):
            await update.message.reply_text(
                "❗️ Неверный формат. Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
            return ASK_PHONE
        context.user_data['answers'][q['key']] = text

    # Выбор опции
    elif q.get('type') == 'choice':
        if text not in q['options']:
            kb = [[opt] for opt in q['options']]
            markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                "❗️ Пожалуйста, выберите вариант из списка.",
                reply_markup=markup
            )
            return idx
        context.user_data['answers'][q['key']] = text

    # Рейтинг 1–5
    elif q.get('type') == 'rating':
        if not text.isdigit() or not 1 <= int(text) <= 5:
            await update.message.reply_text("❗️ Введите число от 1 до 5")
            return idx
        context.user_data['answers'][q['key']] = int(text)

    # Текст
    else:
        context.user_data['answers'][q['key']] = text

    # Следующий вопрос
    idx += 1
    context.user_data['current_q'] = idx

    if idx < len(config.QUESTIONS):
        next_q = config.QUESTIONS[idx]
        if next_q.get('type') == 'choice':
            kb = [[opt] for opt in next_q['options']]
            markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(next_q['text'], reply_markup=markup)
        else:
            await update.message.reply_text(next_q['text'], reply_markup=ReplyKeyboardRemove())
        return idx

    # Сводка
    labels = {
        'phone': '📱 Телефон', 'city': '🏙️ Город', 'complex_name': '🏘️ ЖК',
        'status': '👤 Статус', 'heating': '🔥 Отопление', 'electricity': '⚡️ Электроснабжение',
        'gas': '🔥 Газоснабжение', 'water': '💧 Водоснабжение', 'noise': '🔊 Шум',
        'mgmt': '🏢 УК (застройщик)', 'rent_price': '💰 Аренда', 'likes': '👍 Плюсы',
        'annoy': '👎 Минусы', 'recommend': '✅ Советую'
    }
    lines = [f"{labels.get(k)}: {v}" for k,v in context.user_data['answers'].items()]
    summary = "\n".join(lines)

    # Подтверждение
    kb = ReplyKeyboardMarkup([['Да','Нет']], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(summary + "\n\nПодтвердите отправку:", reply_markup=kb)
    return CONFIRM

# Завершение
async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'да':
        save_review(context.user_data['answers'])
        await update.message.reply_text('Спасибо, отзыв сохранён!', reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text('Отзыв отменён.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

review_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^Оставить отзыв$'), start_review)],
    states={
        **{i: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_field)] for i in range(len(config.QUESTIONS))},
        CONFIRM: [MessageHandler(filters.Regex('^(Да|Нет)$'), finish)]
    },
    fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
)
