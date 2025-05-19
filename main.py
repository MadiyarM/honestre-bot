import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)
import config

# Хэндлеры
from handlers.start   import start, menu_choice
from handlers.review  import review_conv_handler
from handlers.search  import search_conv_handler

from db import init_db


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


async def _unknown(update, context):
    from handlers.start import _MENU   # чтобы не дублировать клавиатуру
    await update.message.reply_text(
        "Я не понял запрос. Пожалуйста, выберите действие из меню.",
        reply_markup=_MENU
    )


async def main() -> None:
    # 1) Инициализация БД
    await init_db()

    # 2) Telegram‑приложение
    app = (
        Application.builder()
        .token(config.API_TOKEN)
        .build()
    )

    # ────────── Роутинг ──────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(menu_choice())          # ловим кнопки «📝…» / «🔍…»
    app.add_handler(review_conv_handler)    # диалог «Оставить отзыв»
    app.add_handler(search_conv_handler)    # диалог «Найти ЖК»

    # неизвестные /команды
    app.add_handler(MessageHandler(filters.COMMAND, _unknown))

    logging.info("Bot started")
    await app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    asyncio.run(main())
