"""
Обработчики админ-панели
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, timedelta
import aiosqlite

from database.models import db
from keyboards.inline import (
    get_admin_panel_keyboard, get_user_management_keyboard,
    get_back_keyboard, get_main_menu_keyboard
)
from utils.formatters import format_admin_user_info, format_schedule
from config import ADMIN_IDS

router = Router()

class AdminStates(StatesGroup):
    waiting_for_user_edit = State()
    waiting_for_broadcast_message = State()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Показать админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
⚙️ <b>Админ-панель СК «Алекс»</b>

<i>Добро пожаловать в панель администратора!</i>

<blockquote>Выберите действие:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def show_all_users(callback: CallbackQuery):
    """Показать всех пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    users = await db.get_all_users()
    
    if not users:
        text = """
👥 <b>Пользователи не найдены</b>

<i>В системе пока нет зарегистрированных пользователей.</i>
"""
    else:
        text = f"""
👥 <b>Все пользователи ({len(users)})</b>

<i>Список всех зарегистрированных пользователей:</i>

"""
        
        for user in users:
            user_type = "👨‍🎓" if user['user_type'] == 'athlete' else "👨‍👩‍👦"
            status = "✅" if user['is_active'] else "❌"
            
            text += f"{user_type} {status} <b>{user['name']}</b>\n"
            text += f"<code>📱 {user['phone']}</code> | <code>ID: {user['id']}</code>\n"
            text += f"<code>📅 {user['registration_date'][:10]}</code>\n\n"
            
            # Ограничиваем длину сообщения
            if len(text) > 3500:
                text += "<i>... и другие пользователи</i>"
                break
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    await callback.answer()

@router.callback_query(F.data == "admin_schedule")
async def show_admin_schedule(callback: CallbackQuery):
    """Показать расписание и записи"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем расписание на ближайшие 7 дней
    today = date.today()
    week_later = today + timedelta(days=7)
    
    trainings = await db.get_training_schedule(today, week_later)
    
    if not trainings:
        text = """
📅 <b>Расписание тренировок</b>

<i>На ближайшие 7 дней записей нет.</i>

<blockquote>Записи будут отображаться здесь по мере их появления.</blockquote>
"""
    else:
        text = f"""
📅 <b>Расписание тренировок</b>

<i>Все записи на ближайшие 7 дней ({len(trainings)} записей):</i>

"""
        current_date = None
        for training in trainings:
            # Группируем по датам
            if current_date != training['training_date']:
                current_date = training['training_date']
                text += f"\n📆 <b>{format_date(current_date)}</b>\n"
            
            # Статус тренировки
            status_emoji = {
                'scheduled': '⏰',
                'completed': '✅',
                'cancelled': '❌',
                'no_show': '😞'
            }.get(training['status'], '❓')
            
            # Тип тренировки
            training_type = "🆓 Пробная" if training['is_trial'] else f"🏃‍♂️ {training['training_type']}"
            
            text += f"{status_emoji} <b>{training['training_time']}</b> - {training_type}\n"
            text += f"👤 <code>{training['user_name']}</code>\n"
            text += f"📱 <code>{training['user_phone']}</code>\n"
            
            if training.get('trainer'):
                text += f"👨‍🏫 {training['trainer']}\n"
            
            text += "\n"
    
    from keyboards.inline import get_schedule_management_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_schedule_management_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем статистику
    all_users = await db.get_all_users()
    
    # Считаем статистику
    total_users = len(all_users)
    active_users = len([u for u in all_users if u['is_active']])
    athletes = len([u for u in all_users if u['user_type'] == 'athlete'])
    parents = len([u for u in all_users if u['user_type'] == 'parent'])
    
    # Регистрации за последние 30 дней
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_users = len([
        u for u in all_users 
        if datetime.fromisoformat(u['registration_date'].replace('Z', '+00:00')) > thirty_days_ago
    ])
    
    text = f"""
📊 <b>Статистика СК «Алекс»</b>

<b>Пользователи:</b>
<code>👥 Всего:</code> <b>{total_users}</b>
<code>✅ Активных:</code> <b>{active_users}</b>
<code>❌ Неактивных:</code> <b>{total_users - active_users}</b>

<b>По типам:</b>
<code>👨‍🎓 Спортсменов:</code> <b>{athletes}</b>
<code>👨‍👩‍👦 Родителей:</code> <b>{parents}</b>

<b>Активность:</b>
<code>📈 Новых за 30 дней:</code> <b>{recent_users}</b>

<i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
📢 <b>Рассылка сообщений</b>

<i>Введите текст сообщения для рассылки всем пользователям:</i>

<blockquote>⚠️ Внимание: Сообщение будет отправлено всем зарегистрированным пользователям!</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    broadcast_text = message.text.strip()
    
    if len(broadcast_text) < 10:
        await message.answer("❌ Сообщение слишком короткое. Минимум 10 символов.")
        return
    
    # Получаем всех активных пользователей
    users = await db.get_all_users()
    active_users = [u for u in users if u['is_active']]
    
    # Показываем превью
    preview_text = f"""
📢 <b>Превью рассылки</b>

<b>Получателей:</b> <code>{len(active_users)}</code>

<b>Текст сообщения:</b>
<blockquote>{broadcast_text}</blockquote>

<i>Подтвердите отправку:</i>
"""
    
    await state.update_data(broadcast_text=broadcast_text, users=active_users)
    
    from keyboards.inline import get_confirmation_keyboard
    await message.answer(
        preview_text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard("broadcast")
    )

@router.callback_query(F.data == "confirm:broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text')
    users = data.get('users', [])
    
    if not broadcast_text or not users:
        await callback.answer("❌ Данные для рассылки не найдены", show_alert=True)
        return
    
    # Начинаем рассылку
    await callback.message.edit_text(
        f"📤 <b>Начинаем рассылку...</b>\n\nОтправляем сообщение {len(users)} пользователям.",
        parse_mode='HTML'
    )
    
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await callback.bot.send_message(
                chat_id=user['telegram_id'],
                text=f"📢 <b>Сообщение от администрации</b>\n\n{broadcast_text}",
                parse_mode='HTML'
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")
    
    # Отчет о рассылке
    result_text = f"""
✅ <b>Рассылка завершена!</b>

<b>Результаты:</b>
<code>📤 Отправлено:</code> <b>{sent_count}</b>
<code>❌ Ошибок:</code> <b>{failed_count}</b>
<code>👥 Всего получателей:</code> <b>{len(users)}</b>

<i>Время завершения: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
"""
    
    await callback.message.edit_text(
        result_text,
        parse_mode='HTML',
                    reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "back_to_admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
⚙️ <b>Админ-панель СК «Алекс»</b>

<i>Добро пожаловать в панель администратора!</i>

<blockquote>Выберите действие:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "manage_training_days")
async def manage_training_days(callback: CallbackQuery):
    """Управление днями тренировок"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
📅 <b>Управление днями тренировок</b>

<i>Функция в разработке.</i>

<b>Планируемый функционал:</b>
<code>▫️</code> Включение/отключение дней недели
<code>▫️</code> Настройка особых дней (праздники)
<code>▫️</code> Массовое редактирование расписания

<blockquote>Скоро будет доступно!</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_schedule")
    )
    await callback.answer()

@router.callback_query(F.data == "manage_training_times")
async def manage_training_times(callback: CallbackQuery):
    """Управление временными слотами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    from config import TRAINING_SLOTS
    
    slots_text = "\n".join([f"<code>▫️ {slot}</code>" for slot in TRAINING_SLOTS])
    
    text = f"""
🕐 <b>Управление временными слотами</b>

<b>Текущие слоты:</b>
{slots_text}

<i>Функция редактирования в разработке.</i>

<b>Планируемый функционал:</b>
<code>▫️</code> Добавление новых слотов
<code>▫️</code> Удаление существующих
<code>▫️</code> Изменение времени слотов

<blockquote>Пока слоты настраиваются в config.py</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_schedule")
    )
    await callback.answer()

@router.callback_query(F.data == "export_schedule")
async def export_schedule(callback: CallbackQuery):
    """Экспорт расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем расписание на месяц
    today = date.today()
    month_later = today + timedelta(days=30)
    
    trainings = await db.get_training_schedule(today, month_later)
    
    if not trainings:
        text = """
📋 <b>Экспорт расписания</b>

<i>На ближайший месяц записей нет.</i>

<blockquote>Нечего экспортировать.</blockquote>
"""
    else:
        # Формируем текст для экспорта
        export_text = f"📋 РАСПИСАНИЕ СК «АЛЕКС» ({today.strftime('%d.%m.%Y')} - {month_later.strftime('%d.%m.%Y')})\n\n"
        
        current_date = None
        for training in trainings:
            if current_date != training['training_date']:
                current_date = training['training_date']
                from utils.formatters import format_date
                export_text += f"\n📆 {format_date(current_date)}\n"
            
            training_type = "🆓 Пробная" if training['is_trial'] else training['training_type']
            export_text += f"• {training['training_time']} - {training_type}\n"
            export_text += f"  👤 {training['user_name']} ({training['user_phone']})\n"
        
        text = f"""
📋 <b>Экспорт расписания</b>

<i>Готов экспорт на {len(trainings)} записей</i>

<blockquote>Данные готовы для копирования:</blockquote>

<pre>{export_text[:1000]}...</pre>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_schedule")
    )
    await callback.answer()

# Обработчики управления расписанием
@router.callback_query(F.data == "schedule_settings")
async def show_schedule_settings(callback: CallbackQuery):
    """Показать настройки расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
⚙️ <b>Настройки расписания</b>

<i>Управление компонентами расписания тренировок</i>

<b>Доступные настройки:</b>
<code>▫️</code> <b>Тренеры</b> - добавление и управление тренерами
<code>▫️</code> <b>Дни недели</b> - настройка рабочих дней
<code>▫️</code> <b>Время</b> - управление временными слотами
<code>▫️</code> <b>Синхронизация</b> - обновление данных из конфига

<blockquote>Выберите что хотите настроить:</blockquote>
"""
    
    from keyboards.inline import get_schedule_settings_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_schedule_settings_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "manage_trainers")
async def show_trainers_management(callback: CallbackQuery):
    """Управление тренерами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
👨‍🏫 <b>Управление тренерами</b>

<i>Добавление и настройка тренеров</i>

<b>Возможности:</b>
<code>▫️</code> Добавить нового тренера
<code>▫️</code> Просмотреть список всех тренеров
<code>▫️</code> Включить/отключить тренера

<blockquote>Тренеры, которые отключены, не будут доступны для записи</blockquote>
"""
    
    from keyboards.inline import get_trainers_management_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_trainers_management_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "list_trainers")
async def show_trainers_list(callback: CallbackQuery):
    """Показать список тренеров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем всех тренеров (не только активных)
    async with aiosqlite.connect(db.db_path) as database:
        database.row_factory = aiosqlite.Row
        cursor = await database.execute('''
            SELECT * FROM active_trainers ORDER BY trainer_name
        ''')
        trainers = [dict(row) for row in await cursor.fetchall()]
    
    if not trainers:
        text = """
👨‍🏫 <b>Список тренеров</b>

<i>Тренеров пока нет в базе данных.</i>

<b>Рекомендуется:</b>
<code>▫️</code> Выполнить синхронизацию данных
<code>▫️</code> Или добавить тренеров вручную

<blockquote>Нажмите "Синхронизация" в настройках расписания</blockquote>
"""
        from keyboards.inline import get_back_keyboard
        keyboard = get_back_keyboard("manage_trainers")
    else:
        text = f"""
👨‍🏫 <b>Список тренеров ({len(trainers)})</b>

<i>Нажмите на тренера чтобы включить/отключить:</i>

<code>✅</code> - активен, доступен для записи
<code>❌</code> - отключен, недоступен для записи
"""
        from keyboards.inline import get_trainer_list_keyboard
        keyboard = get_trainer_list_keyboard(trainers)
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_trainer:"))
async def toggle_trainer(callback: CallbackQuery):
    """Переключить статус тренера"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    trainer_id = callback.data.split(":", 1)[1]
    success = await db.toggle_trainer_status(trainer_id)
    
    if success:
        await callback.answer("✅ Статус тренера изменен", show_alert=True)
        # Обновляем список
        await show_trainers_list(callback)
    else:
        await callback.answer("❌ Ошибка изменения статуса", show_alert=True)

@router.callback_query(F.data == "manage_days")
async def show_days_management(callback: CallbackQuery):
    """Управление днями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
📅 <b>Управление днями недели</b>

<i>Настройка рабочих дней спортклуба</i>

<b>Возможности:</b>
<code>▫️</code> Просмотреть статус всех дней недели
<code>▫️</code> Включить/отключить определенные дни

<blockquote>Отключенные дни не будут доступны для записи</blockquote>
"""
    
    from keyboards.inline import get_days_management_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_days_management_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "list_days")
async def show_days_list(callback: CallbackQuery):
    """Показать список дней"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем все дни
    async with aiosqlite.connect(db.db_path) as database:
        database.row_factory = aiosqlite.Row
        cursor = await database.execute('''
            SELECT * FROM active_days ORDER BY day_of_week
        ''')
        days = [dict(row) for row in await cursor.fetchall()]
    
    if not days:
        text = """
📅 <b>Настройка дней недели</b>

<i>Дни недели не настроены.</i>

<b>Рекомендуется:</b>
<code>▫️</code> Выполнить синхронизацию данных

<blockquote>Нажмите "Синхронизация" в настройках расписания</blockquote>
"""
        from keyboards.inline import get_back_keyboard
        keyboard = get_back_keyboard("manage_days")
    else:
        active_count = sum(1 for day in days if day['is_active'])
        text = f"""
📅 <b>Настройка дней недели</b>

<i>Нажмите на день чтобы включить/отключить:</i>

<b>Активных дней:</b> <code>{active_count}/7</code>

<code>✅</code> - день рабочий, можно записываться
<code>❌</code> - день выходной, запись недоступна
"""
        from keyboards.inline import get_days_list_keyboard
        keyboard = get_days_list_keyboard(days)
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_day:"))
async def toggle_day(callback: CallbackQuery):
    """Переключить статус дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    day_of_week = int(callback.data.split(":", 1)[1])
    success = await db.toggle_day_status(day_of_week)
    
    if success:
        day_names = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]
        await callback.answer(f"✅ Изменен статус дня: {day_names[day_of_week]}", show_alert=True)
        # Обновляем список
        await show_days_list(callback)
    else:
        await callback.answer("❌ Ошибка изменения статуса", show_alert=True)

@router.callback_query(F.data == "manage_time_slots")
async def show_time_slots_management(callback: CallbackQuery):
    """Управление временными слотами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = """
🕐 <b>Управление временными слотами</b>

<i>Настройка времени проведения тренировок</i>

<b>Возможности:</b>
<code>▫️</code> Добавить новое время тренировки
<code>▫️</code> Просмотреть все временные слоты
<code>▫️</code> Включить/отключить определенное время

<blockquote>Отключенные слоты не будут доступны для записи</blockquote>
"""
    
    from keyboards.inline import get_time_slots_management_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_time_slots_management_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "list_time_slots")
async def show_time_slots_list(callback: CallbackQuery):
    """Показать список временных слотов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получаем все временные слоты
    async with aiosqlite.connect(db.db_path) as database:
        database.row_factory = aiosqlite.Row
        cursor = await database.execute('''
            SELECT * FROM active_time_slots ORDER BY sort_order, time_slot
        ''')
        time_slots = [dict(row) for row in await cursor.fetchall()]
    
    if not time_slots:
        text = """
🕐 <b>Временные слоты</b>

<i>Временные слоты не настроены.</i>

<b>Рекомендуется:</b>
<code>▫️</code> Выполнить синхронизацию данных
<code>▫️</code> Или добавить слоты вручную

<blockquote>Нажмите "Синхронизация" в настройках расписания</blockquote>
"""
        from keyboards.inline import get_back_keyboard
        keyboard = get_back_keyboard("manage_time_slots")
    else:
        active_count = sum(1 for slot in time_slots if slot['is_active'])
        text = f"""
🕐 <b>Временные слоты ({len(time_slots)})</b>

<i>Нажмите на время чтобы включить/отключить:</i>

<b>Активных слотов:</b> <code>{active_count}/{len(time_slots)}</code>

<code>✅</code> - время доступно для записи
<code>❌</code> - время отключено
"""
        from keyboards.inline import get_time_slots_list_keyboard
        keyboard = get_time_slots_list_keyboard(time_slots)
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_time_slot:"))
async def toggle_time_slot(callback: CallbackQuery):
    """Переключить статус временного слота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    time_slot = callback.data.split(":", 1)[1]
    success = await db.toggle_time_slot_status(time_slot)
    
    if success:
        await callback.answer(f"✅ Изменен статус времени: {time_slot}", show_alert=True)
        # Обновляем список
        await show_time_slots_list(callback)
    else:
        await callback.answer("❌ Ошибка изменения статуса", show_alert=True)

@router.callback_query(F.data == "sync_schedule_data")
async def sync_schedule_data(callback: CallbackQuery):
    """Синхронизация данных расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Инициализируем таблицы
        await db.init_schedule_tables()
        # Синхронизируем данные из config.py
        await db.sync_config_data()
        
        text = """
🔄 <b>Синхронизация завершена!</b>

<i>Данные успешно обновлены из конфигурации</i>

<blockquote>Теперь вы можете управлять расписанием через интерфейс</blockquote>
"""
        
        await callback.answer("✅ Данные синхронизированы!", show_alert=True)
    except Exception as e:
        text = f"""
❌ <b>Ошибка синхронизации</b>

<i>Произошла ошибка при обновлении данных</i>

<b>Ошибка:</b> <code>{str(e)}</code>

<blockquote>Обратитесь к разработчику</blockquote>
"""
        await callback.answer("❌ Ошибка синхронизации", show_alert=True)
    
    from keyboards.inline import get_back_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("schedule_settings")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_user:"))
async def edit_user_profile(callback: CallbackQuery, state: FSMContext):
    """Редактирование профиля пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    
    # Получаем пользователя
    # TODO: Добавить метод get_user_by_id в базу данных
    
    text = f"""
✏️ <b>Редактирование пользователя</b>

<i>Функция в разработке.</i>

<b>Скоро здесь можно будет редактировать:</b>
<code>▫️</code> Тренера
<code>▫️</code> Звание  
<code>▫️</code> Достижения
<code>▫️</code> Заметки
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_trainings:"))
async def show_user_trainings(callback: CallbackQuery):
    """Показать тренировки пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    
    trainings = await db.get_user_trainings(user_id, limit=20)
    
    text = f"""
📅 <b>Тренировки пользователя</b>

{format_training_list(trainings) if trainings else "Тренировки не найдены"}
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_payments:"))
async def show_user_payments(callback: CallbackQuery):
    """Показать платежи пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    
    # TODO: Добавить метод get_user_payments в базу данных
    
    text = """
💳 <b>Платежи пользователя</b>

<i>Функция в разработке.</i>

<blockquote>Скоро здесь будет отображаться история платежей.</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_admin_panel")
    )
    await callback.answer()
