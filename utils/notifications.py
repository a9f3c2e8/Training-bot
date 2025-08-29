"""
Система уведомлений
"""
import asyncio
from datetime import datetime, timedelta, date
from typing import List
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import db
from config import NOTIFICATION_SETTINGS

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    def start_scheduler(self):
        """Запуск планировщика уведомлений"""
        # Проверка дней рождения каждый день в 10:00
        self.scheduler.add_job(
            self.send_birthday_notifications,
            'cron',
            hour=10,
            minute=0,
            id='birthday_notifications'
        )
        
        # Проверка неактивных пользователей каждый понедельник в 12:00
        self.scheduler.add_job(
            self.send_inactive_user_notifications,
            'cron',
            day_of_week='mon',
            hour=12,
            minute=0,
            id='inactive_user_notifications'
        )
        
        # Напоминание о тренировках каждый час
        self.scheduler.add_job(
            self.send_training_reminders,
            'cron',
            minute=0,
            id='training_reminders'
        )
        
        self.scheduler.start()

    async def send_birthday_notifications(self):
        """Отправка уведомлений о днях рождения"""
        try:
            users = await db.get_users_for_birthday_notification(
                NOTIFICATION_SETTINGS['birthday_reminder_days']
            )
            
            for user in users:
                message = self._format_birthday_message(user)
                await self._send_notification(user['telegram_id'], message)
                
        except Exception as e:
            print(f"Ошибка отправки уведомлений о днях рождения: {e}")

    async def send_inactive_user_notifications(self):
        """Отправка уведомлений неактивным пользователям"""
        try:
            users = await db.get_inactive_users(
                NOTIFICATION_SETTINGS['inactive_reminder_days']
            )
            
            for user in users:
                message = self._format_inactive_user_message(user)
                await self._send_notification(user['telegram_id'], message)
                
        except Exception as e:
            print(f"Ошибка отправки уведомлений неактивным пользователям: {e}")

    async def send_training_reminders(self):
        """Отправка напоминаний о тренировках"""
        try:
            # Получаем тренировки на ближайший час
            reminder_time = datetime.now() + timedelta(
                hours=NOTIFICATION_SETTINGS['training_reminder_hours']
            )
            
            # Здесь нужно добавить метод в базу данных для получения тренировок на определенное время
            # trainings = await db.get_trainings_for_reminder(reminder_time)
            
            # Пока заглушка
            trainings = []
            
            for training in trainings:
                user = await db.get_user_by_telegram_id(training['user_telegram_id'])
                if user:
                    message = self._format_training_reminder_message(training, user)
                    await self._send_notification(user['telegram_id'], message)
                    
        except Exception as e:
            print(f"Ошибка отправки напоминаний о тренировках: {e}")

    async def send_custom_notification(self, user_telegram_id: int, message: str):
        """Отправка кастомного уведомления"""
        await self._send_notification(user_telegram_id, message)

    async def _send_notification(self, telegram_id: int, message: str):
        """Отправка уведомления пользователю"""
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {telegram_id}: {e}")

    def _format_birthday_message(self, user: dict) -> str:
        """Форматирование сообщения о дне рождения"""
        return f"""
🎉 <b>Скоро день рождения!</b>

Привет, {user['name']}! 

Через неделю у вас день рождения! 🎂

В честь этого события мы дарим вам <b>скидку 20%</b> на любой абонемент!

Используйте промокод: <code>BIRTHDAY20</code>

🎁 Скидка действует до конца месяца.
"""

    def _format_inactive_user_message(self, user: dict) -> str:
        """Форматирование сообщения для неактивного пользователя"""
        return f"""
😊 <b>Мы скучаем по вам!</b>

Привет, {user['name']}! 

Давно вас не видели в нашей спортивной школе.

Возвращайтесь к тренировкам со скидкой <b>30%</b> на первый месяц!

Используйте промокод: <code>COMEBACK30</code>

💪 Ждем вас снова в зале!
"""

    def _format_training_reminder_message(self, training: dict, user: dict) -> str:
        """Форматирование напоминания о тренировке"""
        return f"""
⏰ <b>Напоминание о тренировке</b>

Привет, {user['name']}!

Через час у вас запланирована тренировка:
📅 {training['training_date']}
🕐 {training['training_time']}
🏃‍♂️ {training['training_type']}

Подтвердите, что вы планируете прийти, или отмените запись, если планы изменились.

До встречи в зале! 💪
"""

# Глобальная переменная для сервиса уведомлений
notification_service = None

def init_notification_service(bot: Bot):
    """Инициализация сервиса уведомлений"""
    global notification_service
    notification_service = NotificationService(bot)
    return notification_service
