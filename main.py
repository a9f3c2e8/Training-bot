"""
Главный файл запуска Telegram бота
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from bot.dp import dp, setup_handlers
from database.models import db
from utils.notifications import init_notification_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    try:
        # Инициализируем базу данных
        logger.info("Инициализация базы данных...")
        await db.init_db()
        await db.init_schedule_tables()
        
        # Выполняем первоначальную синхронизацию данных
        try:
            await db.sync_config_data()
            logger.info("Данные расписания синхронизированы")
        except Exception as e:
            logger.warning(f"Ошибка синхронизации данных расписания: {e}")
        
        logger.info("База данных инициализирована")
        
        # Инициализируем сервис уведомлений
        logger.info("Инициализация сервиса уведомлений...")
        notification_service = init_notification_service(bot)
        notification_service.start_scheduler()
        logger.info("Сервис уведомлений запущен")
        
        # Подключаем обработчики
        logger.info("Подключение обработчиков...")
        setup_handlers()
        logger.info("Обработчики подключены")
        
        # Уведомляем о запуске
        logger.info("Бот запускается...")
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username}")
        
        # Отправляем уведомление админам о запуске
        from config import ADMIN_IDS
        if ADMIN_IDS:
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, startup_message, parse_mode='HTML')
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
