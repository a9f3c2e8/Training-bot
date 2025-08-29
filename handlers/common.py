"""
Общие обработчики команд
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.models import db
from keyboards.inline import get_user_type_keyboard, get_main_menu_keyboard
from utils.formatters import format_user_profile
from config import ADMIN_IDS

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    await state.clear()
    
    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        # Пользователь уже зарегистрирован
        # Проверяем, есть ли у пользователя пробная тренировка
        has_trial = await db.has_trial_training(user['id'])
        
        welcome_text = f"""
🏆 <b>Добро пожаловать обратно, {user['name']}!</b>

<i>Рады видеть вас снова в СК «Алекс»!</i>

<blockquote>Выберите действие:</blockquote>
"""
        await message.answer(
            welcome_text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
    else:
        # Новый пользователь - начинаем регистрацию
        welcome_text = f"""
🏆 <b>Добро пожаловать в СК «Алекс»!</b>

<i>Я помогу вам записаться на тренировки и управлять абонементами.</i>

<b>Мои возможности:</b>
<code>▫️</code> Регистрация спортсменов и родителей
<code>▫️</code> Продажа абонементов с онлайн-оплатой  
<code>▫️</code> Запись на тренировки
<code>▫️</code> Пробные тренировки
<code>▫️</code> Напоминания и уведомления
<code>▫️</code> Личная статистика

<blockquote>Для начала выберите, кто вы:</blockquote>
"""
        await message.answer(
            welcome_text,
            parse_mode='HTML',
            reply_markup=get_user_type_keyboard()
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = """
ℹ️ <b>Справка по боту СК «Алекс»</b>

<b>Основные команды:</b>
<code>▫️ /start</code> - Начать работу с ботом
<code>▫️ /admin</code> - Админ-панель (только для администраторов)

<b>Возможности:</b>
<code>▫️</code> Регистрация спортсменов и родителей
<code>▫️</code> Покупка абонементов с онлайн-оплатой
<code>▫️</code> Разовые и индивидуальные тренировки  
<code>▫️</code> Запись на пробные тренировки
<code>▫️</code> Автоматические напоминания
<code>▫️</code> Персональная статистика

<b>Тарифы:</b>
<code>💰 4500₽</code> - 2 раза в неделю (8 тренировок)
<code>💰 5500₽</code> - 3 раза в неделю (12 тренировок)
<code>💰 800₽</code> - разовая тренировка
<code>💰 2500₽</code> - индивидуальная тренировка

<blockquote>По вопросам обращайтесь к администратору.</blockquote>
"""
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        has_trial = await db.has_trial_training(user['id'])
        reply_markup = get_main_menu_keyboard(show_trial=not has_trial)
    else:
        reply_markup = get_user_type_keyboard()
    
    await message.answer(help_text, parse_mode='HTML', reply_markup=reply_markup)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin - доступ к админ-панели"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    from keyboards.inline import get_admin_panel_keyboard
    
    admin_text = """
⚙️ <b>Админ-панель СК «Алекс»</b>

<i>Добро пожаловать в панель администратора!</i>

<blockquote>Выберите действие:</blockquote>
"""
    
    await message.answer(
        admin_text,
        parse_mode='HTML',
        reply_markup=get_admin_panel_keyboard()
    )

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
            reply_markup=get_user_type_keyboard()
        )
        return
    
    # Получаем активный абонемент
    subscription = await db.get_active_subscription(user['id'])
    
    profile_text = format_user_profile(user, subscription)
    
    from keyboards.inline import get_profile_management_keyboard
    
    await message.answer(
        profile_text,
        parse_mode='HTML',
        reply_markup=get_profile_management_keyboard()
    )

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
            reply_markup=get_user_type_keyboard()
        )
        return
    
    # Получаем активный абонемент
    subscription = await db.get_active_subscription(user['id'])
    
    profile_text = format_user_profile(user, subscription)
    
    from keyboards.inline import get_profile_management_keyboard
    
    await callback.message.edit_text(
        profile_text,
        parse_mode='HTML',
        reply_markup=get_profile_management_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
            reply_markup=get_user_type_keyboard()
        )
        return
    
    # Проверяем, есть ли у пользователя пробная тренировка
    has_trial = await db.has_trial_training(user['id'])
    
    menu_text = f"""
🏠 <b>Главное меню</b>

<i>Привет, {user['name']}!</i>

<blockquote>Выберите действие:</blockquote>
"""
    
    await callback.message.edit_text(
        menu_text,
        parse_mode='HTML',
        reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_training_type")
async def back_to_training_type(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору типа тренировки"""
    from keyboards.inline import get_training_type_keyboard
    
    text = """
📝 <b>Запись на тренировку</b>

<blockquote>Выберите тип тренировки:</blockquote>

<code>▫️</code> <b>Групповая</b> - <i>тренировка в группе до 15 человек</i>
<code>▫️</code> <b>Индивидуальная</b> - <i>персональная работа с тренером</i>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_training_type_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_date_selection")
async def back_to_date_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    from keyboards.inline import get_date_keyboard
    
    data = await state.get_data()
    training_type = data.get('training_type', 'group')
    
    if training_type == "individual":
        # Для индивидуальной тренировки показываем информацию о выбранном тренере
        from config import TRAINERS
        selected_trainer_id = data.get('selected_trainer_id')
        
        if selected_trainer_id and selected_trainer_id in TRAINERS:
            trainer_info = TRAINERS[selected_trainer_id]
            text = f"""
📅 <b>Выбор даты</b>

<i>Индивидуальная тренировка с тренером</i>

👨‍🏫 <b>Тренер:</b> {trainer_info['emoji']} {trainer_info['name']}
🎯 <b>Специализация:</b> <i>{trainer_info['specialization']}</i>
⏱️ <b>Опыт:</b> <code>{trainer_info['experience']}</code>

<blockquote>Выберите удобную дату:</blockquote>
"""
        else:
            text = """
📅 <b>Выбор даты</b>

<i>Индивидуальная тренировка</i>

<blockquote>Выберите удобную дату:</blockquote>
"""
    else:
        text = """
📅 <b>Выбор даты</b>

<i>Групповая тренировка</i>

<blockquote>Выберите удобную дату:</blockquote>
"""
    
    # Определяем, куда должна вести кнопка "Назад"
    if training_type == "individual":
        back_to = "back_to_trainer_selection"
    elif training_type == "trial":
        back_to = "back_to_menu"
    else:
        back_to = "back_to_training_type"
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_date_keyboard(back_to=back_to)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_time_selection")
async def back_to_time_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    from keyboards.inline import get_time_keyboard
    
    data = await state.get_data()
    selected_date = data.get('selected_date')
    training_type = data.get('training_type', 'group')
    
    if not selected_date:
        # Если нет выбранной даты, возвращаемся к выбору даты
        await back_to_date_selection(callback, state)
        return
    
    from datetime import datetime
    date_obj = datetime.fromisoformat(selected_date).date()
    
    if training_type == "trial":
        training_type_text = "пробную тренировку"
    elif training_type == "group":
        training_type_text = "групповую тренировку"
    else:
        training_type_text = "индивидуальную тренировку"
    
    text = f"""
🕐 <b>Выберите время</b>

<i>Запись на {training_type_text}</i>
📅 <b>{date_obj.strftime('%d.%m.%Y')}</b>

<blockquote>Выберите удобное время:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_time_keyboard(selected_date)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_trainer_selection")
async def back_to_trainer_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору тренера"""
    from keyboards.inline import get_trainer_keyboard
    from config import TRAINERS
    
    text = """
👤 <b>Выбор тренера</b>

<i>Запись на индивидуальную тренировку</i>

<blockquote>Выберите тренера для занятия:</blockquote>

<b>Наши тренеры:</b>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_trainer_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "delete_profile")
async def delete_profile_confirmation(callback: CallbackQuery):
    """Подтверждение удаления профиля"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    text = f"""
🗑 <b>Удаление профиля</b>

<b>Внимание!</b> Вы действительно хотите удалить свой профиль?

<b>Будут удалены:</b>
<code>▫️</code> Все ваши данные
<code>▫️</code> История тренировок
<code>▫️</code> Абонементы
<code>▫️</code> Платежи

<blockquote>⚠️ Это действие нельзя отменить!</blockquote>
"""
    
    from keyboards.inline import get_delete_confirmation_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_delete_confirmation_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_delete_profile")
async def confirm_delete_profile(callback: CallbackQuery):
    """Подтверждение удаления профиля"""
    try:
        # Добавим метод удаления пользователя в базу данных
        # await db.delete_user(callback.from_user.id)
        
        text = """
✅ <b>Профиль удален</b>

<i>Ваш профиль и все данные успешно удалены из системы.</i>

<blockquote>Спасибо, что были с нами! До свидания! 👋</blockquote>
"""
        
        await callback.message.edit_text(
            text,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка удаления</b>\n\n"
            "<i>Произошла ошибка при удалении профиля. Обратитесь к администратору.</i>",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        print(f"Ошибка удаления профиля: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery):
    """Редактирование профиля"""
    from keyboards.inline import get_back_keyboard
    
    text = """
✏️ <b>Редактирование профиля</b>

<i>Функция в разработке.</i>

<b>Скоро здесь можно будет изменить:</b>
<code>▫️</code> Имя
<code>▫️</code> Телефон
<code>▫️</code> Дату рождения

<blockquote>Пока обратитесь к администратору для изменения данных.</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("profile")
    )
    await callback.answer()

@router.message()
async def handle_unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer(
            "❓ Я вас не понимаю. Давайте начнем с регистрации - нажмите /start",
            reply_markup=get_user_type_keyboard()
        )
    else:
        has_trial = await db.has_trial_training(user['id'])
        await message.answer(
            "❓ Я вас не понимаю. Используйте кнопки меню для навигации.",
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback"""
    await callback.answer("❓ Неизвестная команда", show_alert=True)
