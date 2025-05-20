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
from handlers.start import MAIN_MENU, start as cmd_start  # для возврата в меню

# Состояния диалога
ASKING, CONFIRM = range(2)

# Клавиатура подтверждения
_CONFIRM_KB = ReplyKeyboardMarkup(
    [["Да", "Нет", "Назад"]], resize_keyboard=True, one_time_keyboard=True
)

# Допустимые коды операторов
_VALID_CODES = {
    "700","701","702","703","704","705","706","707","708","709",
    "747","750","751","760","761","762","763","764",
    "771","775","776","777","778","727",
}

# ────────── Точка входа ──────────
async def entry_start_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["answers"] = {}
    context.user_data["q_idx"] = 0
    await _ask_next_question(update, context)
    return ASKING


# ────────── Формируем клавиатуру с «Назад» ──────────
def _build_markup(options: list[str] | None, allow_back: bool) -> ReplyKeyboardMarkup | None:
    rows = []
    if options:
        rows.append(options)
    if allow_back:
        rows.append(["Назад"])
    if rows:
        return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)
    return None


# ────────── Задаём вопросы по очереди ──────────
async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]

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
            f"✅ Рекомендация: {'Да' if answers.get('recommend') else 'Нет'}",
        ]
        summary = "\n".join(summary_lines)
        await update.message.reply_text(
            summary + "\n\nПодтверждаете отзыв?",
            reply_markup=_CONFIRM_KB
        )
        return CONFIRM

    q = config.QUESTIONS[idx]
    allow_back = idx > 0

    markup = _build_markup(q.get("options"), allow_back) if q["type"] == "choice" else _build_markup(None, allow_back)
    await update.message.reply_text(q["text"], reply_markup=markup)
    return ASKING


# ────────── Принимаем ответ пользователя ──────────
async def _collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q_idx"]
    q   = config.QUESTIONS[idx]
    text = (update.message.text or "").strip()

    # Кнопка «Назад»
    if text.lower() == "назад":
        if idx == 0:
            await update.message.reply_text("Вы уже на первом вопросе.")
            return ASKING
        context.user_data["q_idx"] -= 1
        return await _ask_next_question(update, context)

    # Специальная валидация телефона
    if q["key"] == "phone":
        valid, err = _validate_phone(text)
        if not valid:
            await update.message.reply_text(err)
            return ASKING
        context.user_data["answers"][q["key"]] = text

    # Валидация рейтингов
    elif q["type"] == "rating":
        try:
            val = int(text)
            if not 1 <= val <= 5:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Введите число от 1 до 5.")
            return ASKING
        context.user_data["answers"][q["key"]] = val

    # Выбор из списка
    elif q["type"] == "choice":
        if text not in q["options"]:
            await update.message.reply_text("Пожалуйста, выберите вариант из клавиатуры.")
            return ASKING
        context.user_data["answers"][q["key"]] = text

    else:
        context.user_data["answers"][q["key"]] = text

    context.user_data["q_idx"] += 1
    return await _ask_next_question(update, context)


# ────────── Проверка номера телефона ──────────
def _validate_phone(num: str) -> tuple[bool, str | None]:
    if num.startswith("+7") and len(num) == 12 and num[1:].isdigit():
        code = num[2:5]
    elif num.startswith("8") and len(num) == 11 and num.isdigit():
        code = num[1:4]
    else:
        return False, "❗️ Неверный формат. Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX"

    if code not in _VALID_CODES:
        return False, "❗️ Неверный формат. Введите действительный номер"

    return True, None


# ────────── Обрабатываем подтверждение ──────────
async def _confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()
    if text == "назад":
        context.user_data["q_idx"] = len(config.QUESTIONS) - 1
        return await _ask_next_question(update, context)

    if text == "да":
        answers = context.user_data["answers"]
        answers["recommend"] = True if answers.get("recommend") == "Да" else False
        await save_review(answers)
        await update.message.reply_text(
            "Спасибо! Отзыв принят ✅",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    elif text == "нет":
        await update.message.reply_text(
            "Ок, возвращаюсь в меню. Выберите действие:",
            reply_markup=MAIN_MENU
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, нажмите 'Да', 'Нет' или 'Назад'.")
        return CONFIRM


# ────────── Прерывание/Перезапуск ──────────
async def _restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Срабатывает на /start внутри диалога — обнуляем форму и показываем меню."""
    context.user_data.clear()
    await cmd_start(update, context)
    return ConversationHandler.END


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
    states=[
        ASKING:  [MessageHandler(filters.TEXT & ~filters.COMMAND, _collect_answer)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, _confirm)],
    ],
    fallbacks=[
        CommandHandler("cancel", _cancel),
        CommandHandler("start", _restart),
    ],
)
