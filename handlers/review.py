from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import re
import config
from db import save_review

# Состояния: по числу вопросов + CONFIRM
NUM_Q = len(config.QUESTIONS)
(ASK_PHONE, *MID_STATES, CONFIRM) = range(NUM_Q + 1)

async def start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'] = {}
    context.user_data['current_q'] = 0
    q = config.QUESTIONS[0]
    # клавиатура для choice
    if q.get('type') == 'choice':
        kb = [[opt] for opt in q['options']] + [['Назад']]
        markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    else:
        markup = ReplyKeyboardRemove()
    await update.message.reply_text(q['text'], reply_markup=markup)
    return ASK_PHONE

async def ask_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Назад в меню
    if text == 'Назад':
        from handlers.start import start  # импорт внутри, чтобы не было циклических зависимостей
        await start(update, context)
        return ConversationHandler.END

    idx = context.user_data['current_q']
    q = config.QUESTIONS[idx]

    # валидация телефона
    if idx == ASK_PHONE:
        if not re.match(r'^(?:\+7|8)\d{10}$', text):
            await update.message.reply_text(
                "❗️ Неверный формат. Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
            return ASK_PHONE
        context.user_data['answers'][q['key']] = text

    # выбор из списка
    elif q.get('type') == 'choice':
        if text not in q['options']:
            kb = [[opt] for opt in q['options']] + [['Назад']]
            markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                "❗️ Пожалуйста, выберите вариант из списка.",
                reply_markup=markup
            )
            return idx
        context.user_data['answers'][q['key']] = text

    # рейтинг 1-5
    elif q.get('type') == 'rating':
        if not text.isdigit() or not 1 <= int(text) <= 5:
            await update.message.reply_text("❗️ Введите число от 1 до 5")
            return idx
        context.user_data['answers'][q['key']] = int(text)

    # свободный текст
    else:
        context.user_data['answers'][q['key']] = text

    # следующий вопрос
    idx += 1
    context.user_data['current_q'] = idx
    if idx < NUM_Q:
        next_q = config.QUESTIONS[idx]
        if next_q.get('type') == 'choice':
            kb = [[opt] for opt in next_q['options']] + [['Назад']]
            markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
        else:
            markup = ReplyKeyboardRemove()
        await update.message.reply_text(next_q['text'], reply_markup=markup)
        return idx

    # формирование сводки
    summary_lines = []
    for key, val in context.user_data['answers'].items():
        label = config.LABELS.get(key, key)
        summary_lines.append(f"{label}: {val}")
    summary = "\n".join(summary_lines)
    kb = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(summary + "\n\nПодтверждаете отправку?", reply_markup=kb)
    return CONFIRM

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == 'да':
        save_review(context.user_data['answers'])
        await update.message.reply_text('Спасибо, отзыв сохранён!', reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text('Отзыв отменён.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ConversationHandler
review_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^Оставить отзыв$'), start_review)],
    states={
        **{i: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_field)] for i in range(NUM_Q)},
        CONFIRM: [MessageHandler(filters.Regex('^(Да|Нет)$'), finish)]
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
