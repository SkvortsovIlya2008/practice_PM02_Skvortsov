import random
from datetime import datetime, timedelta
from typing import Dict, Any

from models import OrderInput, OrderValidationResult

class FakeValidator:
    def __init__(self, chaos_mode: bool = False, chaos_probability: float = 0.05):
        self.chaos_mode = chaos_mode
        self.chaos_probability = chaos_probability

    def validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Валидация входных данных через Pydantic
        try:
            order_input = OrderInput(**order)
        except Exception as e:
            return {
                "valid": False,
                "reasons": [f"Invalid input: {str(e)}"],
                "risk_score": 0.0
            }

        # 2. Chaos mode
        if self.chaos_mode and random.random() < self.chaos_probability:
            return {
                "valid": random.choice([True, False]),
                "reasons": ["Chaos mode: random error"],
                "risk_score": random.random()
            }

        # 3. Основная логика
        now = datetime.now()
        reasons = []
        valid = True

        # Правило 1: сумма
        if order_input.total_amount <= 0:
            reasons.append("Сумма заказа должна быть больше 0")
            valid = False
        if order_input.total_amount >= 1_000_000:
            reasons.append("Сумма заказа должна быть меньше 1,000,000")
            valid = False

        # Правило 2: новый пользователь
        days_since_registration = (now - order_input.user_created_at).days
        if days_since_registration > 7:
            if order_input.total_amount > 15000:
                reasons.append("Для нового пользователя сумма не должна превышать 15,000")
                valid = False

        # Правило 3: количество позиций
        if order_input.items_count > 50:
            reasons.append("Количество позиций не должно превышать 50")
            valid = False

        # Правило 4: Alcohol
        if order_input.category == OrderCategory.ALCOHOL:
            if not order_input.age_verified:
                reasons.append("Для заказа алкоголя требуется подтверждение возраста")
                valid = False
            
            order_time = order_input.created_at.time()
            start_time = datetime.strptime("08:00", "%H:%M").time()
            end_time = datetime.strptime("23:00", "%H:%M").time()
            if not (start_time <= order_time <= end_time):
                reasons.append("Заказ алкоголя доступен только с 08:00 до 23:00")
                valid = False

        # Правило 5: риск-скоринг
        risk_score = 0.0
        
        if order_input.total_amount > 100_000:
            risk_score = 0.9

        if order_input.user_email_changed_at is not None:
            time_since_email_change = (now - order_input.user_email_changed_at).total_seconds()
            if time_since_email_change < 3600:  # менее часа
                risk_score = min(1.0, risk_score + 0.2)

        if order_input.delivery_country != order_input.wallet_country:
            risk_score = min(1.0, risk_score + 0.3)

        return {
            "valid": valid,
            "reasons": reasons,
            "risk_score": risk_score
        }
