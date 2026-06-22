from datetime import date
from typing import Optional

from src.domain.models import Room
from src.domain.exceptions import InvalidDatesError


class PricingService:
    """
    Сервис расчета стоимости с использованием сезонных коэффициентов.
    
    Коэффициенты по месяцам:
    - Июнь (6): 1.2
    - Июль (7): 1.5
    - Август (8): 1.5
    - Декабрь (12): 1.3
    - Январь (1): 1.1
    - Остальные: 1.0
    """
    
    def __init__(self, seasonal_coefficients: Optional[dict] = None):
        self.seasonal_coefficients = seasonal_coefficients or {
            6: 1.2,   # июнь
            7: 1.5,   # июль
            8: 1.5,   # август
            12: 1.3,  # декабрь (новый год)
            1: 1.1,   # январь
        }

    def calculate_price(
        self,
        room: Room,
        check_in: date,
        check_out: date
    ) -> float:
        """
        Рассчитать стоимость бронирования.
        
        Учитывает:
        1. Сезонные коэффициенты (по месяцам)
        2. Скидку за длительное бронирование (7+ дней: 5%, 14+ дней: 14.5%)
        """
        nights = (check_out - check_in).days
        if nights <= 0:
            raise InvalidDatesError("Количество ночей должно быть больше 0")

        # Базовая цена с учётом сезонности
        total = 0.0
        current_date = check_in
        
        while current_date < check_out:
            month = current_date.month
            coefficient = self.seasonal_coefficients.get(month, 1.0)
            total += room.price_per_night * coefficient
            
            # Переход к следующему месяцу
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

        # Дополнительная скидка за длительное бронирование
        if nights >= 7:
            total *= 0.95  # 5% скидка
        if nights >= 14:
            total *= 0.9   # дополнительная скидка (всего 14.5%)

        return round(total, 2)
