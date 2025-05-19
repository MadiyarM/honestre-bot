import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)

import config
from handlers.start   import start, MAIN_MENU
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
    app = (
        Application.builder()
        .token(config.API_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(review_conv_handler)
    app.add_handler(search_conv_handler)
    app.add_handler(MessageHandler(filters.COMMAND, _unknown))
    return app


def main() -> None:
    # создаём собственный event‑loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # применяем миграции БД
    loop.run_until_complete(init_db())

    # запускаем бот
    app = build_application()
    logging.info("Bot started")
    app.run_polling(allowed_updates=["message"], close_loop=False)

    # чистое завершение
    loop.close()


if __name__ == "__main__":
    main()
