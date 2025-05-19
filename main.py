import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)

import config
from handlers.start   import start, menu_handler, MAIN_MENU
from handlers.review  import review_conv_handler
from handlers.search  import search_conv_handler
from db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


async def _unknown(update, context):
    await update.message.reply_text(
        "Я не понял запрос. Пожалуйста, выберите действие из меню.",
        reply_markup=MAIN_MENU
    )


def build_application() -> Application:
    """Создаём и настраиваем объект Application без запуска polling."""
    app = (
        Application.builder()
        .token(config.API_TOKEN)
        .build()
    )

    # ────────── Роутинг ──────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(menu_handler())          # ловим кнопки «📝…» / «🔍…»
    app.add_handler(review_conv_handler)    # диалог «Оставить отзыв»
    app.add_handler(search_conv_handler)    # диалог «Найти ЖК»

    # неизвестные / команды
    app.add_handler(MessageHandler(filters.COMMAND, _unknown))
    return app


def main() -> None:
    """Точка входа для systemd: синхронная функция без вложенных event-loop'ов."""
    # 1) Инициализация БД (асинхронная) – выполним и закроем цикл
    asyncio.run(init_db())

    # 2) Запускаем Telegram‑бот
    app = build_application()
    logging.info("Bot started")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
