from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional


class BookingStatus(Enum):
    """Статусы бронирования"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


@dataclass
class Hotel:
    """Модель отеля"""
    id: Optional[int]
    name: str
    address: str
    phone: str
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Room:
    """Модель номера"""
    id: Optional[int]
    hotel_id: int
    number: str
    capacity: int
    price_per_night: float
    is_active: bool = True
    room_type: str = "standard"  # standard, deluxe, suite


@dataclass
class Booking:
    """
    Модель бронирования.
    
    Добавлено поле confirmed_at для отслеживания времени подтверждения.
    Добавлен метод is_expired() для проверки просрочки.
    """
    id: Optional[int]
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None  # НОВОЕ ПОЛЕ
    cancelled_at: Optional[datetime] = None

    def is_expired(self, timeout_hours: int = 24) -> bool:
        """
        Проверяет, истёк ли срок для подтверждения бронирования.
        
        Аргументы:
            timeout_hours: Количество часов для подтверждения (по умолчанию 24)
        
        Возвращает:
            True если бронирование просрочено и должно быть отменено
        
        Примеры:
            >>> booking = Booking(
            ...     id=1, room_id=1, guest_name="John",
            ...     guest_email="john@example.com",
            ...     check_in=date(2026, 6, 15),
            ...     check_out=date(2026, 6, 20),
            ...     total_price=500.0,
            ...     status=BookingStatus.PENDING,
            ...     created_at=datetime.now() - timedelta(hours=25)
            ... )
            >>> booking.is_expired(24)
            True
        """
        # Статус должен быть PENDING
        if self.status != BookingStatus.PENDING:
            return False
        
        # Если уже подтверждено, не может быть просрочено
        if self.confirmed_at is not None:
            return False
        
        # Вычисляем разницу во времени
        elapsed = datetime.now() - self.created_at
        
        # Сравниваем с таймаутом
        return elapsed.total_seconds() > timeout_hours * 3600
