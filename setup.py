"""
Скрипт установки и настройки бота
"""
import os
import asyncio
from pathlib import Path

def create_env_file():
    """Создание файла .env с настройками"""
    env_content = """# Конфигурация бота для спортивной школы

# Токен бота (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# ЮKassa настройки (для приема платежей)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# База данных
DATABASE_URL=sqlite:///training_bot.db
"""
    
    env_path = Path('.env')
    if not env_path.exists():
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Файл .env создан")
    else:
        print("ℹ️ Файл .env уже существует")

async def init_database():
    """Инициализация базы данных"""
    from database.models import db
    await db.init_db()
    print("✅ База данных инициализирована")

def main():
    """Основная функция установки"""
    print("🚀 Установка бота для спортивной школы")
    print("=" * 50)
    
    # Создаем .env файл
    create_env_file()
    
    # Инициализируем базу данных
    print("📦 Инициализация базы данных...")
    asyncio.run(init_database())
    
    print("\n✅ Установка завершена!")
    print("\n📝 Что делать дальше:")
    print("1. Отредактируйте файл .env и укажите:")
    print("   - BOT_TOKEN (получите у @BotFather)")
    print("   - YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY (для приема платежей)")
    print("   - ADMIN_IDS (ваш Telegram ID)")
    print("2. Запустите бота: python main.py")
    print("\n🎯 Удачи с проектом!")

if __name__ == "__main__":
    main()
