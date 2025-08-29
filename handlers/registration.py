"""
Обработчики регистрации пользователей
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date
import re

from database.models import db
from keyboards.inline import get_user_type_keyboard, get_main_menu_keyboard
from config import ADMIN_IDS

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_user_type = State()
    waiting_for_parent_name = State()
    waiting_for_child_name = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_birth_date = State()

@router.callback_query(F.data.startswith("user_type:"))
async def process_user_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа пользователя"""
    user_type = callback.data.split(":")[1]
    await state.update_data(user_type=user_type)
    
    user_type_text = "Спортсмен" if user_type == "athlete" else "Родитель"
    name_prompt = "Ваше имя" if user_type == "athlete" else "Имя ребенка, который будет заниматься"
    
    if user_type == "parent":
        text = f"""
✅ <b>Вы выбрали:</b> <code>{user_type_text}</code>

<blockquote>Сначала введите ваше имя (родителя):</blockquote>
"""
        await callback.message.edit_text(text, parse_mode='HTML')
        await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await state.set_state(RegistrationStates.waiting_for_parent_name)
    else:
        text = f"""
✅ <b>Вы выбрали:</b> <code>{user_type_text}</code>

<blockquote>Теперь введите {name_prompt}:</blockquote>
"""
        await callback.message.edit_text(text, parse_mode='HTML')
        await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await state.set_state(RegistrationStates.waiting_for_name)
    
    await callback.answer()

@router.message(RegistrationStates.waiting_for_parent_name)
async def process_parent_name(message: Message, state: FSMContext):
    """Обработка ввода имени родителя"""
    parent_name = message.text.strip()
    
    if len(parent_name) < 2:
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать минимум 2 символа.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    if not re.match(r"^[а-яёА-ЯЁa-zA-Z\s]+$", parent_name):
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать только буквы.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    await state.update_data(parent_name=parent_name)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    
    text = f"""
✅ <b>Вы выбрали:</b> <code>родитель</code>
✅ <b>Ваше имя:</b> <code>{parent_name}</code>

<blockquote>Теперь введите имя ребенка, который будет заниматься:</blockquote>
"""
    
    # Редактируем исходное сообщение
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=data.get('chat_id'),
            message_id=data.get('message_id'),
            parse_mode='HTML'
        )
    except:
        # Если не удалось отредактировать, отправляем новое
        sent_message = await message.answer(text, parse_mode='HTML')
        await state.update_data(message_id=sent_message.message_id, chat_id=sent_message.chat.id)
    
    await state.set_state(RegistrationStates.waiting_for_child_name)

@router.message(RegistrationStates.waiting_for_child_name)
async def process_child_name(message: Message, state: FSMContext):
    """Обработка ввода имени ребенка"""
    child_name = message.text.strip()
    
    if len(child_name) < 2:
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать минимум 2 символа.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    if not re.match(r"^[а-яёА-ЯЁa-zA-Z\s]+$", child_name):
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать только буквы.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    await state.update_data(name=child_name)  # Сохраняем как основное имя для записи
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    
    text = f"""
✅ <b>Вы выбрали:</b> <code>родитель</code>
✅ <b>Ваше имя:</b> <code>{data['parent_name']}</code>
✅ <b>Имя ребенка:</b> <code>{child_name}</code>

<blockquote>Теперь введите номер телефона в формате +7XXXXXXXXXX:</blockquote>
"""
    
    # Редактируем исходное сообщение
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=data.get('chat_id'),
            message_id=data.get('message_id'),
            parse_mode='HTML'
        )
    except:
        # Если не удалось отредактировать, отправляем новое
        sent_message = await message.answer(text, parse_mode='HTML')
        await state.update_data(message_id=sent_message.message_id, chat_id=sent_message.chat.id)
    
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    name = message.text.strip()
    
    if len(name) < 2:
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать минимум 2 символа.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    if not re.match(r"^[а-яёА-ЯЁa-zA-Z\s]+$", name):
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Имя должно содержать только буквы.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    await state.update_data(name=name)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    user_type_text = "спортсмен" if data['user_type'] == 'athlete' else "родитель"
    
    text = f"""
✅ <b>Вы выбрали:</b> <code>{user_type_text}</code>
✅ <b>Имя:</b> <code>{name}</code>

<blockquote>Теперь введите номер телефона в формате +7XXXXXXXXXX:</blockquote>
"""
    
    # Редактируем исходное сообщение
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=data.get('chat_id'),
            message_id=data.get('message_id'),
            parse_mode='HTML'
        )
    except:
        # Если не удалось отредактировать, отправляем новое
        sent_message = await message.answer(text, parse_mode='HTML')
        await state.update_data(message_id=sent_message.message_id, chat_id=sent_message.chat.id)
    
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = re.sub(r'[^\d+]', '', message.text.strip())
    
    # Проверяем формат телефона
    if not re.match(r'^(\+7|8)\d{10}$', phone):
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Неверный формат телефона.</i>

<blockquote>Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX:</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    # Приводим к единому формату +7
    if phone.startswith('8'):
        phone = '+7' + phone[1:]
    
    await state.update_data(phone=phone)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    user_type_text = "спортсмен" if data['user_type'] == 'athlete' else "родитель"
    birth_prompt = "спортсмена" if data['user_type'] == 'athlete' else "ребенка"
    
    if data['user_type'] == 'parent':
        text = f"""
✅ <b>Вы выбрали:</b> <code>родитель</code>
✅ <b>Ваше имя:</b> <code>{data['parent_name']}</code>
✅ <b>Имя ребенка:</b> <code>{data['name']}</code>
✅ <b>Телефон:</b> <code>{phone}</code>

<blockquote>Теперь введите дату рождения {birth_prompt} в формате ДД.ММ.ГГГГ (например, 15.06.2005):</blockquote>
"""
    else:
        text = f"""
✅ <b>Вы выбрали:</b> <code>{user_type_text}</code>
✅ <b>Имя:</b> <code>{data['name']}</code>
✅ <b>Телефон:</b> <code>{phone}</code>

<blockquote>Теперь введите дату рождения {birth_prompt} в формате ДД.ММ.ГГГГ (например, 15.06.2005):</blockquote>
"""
    
    # Редактируем исходное сообщение
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=data.get('chat_id'),
            message_id=data.get('message_id'),
            parse_mode='HTML'
        )
    except:
        # Если не удалось отредактировать, отправляем новое
        sent_message = await message.answer(text, parse_mode='HTML')
        await state.update_data(message_id=sent_message.message_id, chat_id=sent_message.chat.id)
    
    await state.set_state(RegistrationStates.waiting_for_birth_date)

@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка ввода даты рождения"""
    birth_date_str = message.text.strip()
    
    try:
        # Парсим дату
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        
        # Проверяем, что дата не в будущем
        if birth_date > date.today():
            error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Дата рождения не может быть в будущем.</i>

<blockquote>Попробуйте еще раз:</blockquote>
"""
            await message.answer(error_text, parse_mode='HTML')
            return
        
        # Проверяем возраст (от 3 до 80 лет)
        age = (date.today() - birth_date).days // 365
        if age < 3 or age > 80:
            error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Возраст должен быть от 3 до 80 лет.</i>

<blockquote>Проверьте дату рождения:</blockquote>
"""
            await message.answer(error_text, parse_mode='HTML')
            return
        
    except ValueError:
        error_text = f"""
❌ <b>Ошибка ввода</b>

<i>Неверный формат даты.</i>

<blockquote>Используйте формат ДД.ММ.ГГГГ (например, 15.06.2005):</blockquote>
"""
        await message.answer(error_text, parse_mode='HTML')
        return
    
    await state.update_data(birth_date=birth_date)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    # Завершаем регистрацию
    await complete_registration(message, state)

async def complete_registration(message: Message, state: FSMContext):
    """Завершение регистрации"""
    data = await state.get_data()
    
    try:
        # Проверяем, не зарегистрирован ли уже пользователь
        existing_user = await db.get_user_by_telegram_id(message.from_user.id)
        if existing_user:
            await message.answer(
                "ℹ️ Вы уже зарегистрированы в системе!",
                reply_markup=get_main_menu_keyboard(message.from_user.id in ADMIN_IDS)
            )
            await state.clear()
            return
        
        # Добавляем пользователя в базу данных
        parent_telegram_id = message.from_user.id if data['user_type'] == 'parent' else None
        
        user_id = await db.add_user(
            telegram_id=message.from_user.id,
            user_type=data['user_type'],
            name=data['name'],
            phone=data['phone'],
            birth_date=data['birth_date'],
            parent_telegram_id=parent_telegram_id
        )
        
        user_type_text = "Спортсмена" if data['user_type'] == 'athlete' else "Родителя"
        
        # Отправляем подтверждение
        if data['user_type'] == 'parent':
            confirmation_text = f"""
🎉 <b>Регистрация завершена!</b>

<i>Добро пожаловать в СК «Алекс»!</i>

<b>Данные родителя:</b>
<b>Ваше имя:</b> <code>{data['parent_name']}</code>
<b>Телефон:</b> <code>{data['phone']}</code>

<b>Данные ребенка:</b>
<b>Имя ребенка:</b> <code>{data['name']}</code>
<b>Дата рождения:</b> <code>{data['birth_date'].strftime('%d.%m.%Y')}</code>

<b>Теперь вы можете:</b>
<code>▫️</code> Купить абонемент для ребенка
<code>▫️</code> Записать ребенка на пробную тренировку
<code>▫️</code> Планировать тренировки

<blockquote>Желаем успешных тренировок вашему ребенку!</blockquote>
"""
        else:
            confirmation_text = f"""
🎉 <b>Регистрация завершена!</b>

<i>Добро пожаловать в СК «Алекс»!</i>

<b>Ваши данные:</b>
<b>Тип:</b> <code>{user_type_text}</code>
<b>Имя:</b> <code>{data['name']}</code>
<b>Телефон:</b> <code>{data['phone']}</code>
<b>Дата рождения:</b> <code>{data['birth_date'].strftime('%d.%m.%Y')}</code>

<b>Теперь вы можете:</b>
<code>▫️</code> Купить абонемент
<code>▫️</code> Записаться на пробную тренировку
<code>▫️</code> Планировать тренировки

<blockquote>Желаем успешных тренировок!</blockquote>
"""
        
        # Сначала редактируем исходное сообщение с финальной информацией
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                text=confirmation_text,
                chat_id=data.get('chat_id'),
                message_id=data.get('message_id'),
                parse_mode='HTML',
                reply_markup=get_main_menu_keyboard()
            )
        except:
            # Если не удалось отредактировать, отправляем новое
            await message.answer(
                confirmation_text,
                parse_mode='HTML',
                reply_markup=get_main_menu_keyboard()
            )
        
        # Уведомляем админов о новой регистрации
        await notify_admins_about_new_user(message, data, user_id)
        
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже или обратитесь к администратору."
        )
        print(f"Ошибка регистрации: {e}")
    
    await state.clear()

async def notify_admins_about_new_user(message: Message, user_data: dict, user_id: int):
    """Уведомление админов о новом пользователе"""
    if not ADMIN_IDS:
        return
    
    user_type_text = "Спортсмен" if user_data['user_type'] == 'athlete' else "Родитель"
    
    admin_notification = f"""
👥 <b>Новая регистрация!</b>

🆔 <b>User ID:</b> {user_id}
📱 <b>Telegram:</b> @{message.from_user.username or 'нет username'}
👤 <b>Тип:</b> {user_type_text}
👨‍💼 <b>Имя:</b> {user_data['name']}
📱 <b>Телефон:</b> {user_data['phone']}
🎂 <b>Дата рождения:</b> {user_data['birth_date'].strftime('%d.%m.%Y')}
📅 <b>Время регистрации:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу {admin_id}: {e}")
