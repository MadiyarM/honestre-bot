from dotenv import load_dotenv
import os

load_dotenv()           # автоматически загрузит .env

API_TOKEN      = os.getenv("BOT_API_TOKEN")
DATABASE_URL   = os.getenv("DATABASE_URL")

# Список вопросов для ConversationHandler (как был раньше)
QUESTIONS = [
    {'key': 'phone',        'text': '📱 Введите ваш мобильный номер для подтверждения:',         'type': 'text'},
    {'key': 'city',         'text': '🏙️ В каком городе находится ваш ЖК?',                      'type': 'text'},
    {'key': 'complex_name', 'text': '🏘️ Название жилого комплекса:',                            'type': 'text'},
    {'key': 'status',       'text': '👤 Ваш статус:',                                            'type': 'choice',  'options': ['Собственник', 'Арендатор']},
    {'key': 'heating',      'text': '🔥 Оцените систему отопления (1–5):',                       'type': 'rating'},
    {'key': 'electricity',  'text': '⚡️ Оцените электроснабжение (1–5):',                       'type': 'rating'},
    {'key': 'gas',          'text': '🔥 Оцените газоснабжение (1–5):',                           'type': 'rating'},
    {'key': 'water',        'text': '💧 Оцените водоснабжение (1–5):',                           'type': 'rating'},
    {'key': 'noise',        'text': '🔊 Соседи: уровень шума (1 — Очень шумно, 5 — Благоприятно):', 'type': 'rating'},
    {'key': 'mgmt',         'text': '🏢 Оцените работу УК (1–5):',                               'type': 'rating'},
    {'key': 'rent_price',   'text': '💰 Сколько вы платите за аренду (₸/мес)? Если вы собственник — введите "—".', 'type': 'text'},
    {'key': 'likes',        'text': '👍 Что вам нравится в этом ЖК?',                            'type': 'text'},
    {'key': 'annoy',        'text': '👎 Что вас больше всего раздражает в этом ЖК?',             'type': 'text'},
    {'key': 'recommend',    'text': '✅ Советовали бы вы этот ЖК? (Да/Нет)',                     'type': 'choice',  'options': ['Да', 'Нет']},
]  # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
