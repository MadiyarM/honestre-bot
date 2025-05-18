import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import config

# Импорты хэндлеров
from handlers.start import start, menu_choice
from handlers.review import review_conv_handler
from handlers.search import search_conv_handler

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def unknown(update, context):
    # Обработчик неизвестных команд и сообщений
    await update.message.reply_text(
        'Я не понял запрос. Пожалуйста, выберите действие в меню.',
        reply_markup=menu_choice()
    )


def main():
    # Создаем приложение
    app = ApplicationBuilder().token(config.API_TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler('start', start))

    # Главное меню: кнопки из start.menu_choice
    app.add_handler(menu_choice)

    # ConversationHandlers
    app.add_handler(review_conv_handler)
    app.add_handler(search_conv_handler)

    # Неизвестные команды и любые slash-команды
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Запуск бота
    logging.info('Бот запущен')
    app.run_polling()


if __name__ == '__main__':
    main()
