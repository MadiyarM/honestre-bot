import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import config
# Импорт основного меню: handler и функцию клавиатуры
from handlers.start import start, menu_handler, get_main_menu
from handlers.review import review_conv_handler
from handlers.search import search_conv_handler

# Логирование
logging.basicConfig(
    format='%((asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def unknown(update, context):
    # Обработчик неизвестных команд или сообщений
    await update.message.reply_text(
        'Я не понял запрос. Пожалуйста, выберите действие в меню.',
        reply_markup=get_main_menu()
    )


def main():
    # Создаем приложение с токеном из config.API_TOKEN
    app = ApplicationBuilder().token(config.API_TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler('start', start))

    # Главное меню: обработка кнопок (регистрация handler-а)
    app.add_handler(menu_handler)

    # ConversationHandlers для отзывов и поиска
    app.add_handler(review_conv_handler)
    app.add_handler(search_conv_handler)

    # Обработка любых других команд
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logging.info('Бот запущен')
    app.run_polling()


if __name__ == '__main__':
    main()
