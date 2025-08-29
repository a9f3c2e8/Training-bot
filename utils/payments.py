"""
Интеграция с ЮKassa для обработки платежей
"""
import uuid
import asyncio
from typing import Optional, Dict, Any
from yookassa import Configuration, Payment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

# Настройка ЮKassa
Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

class PaymentService:
    @staticmethod
    async def create_payment(amount: int, description: str, user_telegram_id: int, 
                           return_url: str = None) -> Optional[Dict[str, Any]]:
        """Создание платежа в ЮKassa"""
        try:
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or "https://t.me/your_bot_name"
                },
                "description": description,
                "metadata": {
                    "user_telegram_id": str(user_telegram_id)
                }
            }
            
            # Создаем платеж в отдельном потоке, так как yookassa не поддерживает async
            loop = asyncio.get_event_loop()
            payment = await loop.run_in_executor(
                None, lambda: Payment.create(payment_data, uuid.uuid4())
            )
            
            return {
                "id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status,
                "amount": payment.amount.value
            }
        except Exception as e:
            print(f"Ошибка создания платежа: {e}")
            return None

    @staticmethod
    async def check_payment_status(payment_id: str) -> Optional[str]:
        """Проверка статуса платежа"""
        try:
            loop = asyncio.get_event_loop()
            payment = await loop.run_in_executor(
                None, lambda: Payment.find_one(payment_id)
            )
            return payment.status
        except Exception as e:
            print(f"Ошибка проверки платежа: {e}")
            return None

    @staticmethod
    async def get_payment_info(payment_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о платеже"""
        try:
            loop = asyncio.get_event_loop()
            payment = await loop.run_in_executor(
                None, lambda: Payment.find_one(payment_id)
            )
            
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": payment.amount.value,
                "description": payment.description,
                "metadata": payment.metadata,
                "created_at": payment.created_at
            }
        except Exception as e:
            print(f"Ошибка получения информации о платеже: {e}")
            return None

# Создаем глобальный экземпляр сервиса платежей
payment_service = PaymentService()
