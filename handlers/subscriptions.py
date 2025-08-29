"""
Обработчики покупки абонементов
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from database.models import db
from keyboards.inline import (
    get_subscription_keyboard, get_confirmation_keyboard, 
    get_payment_keyboard, get_main_menu_keyboard
)
from utils.payments import payment_service
from utils.formatters import format_subscription_offer
from config import SUBSCRIPTION_PRICES, ADMIN_IDS

router = Router()

@router.callback_query(F.data == "buy_subscription")
async def show_subscriptions(callback: CallbackQuery):
    """Показать доступные абонементы"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Проверяем активный абонемент
    active_subscription = await db.get_active_subscription(user['id'])
    
    if active_subscription:
        text = f"""
ℹ️ <b>У вас уже есть активный абонемент!</b>

{format_subscription_offer(active_subscription['subscription_type'])}

Вы можете купить новый абонемент, который начнет действовать после окончания текущего.
"""
    else:
        text = """
💳 <b>Выберите абонемент</b>

<blockquote>Доступные варианты тренировок:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_subscription_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("subscription:"))
async def process_subscription_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора абонемента"""
    subscription_type = callback.data.split(":")[1]
    
    if subscription_type not in SUBSCRIPTION_PRICES:
        await callback.answer("❌ Неизвестный тип абонемента", show_alert=True)
        return
    
    await state.update_data(subscription_type=subscription_type)
    
    subscription_info = SUBSCRIPTION_PRICES[subscription_type]
    
    text = f"""
💳 <b>Подтверждение покупки</b>

{format_subscription_offer(subscription_type)}

<b>К оплате:</b> <code>{subscription_info['price']}₽</code>

<blockquote>Подтвердите покупку абонемента:</blockquote>
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard("buy_subscription")
    )
    await callback.answer()

@router.callback_query(F.data == "confirm:buy_subscription")
async def confirm_subscription_purchase(callback: CallbackQuery, state: FSMContext):
    """Подтверждение покупки абонемента"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    
    if not user or 'subscription_type' not in data:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        return
    
    subscription_type = data['subscription_type']
    subscription_info = SUBSCRIPTION_PRICES[subscription_type]
    
    # Создаем платеж
    payment_description = f"Абонемент: {subscription_info['name']}"
    payment_data = await payment_service.create_payment(
        amount=subscription_info['price'],
        description=payment_description,
        user_telegram_id=callback.from_user.id
    )
    
    if not payment_data:
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            "❌ <b>Ошибка создания платежа</b>\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        await callback.answer()
        return
    
    # Сохраняем информацию о платеже
    await db.add_payment(
        user_id=user['id'],
        payment_id=payment_data['id'],
        amount=subscription_info['price'],
        description=payment_description,
        payment_type='subscription'
    )
    
    # Сохраняем данные для завершения покупки
    await state.update_data(
        payment_id=payment_data['id'],
        user_id=user['id']
    )
    
    text = f"""
💳 <b>Оплата абонемента</b>

{format_subscription_offer(subscription_type)}

💰 <b>К оплате:</b> {subscription_info['price']}₽
🆔 <b>Номер платежа:</b> {payment_data['id']}

Нажмите кнопку "Оплатить" для перехода к оплате:
"""
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(payment_data['confirmation_url'])
    )
    await callback.answer()

@router.callback_query(F.data == "payment_check")
async def check_payment_status(callback: CallbackQuery, state: FSMContext):
    """Проверка статуса платежа"""
    data = await state.get_data()
    
    if 'payment_id' not in data:
        await callback.answer("❌ Данные о платеже не найдены", show_alert=True)
        return
    
    payment_id = data['payment_id']
    
    # Проверяем статус платежа
    payment_status = await payment_service.check_payment_status(payment_id)
    
    if payment_status == 'succeeded':
        # Платеж успешен - активируем абонемент
        await activate_subscription(callback, state, data)
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

async def activate_subscription(callback: CallbackQuery, state: FSMContext, data: dict):
    """Активация абонемента после успешной оплаты"""
    subscription_type = data['subscription_type']
    user_id = data['user_id']
    payment_id = data['payment_id']
    
    subscription_info = SUBSCRIPTION_PRICES[subscription_type]
    
    # Определяем даты начала и окончания
    start_date = datetime.now().date()
    
    # Абонемент на месяц
    if subscription_type in ['twice_week', 'thrice_week']:
        end_date = start_date + timedelta(days=30)
    else:
        # Разовые тренировки действуют 3 месяца
        end_date = start_date + timedelta(days=90)
    
    try:
        # Добавляем абонемент в базу
        await db.add_subscription(
            user_id=user_id,
            subscription_type=subscription_type,
            price=subscription_info['price'],
            sessions_total=subscription_info['sessions'],
            start_date=start_date,
            end_date=end_date,
            payment_id=payment_id
        )
        
        # Обновляем статус платежа
        await db.update_payment_status(payment_id, 'succeeded')
        
        text = f"""
✅ <b>Абонемент успешно активирован!</b>

🎉 Поздравляем с покупкой!

💳 <b>Ваш абонемент:</b>
{format_subscription_offer(subscription_type)}

📅 <b>Действует с:</b> {start_date.strftime('%d.%m.%Y')}
📅 <b>Действует до:</b> {end_date.strftime('%d.%m.%Y')}
🏃‍♂️ <b>Доступно тренировок:</b> {subscription_info['sessions']}

Теперь вы можете записываться на тренировки! 💪
"""
        
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        
        # Уведомляем админов
        await notify_admins_about_subscription(callback, subscription_type, subscription_info)
        
    except Exception as e:
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        has_trial = await db.has_trial_training(user['id']) if user else False
        
        await callback.message.edit_text(
            "❌ <b>Ошибка активации абонемента</b>\n\n"
            "Платеж прошел успешно, но произошла ошибка при активации абонемента. "
            "Обратитесь к администратору.",
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(show_trial=not has_trial)
        )
        print(f"Ошибка активации абонемента: {e}")
    
    await state.clear()
    await callback.answer()

async def notify_admins_about_subscription(callback: CallbackQuery, subscription_type: str, subscription_info: dict):
    """Уведомление админов о новой покупке"""
    if not ADMIN_IDS:
        return
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    admin_notification = f"""
💳 <b>Новая покупка абонемента!</b>

👤 <b>Пользователь:</b> {user['name']}
📱 <b>Телефон:</b> {user['phone']}
💳 <b>Абонемент:</b> {subscription_info['name']}
💰 <b>Сумма:</b> {subscription_info['price']}₽
📅 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
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
