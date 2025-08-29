"""
Диспетчер бота
"""
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Создаем диспетчер с хранилищем состояний в памяти
dp = Dispatcher(storage=MemoryStorage())

def setup_handlers():
    """Подключение всех обработчиков"""
    from handlers import registration, common, subscriptions, trainings, admin
    
    # Регистрируем роутеры в правильном порядке
    dp.include_router(registration.router)
    dp.include_router(subscriptions.router)
    dp.include_router(trainings.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)  # Общие обработчики в конце
