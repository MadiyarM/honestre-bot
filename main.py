# main.py
from telegram.ext import ApplicationBuilder
import config
from handlers.start import start, menu_choice
from handlers.review import review_conv_handler
from handlers.search import search_conv_handler

def main():
    app = ApplicationBuilder().token(config.API_TOKEN).build()

    # 1) Сначала ConversationHandler для отзыва
    app.add_handler(review_conv_handler)

    # 2) ConversationHandler для «Узнать отзыв о ЖК»
    app.add_handler(search_conv_handler)

    # 2) /start и меню
    app.add_handler(start)
    app.add_handler(menu_choice)

    app.run_polling()

if __name__ == "__main__":
    main()
