"""
Конфигурация бота для СК «Алекс»
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ЮKassa настройки
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# Администраторы
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///training_bot.db')

# Тарифы
SUBSCRIPTION_PRICES = {
    'twice_week': {
        'name': '2 раза в неделю',
        'price': 4500,
        'sessions': 8
    },
    'thrice_week': {
        'name': '3 раза в неделю', 
        'price': 5500,
        'sessions': 12
    },
    'single_session': {
        'name': 'Разовая тренировка',
        'price': 800,
        'sessions': 1
    },
    'individual': {
        'name': 'Индивидуальная тренировка',
        'price': 2500,
        'sessions': 1
    }
}

# Временные слоты для тренировок
TRAINING_SLOTS = [
    '09:00', '10:30', '12:00', '14:00', '15:30', '17:00', '18:30', '20:00'
]

# Список тренеров
TRAINERS = {
    'alex': {
        'name': 'Алексей Петров',
        'specialization': 'Боевые искусства',
        'experience': '8 лет',
        'emoji': '🥋'
    },
    'maria': {
        'name': 'Мария Сидорова', 
        'specialization': 'Фитнес и растяжка',
        'experience': '5 лет',
        'emoji': '🤸‍♀️'
    },
    'ivan': {
        'name': 'Иван Козлов',
        'specialization': 'Силовые тренировки',
        'experience': '6 лет', 
        'emoji': '💪'
    },
    'elena': {
        'name': 'Елена Васильева',
        'specialization': 'Йога и пилатес',
        'experience': '4 года',
        'emoji': '🧘‍♀️'
    }
}

# Настройки уведомлений
NOTIFICATION_SETTINGS = {
    'training_reminder_hours': 1,  # За час до тренировки
    'birthday_reminder_days': 7,   # За неделю до дня рождения
    'inactive_reminder_days': 60   # Если не оплачивал 2 месяца
}
