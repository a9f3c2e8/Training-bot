"""
Форматтеры для красивого отображения информации
"""
from datetime import datetime, date
from typing import Dict, List, Any
from config import SUBSCRIPTION_PRICES

def format_user_profile(user: Dict[str, Any], subscription: Dict[str, Any] = None) -> str:
    """Форматирование профиля пользователя"""
    user_type = "👨‍🎓 Спортсмен" if user['user_type'] == 'athlete' else "👨‍👩‍👦 Родитель"
    
    profile_text = f"""
👤 <b>Мой профиль</b>

<i>{user_type}</i>

<b>Имя:</b> <code>{user['name']}</code>
<b>Телефон:</b> <code>{user['phone']}</code>
<b>Дата рождения:</b> <code>{format_date(user['birth_date'])}</code>
<b>Регистрация:</b> <code>{format_datetime(user['registration_date'])}</code>
"""

    # Добавляем информацию о тренере и достижениях (если есть)
    if user.get('trainer'):
        profile_text += f"\n<b>Тренер:</b> <code>{user['trainer']}</code>"
    
    if user.get('rank_title'):
        profile_text += f"\n<b>Звание:</b> <code>{user['rank_title']}</code>"
    
    if user.get('achievements'):
        profile_text += f"\n<b>Достижения:</b> <i>{user['achievements']}</i>"

    # Добавляем информацию об активном абонементе
    if subscription:
        profile_text += f"\n\n💳 <b>Активный абонемент:</b>\n"
        profile_text += format_subscription_info(subscription)
    else:
        profile_text += f"\n\n💳 <b>Активный абонемент:</b> <i>Отсутствует</i>"

    return profile_text

def format_subscription_info(subscription: Dict[str, Any]) -> str:
    """Форматирование информации об абонементе"""
    sub_type = SUBSCRIPTION_PRICES.get(subscription['subscription_type'], {})
    
    sessions_left = subscription['sessions_total'] - subscription['sessions_used']
    progress_bar = create_progress_bar(subscription['sessions_used'], subscription['sessions_total'])
    
    return f"""
📋 {sub_type.get('name', subscription['subscription_type'])}
💰 Стоимость: {subscription['price']}₽
🏃‍♂️ Тренировок: {subscription['sessions_used']}/{subscription['sessions_total']}
{progress_bar}
📅 Действует до: {format_date(subscription['end_date'])}
✅ Статус: {'Активен' if subscription['is_active'] else 'Неактивен'}
"""

def format_training_list(trainings: List[Dict[str, Any]]) -> str:
    """Форматирование списка тренировок"""
    if not trainings:
        return """
📅 <b>Ваши тренировки</b>

<i>У вас пока нет запланированных тренировок.</i>

<b>Как записаться:</b>
<code>▫️</code> Нажмите <b>📝 Записаться</b> для групповой или индивидуальной тренировки
<code>▫️</code> Нажмите <b>🆓 Пробная тренировка</b> для первого знакомства

<blockquote>Ждем вас на тренировках! 💪</blockquote>
"""
    
    # Разделяем тренировки на предстоящие и прошедшие
    upcoming = []
    past = []
    today = date.today()
    
    for training in trainings:
        training_date = training['training_date']
        if isinstance(training_date, str):
            training_date = datetime.fromisoformat(training_date).date()
        
        if training_date >= today:
            upcoming.append(training)
        else:
            past.append(training)
    
    text = "📅 <b>Ваши тренировки</b>\n\n"
    
    # Показываем предстоящие тренировки
    if upcoming:
        text += "🔥 <b>Предстоящие тренировки:</b>\n\n"
        for training in upcoming:
            # Определяем тип тренировки с эмодзи
            if training['is_trial']:
                training_type_text = "🆓 <b>Пробная тренировка</b>"
            elif training['training_type'].lower() == 'групповая тренировка':
                training_type_text = "👥 <b>Групповая тренировка</b>"
            elif training['training_type'].lower() == 'индивидуальная тренировка':
                training_type_text = "👤 <b>Индивидуальная тренировка</b>"
            else:
                training_type_text = f"🏃‍♂️ <b>{training['training_type']}</b>"
            
            text += f"{training_type_text}\n"
            text += f"📅 <b>Дата:</b> <code>{format_date(training['training_date'])}</code>\n"
            text += f"🕐 <b>Время:</b> <code>{training['training_time']}</code>\n"
            
            if training.get('trainer'):
                text += f"👨‍🏫 <b>Тренер:</b> <i>{training['trainer']}</i>\n"
            
            status_name = get_status_name(training['status'])
            text += f"📊 <b>Статус:</b> <i>{status_name}</i>\n\n"
    
    # Показываем последние 5 прошедших тренировок
    if past:
        text += "📋 <b>История тренировок:</b>\n\n"
        for training in past[:5]:  # Показываем только последние 5
            # Статус с эмодзи
            status_emoji = {
                'completed': '✅',
                'cancelled': '❌',
                'no_show': '😞'
            }.get(training['status'], '❓')
            
            # Определяем тип тренировки
            if training['is_trial']:
                training_type_text = "🆓 <b>Пробная тренировка</b>"
            elif training['training_type'].lower() == 'групповая тренировка':
                training_type_text = "👥 <b>Групповая тренировка</b>"
            elif training['training_type'].lower() == 'индивидуальная тренировка':
                training_type_text = "👤 <b>Индивидуальная тренировка</b>"
            else:
                training_type_text = f"🏃‍♂️ <b>{training['training_type']}</b>"
            
            text += f"{status_emoji} {training_type_text}\n"
            text += f"📅 <b>Дата:</b> <code>{format_date(training['training_date'])}</code>\n"
            text += f"🕐 <b>Время:</b> <code>{training['training_time']}</code>\n"
            
            if training.get('trainer'):
                text += f"👨‍🏫 <b>Тренер:</b> <i>{training['trainer']}</i>\n"
            
            text += "\n"
        
        if len(past) > 5:
            text += f"<i>И ещё {len(past) - 5} тренировок в истории...</i>\n\n"
    
    # Добавляем итоговую информацию
    total_upcoming = len(upcoming)
    total_past = len(past)
    
    if total_upcoming > 0 or total_past > 0:
        text += "<blockquote>"
        if total_upcoming > 0:
            text += f"⏰ Предстоящих: <b>{total_upcoming}</b>"
            if total_past > 0:
                text += f" • 📋 Завершенных: <b>{total_past}</b>"
        else:
            text += f"📋 Завершенных тренировок: <b>{total_past}</b>"
        text += "</blockquote>"
    
    return text

def format_admin_user_info(user: Dict[str, Any]) -> str:
    """Форматирование информации о пользователе для админа"""
    user_type = "Спортсмен" if user['user_type'] == 'athlete' else "Родитель"
    
    return f"""
👤 <b>Информация о пользователе</b>

🆔 <b>ID:</b> {user['id']}
📱 <b>Telegram ID:</b> {user['telegram_id']}
👨‍💼 <b>Тип:</b> {user_type}
👨‍💼 <b>Имя:</b> {user['name']}
📱 <b>Телефон:</b> {user['phone']}
🎂 <b>Дата рождения:</b> {format_date(user['birth_date'])}
📅 <b>Регистрация:</b> {format_datetime(user['registration_date'])}
🏃‍♂️ <b>Тренер:</b> {user.get('trainer', 'Не назначен')}
🏆 <b>Звание:</b> {user.get('rank_title', 'Не указано')}
🎯 <b>Достижения:</b> {user.get('achievements', 'Не указаны')}
📝 <b>Заметки:</b> {user.get('notes', 'Нет заметок')}
✅ <b>Активен:</b> {'Да' if user['is_active'] else 'Нет'}
"""

def format_schedule(trainings: List[Dict[str, Any]]) -> str:
    """Форматирование расписания для админа"""
    if not trainings:
        return "📅 <b>Расписание пустое</b>"
    
    text = "📅 <b>Расписание тренировок:</b>\n\n"
    current_date = None
    
    for training in trainings:
        # Группируем по датам
        if current_date != training['training_date']:
            current_date = training['training_date']
            text += f"📆 <b>{format_date(current_date)}</b>\n"
        
        status_emoji = {
            'scheduled': '⏰',
            'completed': '✅',
            'cancelled': '❌',
            'no_show': '😞'
        }.get(training['status'], '❓')
        
        text += f"{status_emoji} {training['training_time']} - {training['user_name']}\n"
        text += f"📱 {training['user_phone']}\n"
        text += f"🏃‍♂️ {training['training_type']}\n"
        
        if training.get('trainer'):
            text += f"👨‍🏫 {training['trainer']}\n"
        
        text += "\n"
    
    return text

def format_date(date_str: str) -> str:
    """Форматирование даты"""
    try:
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        else:
            date_obj = date_str
        
        months = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ]
        
        return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"
    except:
        return str(date_str)

def format_datetime(datetime_str: str) -> str:
    """Форматирование даты и времени"""
    try:
        if isinstance(datetime_str, str):
            dt_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        else:
            dt_obj = datetime_str
        
        return f"{format_date(dt_obj.date())} в {dt_obj.strftime('%H:%M')}"
    except:
        return str(datetime_str)

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Создание прогресс-бара"""
    if total == 0:
        return "▱" * length
    
    filled = int((current / total) * length)
    empty = length - filled
    
    return "▰" * filled + "▱" * empty

def get_status_name(status: str) -> str:
    """Получение названия статуса на русском"""
    status_names = {
        'scheduled': 'Запланирована',
        'completed': 'Завершена',
        'cancelled': 'Отменена',
        'no_show': 'Не явился',
        'pending': 'Ожидает оплаты',
        'paid': 'Оплачено',
        'failed': 'Ошибка оплаты'
    }
    return status_names.get(status, status)

def format_payment_info(payment: Dict[str, Any]) -> str:
    """Форматирование информации о платеже"""
    return f"""
💳 <b>Информация о платеже</b>

🆔 <b>ID:</b> {payment['payment_id']}
💰 <b>Сумма:</b> {payment['amount']}₽
📝 <b>Описание:</b> {payment['description']}
📊 <b>Статус:</b> {get_status_name(payment['status'])}
📅 <b>Создан:</b> {format_datetime(payment['created_at'])}
"""

def format_subscription_offer(subscription_type: str) -> str:
    """Форматирование предложения абонемента"""
    info = SUBSCRIPTION_PRICES.get(subscription_type)
    if not info:
        return "Абонемент не найден"
    
    return f"""
💳 <b>{info['name']}</b>

💰 <b>Стоимость:</b> {info['price']}₽
🏃‍♂️ <b>Количество тренировок:</b> {info['sessions']}
📊 <b>Стоимость за тренировку:</b> {info['price'] // info['sessions']}₽

{_get_subscription_description(subscription_type)}
"""

def _get_subscription_description(subscription_type: str) -> str:
    """Получение описания абонемента"""
    descriptions = {
        'twice_week': '🗓 Идеально для начинающих и поддержания формы',
        'thrice_week': '🔥 Для серьезных тренировок и быстрого прогресса',
        'single_session': '🎯 Попробуйте перед покупкой абонемента',
        'individual': '👨‍🏫 Персональный подход и максимальный результат'
    }
    return descriptions.get(subscription_type, '')
