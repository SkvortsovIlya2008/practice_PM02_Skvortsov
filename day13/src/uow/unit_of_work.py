from contextlib import contextmanager

from src.repositories.booking_repo import BookingRepository
from src.repositories.hotel_repo import HotelRepository
from src.repositories.room_repo import RoomRepository


class UnitOfWork:
    """
    Unit of Work — управляет транзакциями.
    
    Обеспечивает атомарность операций: все изменения фиксируются
    одним commit() или откатываются rollback().
    """
    
    def __init__(self):
        self._hotel_repo = HotelRepository()
        self._room_repo = RoomRepository()
        self._booking_repo = BookingRepository()
        self._committed = False

    @property
    def hotels(self) -> HotelRepository:
        return self._hotel_repo

    @property
    def rooms(self) -> RoomRepository:
        return self._room_repo

    @property
    def bookings(self) -> BookingRepository:
        return self._booking_repo

    def commit(self) -> None:
        """Фиксация транзакции"""
        self._committed = True
        # В реальном случае здесь был бы session.commit()

    def rollback(self) -> None:
        """Откат транзакции"""
        self._committed = False
        # В реальном случае здесь был бы session.rollback()

    @contextmanager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.commit()
