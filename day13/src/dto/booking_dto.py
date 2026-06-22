from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional


class BookingCreateDTO(BaseModel):
    """DTO для создания бронирования"""
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date

    @validator('check_out')
    def validate_dates(cls, v, values):
        """Валидация дат: выезд позже заезда, максимум 30 дней"""
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError('Дата выезда должна быть позже даты заезда')
        if (v - values['check_in']).days > 30:
            raise ValueError('Бронирование не может превышать 30 дней')
        return v


class BookingResponseDTO(BaseModel):
    """DTO для ответа с данными бронирования"""
    id: int
    room_id: int
    guest_name: str
    guest_email: Optional[str] = None
    check_in: date
    check_out: date
    total_price: float
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    is_expired: bool = False  # Вычисляемое поле

    @validator('is_expired', always=True)
    def compute_is_expired(cls, v, values):
        """
        Вычисляем, просрочено ли бронирование.
        
        Бронирование просрочено, если:
        - Статус = PENDING
        - Прошло более 24 часов с момента создания
        """
        if values.get('status') == 'pending':
            created_at = values.get('created_at')
            if created_at:
                elapsed = datetime.now() - created_at
                return elapsed.total_seconds() > 24 * 3600
        return False


class BookingUpdateDTO(BaseModel):
    """DTO для обновления бронирования"""
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
