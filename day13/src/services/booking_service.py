# src/services/booking_service.py

from datetime import date, datetime
from typing import List, Optional, Dict, Any
import logging

from src.domain.models import Booking, BookingStatus
from src.domain.exceptions import (
    RoomNotFoundError,
    BookingConflictError,
    BookingNotFoundError,
    DomainError,
    BookingExpiredError
)
from src.dto.booking_dto import BookingCreateDTO, BookingResponseDTO
from src.uow.unit_of_work import UnitOfWork
from src.services.pricing_service import PricingService

logger = logging.getLogger(__name__)


class BookingService:
    """
    Сервис для управления бронированиями с автоматической отменой просроченных.
    
    Добавленная функциональность (Вариант 7):
    1. Автоматическая отмена бронирований через заданное время
    2. Защита от подтверждения просроченных бронирований
    3. Массовая обработка просроченных бронирований
    """

    def __init__(
        self, 
        uow: UnitOfWork, 
        pricing_service: PricingService,
        confirmation_timeout_hours: int = 24
    ):
        """
        Инициализация сервиса бронирований.
        
        Аргументы:
            uow: Unit of Work для управления транзакциями
            pricing_service: Сервис для расчёта стоимости
            confirmation_timeout_hours: Время в часах для подтверждения бронирования
        """
        self.uow = uow
        self.pricing_service = pricing_service
        self.booking_repo = uow.bookings
        self.room_repo = uow.rooms
        self.confirmation_timeout_hours = confirmation_timeout_hours

    def create(self, dto: BookingCreateDTO) -> BookingResponseDTO:
        """
        Создать новое бронирование.
        
        Шаги:
        1. Проверка существования и активности номера
        2. Проверка пересечения с существующими бронированиями
        3. Расчёт стоимости
        4. Сохранение бронирования
        """
        # 1. Проверяем существование номера
        room = self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise RoomNotFoundError(f"Номер {dto.room_id} не найден")
        if not room.is_active:
            raise RoomNotFoundError(f"Номер {dto.room_id} не активен")

        # 2. Проверяем пересечения бронирований
        existing = self.booking_repo.get_by_room_and_dates(
            dto.room_id, dto.check_in, dto.check_out
        )
        if existing:
            raise BookingConflictError(
                f"Номер {dto.room_id} уже забронирован на эти даты",
                details={"conflicting_bookings": [b.id for b in existing]}
            )

        # 3. Рассчитываем стоимость
        total_price = self.pricing_service.calculate_price(
            room, dto.check_in, dto.check_out
        )

        # 4. Создаём бронирование
        booking = Booking(
            id=None,
            room_id=dto.room_id,
            guest_name=dto.guest_name,
            guest_email=dto.guest_email,
            check_in=dto.check_in,
            check_out=dto.check_out,
            total_price=total_price,
            status=BookingStatus.PENDING,
            created_at=datetime.now()
        )

        # 5. Сохраняем
        saved = self.booking_repo.add(booking)
        self.uow.commit()
        
        logger.info(f"Создано бронирование #{saved.id} для номера {saved.room_id}")
        return self._to_response_dto(saved)

    def confirm(self, booking_id: int) -> BookingResponseDTO:
        """
        Подтвердить бронирование.
        
        Если бронирование просрочено, оно автоматически отменяется
        и выбрасывается исключение BookingExpiredError.
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        # Проверка на истечение срока
        if booking.is_expired(self.confirmation_timeout_hours):
            # Автоматически отменяем просроченное бронирование
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.now()
            self.booking_repo.update(booking)
            self.uow.commit()
            
            logger.warning(
                f"Бронирование #{booking_id} автоматически отменено "
                f"(просрочено {self.confirmation_timeout_hours} часов)"
            )
            raise BookingExpiredError(
                f"Бронирование {booking_id} было автоматически отменено, "
                f"так как не подтверждено в течение {self.confirmation_timeout_hours} часов"
            )

        if booking.status != BookingStatus.PENDING:
            raise DomainError(
                f"Бронирование в статусе {booking.status.value} нельзя подтвердить"
            )

        # Подтверждаем
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now()
        self.booking_repo.update(booking)
        self.uow.commit()
        
        logger.info(f"Бронирование #{booking_id} подтверждено")
        return self._to_response_dto(booking)

    def cancel(self, booking_id: int) -> bool:
        """Отменить бронирование (ручная отмена пользователем)"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        if booking.status in (BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT):
            raise DomainError(
                f"Нельзя отменить бронирование в статусе {booking.status.value}"
            )

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now()
        self.booking_repo.update(booking)
        self.uow.commit()
        
        logger.info(f"Бронирование #{booking_id} отменено пользователем")
        return True

    def auto_cancel_expired(self) -> List[int]:
        """
        Автоматическая отмена всех просроченных бронирований.
        
        Процесс:
        1. Получаем все бронирования в статусе PENDING
        2. Для каждого проверяем is_expired()
        3. Если просрочено — меняем статус на CANCELLED
        4. Фиксируем все изменения одной транзакцией (UoW)
        
        Возвращает:
            Список ID отменённых бронирований
        """
        # 1. Получаем все PENDING бронирования
        pending_bookings = self.booking_repo.get_all(status=BookingStatus.PENDING)
        
        cancelled_ids = []
        
        # 2. Проверяем каждое
        for booking in pending_bookings:
            if booking.is_expired(self.confirmation_timeout_hours):
                # 3. Отменяем просроченное
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = datetime.now()
                self.booking_repo.update(booking)
                cancelled_ids.append(booking.id)
                logger.info(f"Автоматически отменено бронирование #{booking.id}")
        
        # 4. Фиксируем все изменения одной транзакцией
        if cancelled_ids:
            self.uow.commit()
            logger.info(f"Автоматически отменено {len(cancelled_ids)} бронирований")
        
        return cancelled_ids

    def get_available_rooms(
        self,
        hotel_id: int,
        check_in: date,
        check_out: date,
        capacity: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить доступные номера в отеле на указанные даты.
        
        Возвращает список номеров, которые не забронированы
        на указанный период.
        """
        rooms = self.room_repo.get_by_hotel(hotel_id, active_only=True)

        if capacity:
            rooms = [r for r in rooms if r.capacity >= capacity]

        available = []
        for room in rooms:
            existing = self.booking_repo.get_by_room_and_dates(
                room.id, check_in, check_out
            )
            if not existing:
                available.append({
                    'room_id': room.id,
                    'number': room.number,
                    'capacity': room.capacity,
                    'price_per_night': room.price_per_night
                })
        return available

    def get_by_id(self, booking_id: int) -> Optional[BookingResponseDTO]:
        """Получить бронирование по ID"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            return None
        return self._to_response_dto(booking)

    def get_all(self, **filters) -> List[BookingResponseDTO]:
        """Получить все бронирования с фильтрами"""
        bookings = self.booking_repo.get_all(**filters)
        return [self._to_response_dto(b) for b in bookings]

    def _to_response_dto(self, booking: Booking) -> BookingResponseDTO:
        """Преобразовать Booking в BookingResponseDTO"""
        return BookingResponseDTO(
            id=booking.id,
            room_id=booking.room_id,
            guest_name=booking.guest_name,
            guest_email=booking.guest_email,
            check_in=booking.check_in,
            check_out=booking.check_out,
            total_price=booking.total_price,
            status=booking.status.value,
            created_at=booking.created_at,
            confirmed_at=booking.confirmed_at,
            cancelled_at=booking.cancelled_at
        )
