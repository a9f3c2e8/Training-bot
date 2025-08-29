"""
Модели базы данных
"""
import aiosqlite
import asyncio
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

class Database:
    def __init__(self, db_path: str = "training_bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    user_type TEXT NOT NULL CHECK (user_type IN ('athlete', 'parent')),
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    birth_date DATE NOT NULL,
                    parent_telegram_id INTEGER,
                    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    trainer TEXT,
                    rank_title TEXT,
                    achievements TEXT,
                    notes TEXT
                )
            ''')

            # Таблица абонементов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    subscription_type TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    sessions_total INTEGER NOT NULL,
                    sessions_used INTEGER DEFAULT 0,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    payment_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица тренировок
            await db.execute('''
                CREATE TABLE IF NOT EXISTS trainings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    training_type TEXT NOT NULL,
                    training_date DATE NOT NULL,
                    training_time TEXT NOT NULL,
                    trainer TEXT,
                    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
                    is_trial BOOLEAN DEFAULT FALSE,
                    payment_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица платежей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    payment_id TEXT UNIQUE NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_type TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица уведомлений
            await db.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    scheduled_at DATETIME NOT NULL,
                    sent_at DATETIME,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            await db.commit()

    async def add_user(self, telegram_id: int, user_type: str, name: str, 
                      phone: str, birth_date: date, parent_telegram_id: Optional[int] = None) -> int:
        """Добавление нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO users (telegram_id, user_type, name, phone, birth_date, parent_telegram_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, user_type, name, phone, birth_date, parent_telegram_id))
            await db.commit()
            return cursor.lastrowid

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_user_info(self, user_id: int, trainer: str = None, 
                              rank_title: str = None, achievements: str = None, notes: str = None):
        """Обновление информации о пользователе (только для админов)"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            
            if trainer is not None:
                fields.append("trainer = ?")
                values.append(trainer)
            if rank_title is not None:
                fields.append("rank_title = ?")
                values.append(rank_title)
            if achievements is not None:
                fields.append("achievements = ?")
                values.append(achievements)
            if notes is not None:
                fields.append("notes = ?")
                values.append(notes)
            
            if fields:
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
                await db.execute(query, values)
                await db.commit()

    async def add_subscription(self, user_id: int, subscription_type: str, price: int, 
                              sessions_total: int, start_date: date, end_date: date, payment_id: str) -> int:
        """Добавление абонемента"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO subscriptions (user_id, subscription_type, price, sessions_total, 
                                         start_date, end_date, payment_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, subscription_type, price, sessions_total, start_date, end_date, payment_id))
            await db.commit()
            return cursor.lastrowid

    async def get_active_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение активного абонемента пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND is_active = TRUE AND end_date >= date('now')
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_training(self, user_id: int, training_type: str, training_date: date, 
                          training_time: str, trainer: str = None, is_trial: bool = False, 
                          payment_id: str = None) -> int:
        """Добавление тренировки"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO trainings (user_id, training_type, training_date, training_time, 
                                     trainer, is_trial, payment_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, training_type, training_date, training_time, trainer, is_trial, payment_id))
            await db.commit()
            return cursor.lastrowid

    async def init_schedule_tables(self):
        """Инициализация таблиц расписания"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица активных тренеров
            await db.execute('''
                CREATE TABLE IF NOT EXISTS active_trainers (
                    id INTEGER PRIMARY KEY,
                    trainer_id TEXT UNIQUE NOT NULL,
                    trainer_name TEXT NOT NULL,
                    specialization TEXT,
                    experience TEXT,
                    emoji TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица активных дней
            await db.execute('''
                CREATE TABLE IF NOT EXISTS active_days (
                    id INTEGER PRIMARY KEY,
                    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                    day_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица активных временных слотов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS active_time_slots (
                    id INTEGER PRIMARY KEY,
                    time_slot TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()

    async def get_user_trainings(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение тренировок пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM trainings 
                WHERE user_id = ? 
                ORDER BY training_date DESC, training_time DESC 
                LIMIT ?
            ''', (user_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_payment(self, user_id: int, payment_id: str, amount: int, 
                         description: str, payment_type: str) -> int:
        """Добавление платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO payments (user_id, payment_id, amount, description, payment_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, payment_id, amount, description, payment_type))
            await db.commit()
            return cursor.lastrowid

    async def update_payment_status(self, payment_id: str, status: str):
        """Обновление статуса платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE payments SET status = ?, completed_at = CURRENT_TIMESTAMP 
                WHERE payment_id = ?
            ''', (status, payment_id))
            await db.commit()

    async def get_users_for_birthday_notification(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Получение пользователей для уведомления о дне рождения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM users 
                WHERE is_active = TRUE 
                AND date('now', '+' || ? || ' days') = date(birth_date, 
                    CASE 
                        WHEN strftime('%m-%d', birth_date) >= strftime('%m-%d', 'now') 
                        THEN strftime('%Y', 'now') 
                        ELSE strftime('%Y', 'now', '+1 year') 
                    END || '-' || strftime('%m-%d', birth_date))
            ''', (days_ahead,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_inactive_users(self, days_threshold: int = 60) -> List[Dict[str, Any]]:
        """Получение неактивных пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT u.* FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id 
                WHERE u.is_active = TRUE 
                AND (s.end_date IS NULL OR s.end_date < date('now', '-' || ? || ' days'))
                GROUP BY u.id
            ''', (days_threshold,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей (для админки)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM users ORDER BY registration_date DESC')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_training_schedule(self, date_from: date, date_to: date) -> List[Dict[str, Any]]:
        """Получение расписания тренировок"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT t.*, u.name as user_name, u.phone as user_phone
                FROM trainings t
                JOIN users u ON t.user_id = u.id
                WHERE t.training_date BETWEEN ? AND ?
                ORDER BY t.training_date, t.training_time
            ''', (date_from, date_to))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def has_trial_training(self, user_id: int) -> bool:
        """Проверка, есть ли у пользователя пробная тренировка"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM trainings 
                WHERE user_id = ? AND is_trial = TRUE
            ''', (user_id,))
            count = await cursor.fetchone()
            return count[0] > 0

    # Методы для управления тренерами
    async def get_active_trainers(self) -> List[Dict[str, Any]]:
        """Получение списка активных тренеров"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM active_trainers WHERE is_active = TRUE
                ORDER BY trainer_name
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_trainer(self, trainer_id: str, trainer_name: str, specialization: str = None, 
                         experience: str = None, emoji: str = None) -> bool:
        """Добавление тренера"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO active_trainers (trainer_id, trainer_name, specialization, experience, emoji)
                    VALUES (?, ?, ?, ?, ?)
                ''', (trainer_id, trainer_name, specialization, experience, emoji))
                await db.commit()
                return True
        except:
            return False

    async def toggle_trainer_status(self, trainer_id: str) -> bool:
        """Переключение статуса тренера (активен/неактивен)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE active_trainers 
                SET is_active = NOT is_active 
                WHERE trainer_id = ?
            ''', (trainer_id,))
            await db.commit()
            return True

    # Методы для управления днями
    async def get_active_days(self) -> List[Dict[str, Any]]:
        """Получение списка активных дней"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM active_days WHERE is_active = TRUE
                ORDER BY day_of_week
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def toggle_day_status(self, day_of_week: int) -> bool:
        """Переключение статуса дня недели"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE active_days 
                SET is_active = NOT is_active 
                WHERE day_of_week = ?
            ''', (day_of_week,))
            await db.commit()
            return True

    # Методы для управления временными слотами
    async def get_active_time_slots(self) -> List[Dict[str, Any]]:
        """Получение списка активных временных слотов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM active_time_slots WHERE is_active = TRUE
                ORDER BY sort_order, time_slot
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_time_slot(self, time_slot: str, sort_order: int = 0) -> bool:
        """Добавление временного слота"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO active_time_slots (time_slot, sort_order)
                    VALUES (?, ?)
                ''', (time_slot, sort_order))
                await db.commit()
                return True
        except:
            return False

    async def toggle_time_slot_status(self, time_slot: str) -> bool:
        """Переключение статуса временного слота"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE active_time_slots 
                SET is_active = NOT is_active 
                WHERE time_slot = ?
            ''', (time_slot,))
            await db.commit()
            return True

    async def sync_config_data(self):
        """Синхронизация данных из config.py с базой данных"""
        from config import TRAINERS, TRAINING_SLOTS
        
        # Синхронизируем тренеров
        for trainer_id, trainer_info in TRAINERS.items():
            await self.add_trainer(
                trainer_id=trainer_id,
                trainer_name=trainer_info['name'],
                specialization=trainer_info['specialization'],
                experience=trainer_info['experience'],
                emoji=trainer_info['emoji']
            )
        
        # Синхронизируем дни недели
        days = [
            (0, "Понедельник"), (1, "Вторник"), (2, "Среда"), (3, "Четверг"),
            (4, "Пятница"), (5, "Суббота"), (6, "Воскресенье")
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            for day_of_week, day_name in days:
                await db.execute('''
                    INSERT OR IGNORE INTO active_days (day_of_week, day_name)
                    VALUES (?, ?)
                ''', (day_of_week, day_name))
            
            # Синхронизируем временные слоты
            for i, time_slot in enumerate(TRAINING_SLOTS):
                await db.execute('''
                    INSERT OR IGNORE INTO active_time_slots (time_slot, sort_order)
                    VALUES (?, ?)
                ''', (time_slot, i))
            
            await db.commit()

# Создаем глобальный экземпляр базы данных
db = Database()
