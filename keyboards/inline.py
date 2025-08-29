"""
Inline клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUBSCRIPTION_PRICES, TRAINING_SLOTS, TRAINERS
from datetime import datetime, timedelta

def get_user_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа пользователя"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏃‍♂️ Я спортсмен", callback_data="user_type:athlete"),
            InlineKeyboardButton(text="👨‍👩‍👦 Я родитель", callback_data="user_type:parent")
        ]
    ])
    return keyboard

def get_main_menu_keyboard(show_trial: bool = True) -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="💳 Абонемент", callback_data="buy_subscription")
        ],
        [
            InlineKeyboardButton(text="📝 Записаться", callback_data="book_training"),
            InlineKeyboardButton(text="📅 Тренировки", callback_data="my_trainings")
        ]
    ]
    
    # Добавляем кнопку пробной тренировки только если пользователь ещё не записывался
    if show_trial:
        buttons.append([InlineKeyboardButton(text="🆓 Пробная тренировка", callback_data="trial_training")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора абонемента"""
    buttons = []
    
    # Группируем абонементы по 2 в ряд где возможно
    subscription_items = list(SUBSCRIPTION_PRICES.items())
    
    for i in range(0, len(subscription_items), 2):
        row = []
        for j in range(2):
            if i + j < len(subscription_items):
                key, info = subscription_items[i + j]
                # Укороченные названия для красивого отображения
                short_names = {
                    'twice_week': '2 раза/нед',
                    'thrice_week': '3 раза/нед', 
                    'single_session': 'Разовая',
                    'individual': 'Индивидуальная'
                }
                text = f"{short_names.get(key, info['name'])} - {info['price']}₽"
                row.append(InlineKeyboardButton(text=text, callback_data=f"subscription:{key}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_training_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа тренировки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Групповая", callback_data="training_type:group"),
            InlineKeyboardButton(text="👤 Индивидуальная", callback_data="training_type:individual")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard

def get_trainer_keyboard(trainers_data: list = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора тренера для индивидуальной тренировки"""
    buttons = []
    
    # Если данные не переданы, используем данные из конфига
    if trainers_data is None:
        trainer_items = list(TRAINERS.items())
        
        for i in range(0, len(trainer_items), 2):
            row = []
            for j in range(2):
                if i + j < len(trainer_items):
                    trainer_id, trainer_info = trainer_items[i + j]
                    button_text = f"{trainer_info['emoji']} {trainer_info['name'].split()[0]}"
                    row.append(InlineKeyboardButton(text=button_text, callback_data=f"trainer:{trainer_id}"))
            buttons.append(row)
    else:
        # Используем данные из базы данных
        for i in range(0, len(trainers_data), 2):
            row = []
            for j in range(2):
                if i + j < len(trainers_data):
                    trainer = trainers_data[i + j]
                    if trainer['is_active']:  # Показываем только активных тренеров
                        emoji = trainer.get('emoji', '👨‍🏫')
                        name = trainer['trainer_name'].split()[0]
                        button_text = f"{emoji} {name}"
                        row.append(InlineKeyboardButton(
                            text=button_text, 
                            callback_data=f"trainer:{trainer['trainer_id']}"
                        ))
            if row:  # Добавляем ряд только если он не пустой
                buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_training_type")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_date_keyboard(days_ahead: int = 14, back_to: str = "back_to_training_type") -> InlineKeyboardMarkup:
    """Клавиатура выбора даты"""
    buttons = []
    today = datetime.now().date()
    
    # Первые две строки - сегодня и завтра (если есть)
    for i in range(min(2, days_ahead)):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m")
        
        if i == 0:
            text = f"🔸 Сегодня {date_str}"
        elif i == 1:
            text = f"🔹 Завтра {date_str}"
        
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"date:{date.isoformat()}")])
    
    # Остальные дни группируем по 2 в ряд
    for i in range(2, days_ahead, 2):
        row = []
        for j in range(2):
            if i + j < days_ahead:
                date = today + timedelta(days=i + j)
                date_str = date.strftime("%d.%m")
                day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date.weekday()]
                
                text = f"{day_name} {date_str}"
                row.append(InlineKeyboardButton(text=text, callback_data=f"date:{date.isoformat()}"))
        
        if row:  # Добавляем ряд только если он не пустой
            buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_to)])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_time_keyboard(selected_date: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора времени"""
    buttons = []
    
    # Разбиваем слоты по 3 в ряд для более компактного отображения
    for i in range(0, len(TRAINING_SLOTS), 3):
        row = []
        for j in range(3):
            if i + j < len(TRAINING_SLOTS):
                time_slot = TRAINING_SLOTS[i + j]
                # Добавляем иконку часов для красоты
                row.append(InlineKeyboardButton(
                    text=f"🕐 {time_slot}", 
                    callback_data=f"time:{selected_date}:{time_slot}"
                ))
        if row:  # Добавляем ряд только если он не пустой
            buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_date_selection")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, подтвердить", callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_time_selection")
        ]
    ])
    return keyboard

def get_payment_keyboard(payment_url: str, payment_type: str = "subscription") -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    # Определяем callback для проверки платежа в зависимости от типа
    check_callback = "payment_check" if payment_type == "subscription" else "payment_check_individual"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=check_callback)],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
    ])
    return keyboard

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="admin_schedule")
        ],
        [
            InlineKeyboardButton(text="💰 Платежи", callback_data="admin_payments"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
    ])
    return keyboard

def get_user_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления пользователем"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data=f"edit_user:{user_id}")],
        [InlineKeyboardButton(text="📋 История тренировок", callback_data=f"user_trainings:{user_id}")],
        [InlineKeyboardButton(text="💳 История платежей", callback_data=f"user_payments:{user_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
    ])
    return keyboard

def get_back_keyboard(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Простая клавиатура "Назад" """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)]
    ])
    return keyboard

def get_profile_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления профилем"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
            InlineKeyboardButton(text="🗑 Удалить профиль", callback_data="delete_profile")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard

def get_delete_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления профиля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete_profile"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="profile")
        ]
    ])
    return keyboard

def get_schedule_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления расписанием"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Настроить дни", callback_data="manage_training_days"),
            InlineKeyboardButton(text="🕐 Настроить время", callback_data="manage_training_times")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_schedule"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="schedule_settings")
        ],
        [
            InlineKeyboardButton(text="📋 Экспорт", callback_data="export_schedule")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin_panel")]
    ])
    return keyboard

def get_schedule_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек расписания"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍🏫 Тренеры", callback_data="manage_trainers"),
            InlineKeyboardButton(text="📅 Дни недели", callback_data="manage_days")
        ],
        [
            InlineKeyboardButton(text="🕐 Время", callback_data="manage_time_slots"),
            InlineKeyboardButton(text="🔄 Синхронизация", callback_data="sync_schedule_data")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_schedule")]
    ])
    return keyboard

def get_trainers_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления тренерами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить тренера", callback_data="add_trainer"),
            InlineKeyboardButton(text="👥 Список тренеров", callback_data="list_trainers")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="schedule_settings")]
    ])
    return keyboard

def get_days_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления днями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Список дней", callback_data="list_days"),
            InlineKeyboardButton(text="⚙️ Настроить", callback_data="configure_days")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="schedule_settings")]
    ])
    return keyboard

def get_time_slots_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления временными слотами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить время", callback_data="add_time_slot"),
            InlineKeyboardButton(text="🕐 Список времени", callback_data="list_time_slots")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="schedule_settings")]
    ])
    return keyboard

def get_trainer_list_keyboard(trainers: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком тренеров для управления"""
    buttons = []
    
    for trainer in trainers:
        status_emoji = "✅" if trainer['is_active'] else "❌"
        button_text = f"{status_emoji} {trainer['emoji']} {trainer['trainer_name']}"
        buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"toggle_trainer:{trainer['trainer_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_trainers")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_days_list_keyboard(days: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком дней для управления"""
    buttons = []
    
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    # Группируем дни по 2 в ряд
    for i in range(0, len(days), 2):
        row = []
        for j in range(2):
            if i + j < len(days):
                day = days[i + j]
                status_emoji = "✅" if day['is_active'] else "❌"
                day_name = day_names[day['day_of_week']]
                button_text = f"{status_emoji} {day_name}"
                row.append(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"toggle_day:{day['day_of_week']}"
                ))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_days")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_time_slots_list_keyboard(time_slots: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком временных слотов для управления"""
    buttons = []
    
    # Группируем слоты по 3 в ряд
    for i in range(0, len(time_slots), 3):
        row = []
        for j in range(3):
            if i + j < len(time_slots):
                slot = time_slots[i + j]
                status_emoji = "✅" if slot['is_active'] else "❌"
                button_text = f"{status_emoji} {slot['time_slot']}"
                row.append(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"toggle_time_slot:{slot['time_slot']}"
                ))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_time_slots")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
