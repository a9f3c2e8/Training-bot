"""
Обработчики записи на тренировки
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, date, timedelta

from database.models import db
from keyboards.inline import (
    get_training_type_keyboard, get_trainer_keyboard, get_date_keyboard, get_time_keyboard,
    get_confirmation_keyboard, get_payment_keyboard, get_main_menu_keyboard,
    get_back_keyboard
)
from utils.payments import payment_service
from utils.formatters import format_training_list, format_subscription_offer
from config import SUBSCRIPTION_PRICES, ADMIN_IDS, TRAINERS

router = Router()

@router.callback_query(F.data == "book_training")
async def show_training_types(callback: CallbackQuery, state: FSMContext):
    """Показать типы тренировок"""
    await state.clear()
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
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

@router.callback_query(F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки"""
    training_type = callback.data.split(":")[1]
    await state.update_data(training_type=training_type)
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Проверяем абонемент для групповых тренировок
    if training_type == "group":
        subscription = await db.get_active_subscription(user['id'])
        
        if not subscription:
            text = """
❌ <b>Нет активного абонемента</b>

Для записи на групповые тренировки необходим активный абонемент.

Хотите купить абонемент?
"""
            await callback.message.edit_text(
                text,
                parse_mode='HTML',
                reply_markup=get_back_keyboard("buy_subscription")
            )
            await callback.answer()
            return
        
        # Проверяем оставшиеся тренировки
        sessions_left = subscription['sessions_total'] - subscription['sessions_used']
        if sessions_left <= 0:
            text = f"""
❌ <b>Тренировки закончились</b>

В вашем абонементе не осталось доступных тренировок.

{format_subscription_offer(subscription['subscription_type'])}

Купите новый абонемент для продолжения тренировок.
"""
            await callback.message.edit_text(
                text,
                parse_mode='HTML',
                reply_markup=get_back_keyboard("buy_subscription")
            )
            await callback.answer()
            return
        
        await state.update_data(subscription_id=subscription['id'])
    
    # Для индивидуальной тренировки сначала выбираем тренера
    if training_type == "individual":
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
        return
    
    # Для групповой тренировки сразу переходим к выбору даты
    training_type_text = "групповую тренировку"
    
    text = f"""
📅 <b>Выберите дату</b>

<i>Запись на {training_type_text}</i>

<blockquote>Выберите удобную дату:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_date_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("trainer:"))
async def process_trainer_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора тренера для индивидуальной тренировки"""
    trainer_id = callback.data.split(":")[1]
    
    if trainer_id not in TRAINERS:
        await callback.answer("❌ Неизвестный тренер", show_alert=True)
        return
    
    trainer_info = TRAINERS[trainer_id]
    await state.update_data(
        selected_trainer_id=trainer_id,
        selected_trainer_name=trainer_info['name']
    )
    
    text = f"""
📅 <b>Выбор даты</b>

<i>Индивидуальная тренировка с тренером</i>

👨‍🏫 <b>Тренер:</b> {trainer_info['emoji']} {trainer_info['name']}
🎯 <b>Специализация:</b> <i>{trainer_info['specialization']}</i>
⏱️ <b>Опыт:</b> <code>{trainer_info['experience']}</code>

<blockquote>Выберите удобную дату:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_date_keyboard(back_to="back_to_trainer_selection")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("date:"))
async def process_date_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    selected_date = callback.data.split(":")[1]
    await state.update_data(selected_date=selected_date)
    
    data = await state.get_data()
    training_type = data.get('training_type')
    
    training_type_text = "групповую тренировку" if training_type == "group" else "индивидуальную тренировку"
    date_obj = datetime.fromisoformat(selected_date).date()
    
    text = f"""
🕐 <b>Выберите время</b>

Запись на {training_type_text}
📅 {date_obj.strftime('%d.%m.%Y')}

Выберите удобное время:
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_time_keyboard(selected_date)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("time:"))
async def process_time_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    # Разбираем callback_data правильно, учитывая что время содержит двоеточие
    parts = callback.data.split(":")
    selected_date = parts[1]  # дата
    selected_time = ":".join(parts[2:])  # время (может содержать двоеточие)
    await state.update_data(selected_time=selected_time)
    
    data = await state.get_data()
    training_type = data.get('training_type')
    
    # Формируем информацию о тренировке
    date_obj = datetime.fromisoformat(selected_date).date()
    
    # Определяем тип и стоимость
    if training_type == "trial":
        training_type_text = "Пробная тренировка"
        price_text = "БЕСПЛАТНО"
        trainer_text = ""
    elif training_type == "group":
        training_type_text = "Групповая тренировка"
        price_text = "Включено в абонемент"
        trainer_text = ""
    else:
        training_type_text = "Индивидуальная тренировка"
        price = SUBSCRIPTION_PRICES['individual']['price']
        price_text = f"{price}₽"
        
        # Добавляем информацию о тренере для индивидуальной тренировки
        selected_trainer_name = data.get('selected_trainer_name')
        if selected_trainer_name:
            trainer_text = f"\n👨‍🏫 <b>Тренер:</b> {selected_trainer_name}"
        else:
            trainer_text = ""
    
    text = f"""
✅ <b>Подтверждение записи</b>

🏃‍♂️ <b>Тип:</b> {training_type_text}
📅 <b>Дата:</b> {date_obj.strftime('%d.%m.%Y')}
🕐 <b>Время:</b> {selected_time}{trainer_text}
💰 <b>Стоимость:</b> {price_text}

<blockquote>Подтвердите запись на тренировку:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard("book_training")
    )
    await callback.answer()

@router.callback_query(F.data == "confirm:book_training")
async def confirm_training_booking(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи на тренировку"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    
    if not user or 'training_type' not in data:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    training_type = data['training_type']
    selected_date = datetime.fromisoformat(data['selected_date']).date()
    selected_time = data['selected_time']
    
    if training_type == "trial":
        # Пробная тренировка - бесплатная
        await book_trial_training_final(callback, state, user, selected_date, selected_time)
    elif training_type == "group":
        # Групповая тренировка - используем абонемент
        await book_group_training(callback, state, user, selected_date, selected_time, data)
    else:
        # Индивидуальная тренировка - требует оплаты
        await book_individual_training(callback, state, user, selected_date, selected_time)

async def book_trial_training_final(callback: CallbackQuery, state: FSMContext, user: dict,
                                   selected_date: date, selected_time: str):
    """Запись на пробную тренировку"""
    try:
        # Добавляем пробную тренировку
        training_id = await db.add_training(
            user_id=user['id'],
            training_type="Пробная тренировка",
            training_date=selected_date,
            training_time=selected_time,
            is_trial=True
        )
        
        text = f"""
✅ <b>Запись на пробную тренировку подтверждена!</b>

🆓 <b>Пробная тренировка</b>
📅 {selected_date.strftime('%d.%m.%Y')} в {selected_time}

<b>Детали:</b>
<code>▫️</code> Стоимость: БЕСПЛАТНО
<code>▫️</code> Длительность: 60 минут
<code>▫️</code> Формат: Групповая тренировка

📍 <b>Адрес:</b> указать адрес зала
👨‍🏫 <b>Тренер:</b> будет назначен

⏰ За час до тренировки вам придет напоминание.

<blockquote>Ждем вас на первой тренировке! 🏃‍♂️</blockquote>
"""
        
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        
        # Уведомляем админов
        await notify_admins_about_training(callback, user, "Пробная", selected_date, selected_time)
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка записи</b>\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        print(f"Ошибка записи на пробную тренировку: {e}")
    
    await state.clear()
    await callback.answer()

async def book_group_training(callback: CallbackQuery, state: FSMContext, user: dict, 
                            selected_date: date, selected_time: str, data: dict):
    """Запись на групповую тренировку"""
    try:
        # Добавляем тренировку
        training_id = await db.add_training(
            user_id=user['id'],
            training_type="Групповая тренировка",
            training_date=selected_date,
            training_time=selected_time,
            is_trial=False
        )
        
        # Списываем тренировку с абонемента (эта логика должна быть в базе данных)
        # TODO: Реализовать списание тренировки с абонемента
        
        text = f"""
✅ <b>Запись подтверждена!</b>

🏃‍♂️ <b>Групповая тренировка</b>
📅 {selected_date.strftime('%d.%m.%Y')} в {selected_time}

📍 Адрес зала: указать адрес
👨‍🏫 Тренер: будет назначен

⏰ За час до тренировки вам придет напоминание.

Желаем продуктивной тренировки! 💪
"""
        
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        
        # Уведомляем админов
        await notify_admins_about_training(callback, user, "Групповая", selected_date, selected_time)
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ <b>Ошибка записи</b>\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        print(f"Ошибка записи на групповую тренировку: {e}")
    
    await state.clear()
    await callback.answer()

async def book_individual_training(callback: CallbackQuery, state: FSMContext, user: dict,
                                 selected_date: date, selected_time: str):
    """Запись на индивидуальную тренировку с оплатой"""
    price = SUBSCRIPTION_PRICES['individual']['price']
    
    # Получаем информацию о выбранном тренере
    data = await state.get_data()
    selected_trainer_name = data.get('selected_trainer_name', 'Не указан')
    
    # Создаем платеж
    payment_description = f"Индивидуальная тренировка с {selected_trainer_name} на {selected_date.strftime('%d.%m.%Y')} в {selected_time}"
    payment_data = await payment_service.create_payment(
        amount=price,
        description=payment_description,
        user_telegram_id=callback.from_user.id
    )
    
    if not payment_data:
        await callback.message.edit_text(
            "❌ <b>Ошибка создания платежа</b>\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Сохраняем информацию о платеже
    await db.add_payment(
        user_id=user['id'],
        payment_id=payment_data['id'],
        amount=price,
        description=payment_description,
        payment_type='individual_training'
    )
    
    # Сохраняем данные для завершения бронирования
    await state.update_data(
        payment_id=payment_data['id'],
        user_id=user['id']
    )
    
    text = f"""
💳 <b>Оплата индивидуальной тренировки</b>

🏃‍♂️ <b>Индивидуальная тренировка</b>
📅 {selected_date.strftime('%d.%m.%Y')} в {selected_time}
💰 <b>К оплате:</b> {price}₽
🆔 <b>Номер платежа:</b> {payment_data['id']}

Нажмите кнопку "Оплатить" для перехода к оплате:
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(payment_data['confirmation_url'], "individual")
    )
    await callback.answer()

@router.callback_query(F.data == "payment_check_individual")
async def check_individual_training_payment(callback: CallbackQuery, state: FSMContext):
    """Проверка оплаты индивидуальной тренировки"""
    data = await state.get_data()
    
    if 'payment_id' not in data:
        await callback.answer("❌ Данные о платеже не найдены", show_alert=True)
        return
    
    payment_id = data['payment_id']
    payment_status = await payment_service.check_payment_status(payment_id)
    
    if payment_status == 'succeeded':
        # Платеж успешен - записываем тренировку
        await finalize_individual_training_booking(callback, state, data)
    elif payment_status == 'pending':
        await callback.answer(
            "⏳ Платеж еще обрабатывается. Попробуйте через несколько минут.",
            show_alert=True
        )
    elif payment_status == 'canceled':
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            "❌ <b>Платеж отменен</b>\n\n"
            "Вы можете попробовать еще раз.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        await state.clear()
        await callback.answer()
    else:
        await callback.answer(
            "❌ Платеж не найден или произошла ошибка. Обратитесь к администратору.",
            show_alert=True
        )

async def finalize_individual_training_booking(callback: CallbackQuery, state: FSMContext, data: dict):
    """Финализация записи на индивидуальную тренировку после оплаты"""
    try:
        user_id = data['user_id']
        payment_id = data['payment_id']
        selected_date = datetime.fromisoformat(data['selected_date']).date()
        selected_time = data['selected_time']
        selected_trainer_name = data.get('selected_trainer_name', 'Не указан')
        
        # Добавляем тренировку в базу данных
        training_id = await db.add_training(
            user_id=user_id,
            training_type="Индивидуальная тренировка",
            training_date=selected_date,
            training_time=selected_time,
            trainer=selected_trainer_name,
            is_trial=False,
            payment_id=payment_id
        )
        
        # Обновляем статус платежа
        await db.update_payment_status(payment_id, 'succeeded')
        
        text = f"""
✅ <b>Индивидуальная тренировка забронирована!</b>

🎉 <b>Оплата прошла успешно!</b>

🏃‍♂️ <b>Детали тренировки:</b>
📅 <b>Дата:</b> {selected_date.strftime('%d.%m.%Y')}
🕐 <b>Время:</b> {selected_time}
👨‍🏫 <b>Тренер:</b> {selected_trainer_name}
💰 <b>Стоимость:</b> {SUBSCRIPTION_PRICES['individual']['price']}₽

📍 <b>Адрес зала:</b> указать адрес зала
⏰ <b>За час до тренировки вам придет напоминание.</b>

<blockquote>Желаем продуктивной тренировки! 💪</blockquote>
"""
        
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        
        # Уведомляем админов
        await notify_admins_about_training(callback, user, f"Индивидуальная с {selected_trainer_name}", selected_date, selected_time)
        
    except Exception as e:
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            "❌ <b>Ошибка записи тренировки</b>\n\n"
            "Платеж прошел успешно, но произошла ошибка при записи. "
            "Обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        print(f"Ошибка записи индивидуальной тренировки: {e}")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "trial_training")
async def book_trial_training(callback: CallbackQuery, state: FSMContext):
    """Запись на пробную тренировку"""
    await state.clear()
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Проверяем, была ли уже пробная тренировка
    # TODO: Добавить проверку в базу данных на пробные тренировки
    
    text = f"""
🆓 <b>Пробная тренировка</b>

<i>Отличная возможность познакомиться с СК «Алекс»!</i>

<b>Стоимость:</b> <code>БЕСПЛАТНО</code>
<b>Длительность:</b> <code>60 минут</code>  
<b>Формат:</b> <code>Групповая тренировка</code>
<b>Тренер:</b> <code>Опытный инструктор</code>

<b>Что включено:</b>
<code>▫️</code> Знакомство с залом и оборудованием
<code>▫️</code> Базовые упражнения и техника
<code>▫️</code> Консультация тренера
<code>▫️</code> Рекомендации по программе тренировок

<blockquote>Выберите удобную дату:</blockquote>
"""
    
    await state.update_data(training_type="trial")
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_date_keyboard(back_to="back_to_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "my_trainings")
async def show_my_trainings(callback: CallbackQuery):
    """Показать мои тренировки"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Получаем тренировки пользователя
    trainings = await db.get_user_trainings(user['id'], limit=20)
    
    # Проверяем, есть ли у пользователя пробная тренировка
    has_trial = await db.has_trial_training(user['id'])
    
    text = format_training_list(trainings)
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
    )
    await callback.answer()

async def notify_admins_about_training(callback: CallbackQuery, user: dict, training_type: str,
                                     training_date: date, training_time: str):
    """Уведомление админов о новой записи"""
    if not ADMIN_IDS:
        return
    
    admin_notification = f"""
📅 <b>Новая запись на тренировку!</b>

👤 <b>Пользователь:</b> {user['name']}
📱 <b>Телефон:</b> {user['phone']}
🏃‍♂️ <b>Тип:</b> {training_type} тренировка
📅 <b>Дата:</b> {training_date.strftime('%d.%m.%Y')}
🕐 <b>Время:</b> {training_time}
📅 <b>Время записи:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу {admin_id}: {e}")
