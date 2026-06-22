import pytest
from datetime import datetime, timedelta, date

from src.domain.models import Booking, BookingStatus


class TestBookingModel:
    """Тесты для модели Booking — проверка логики is_expired()"""

    def test_is_expired_returns_true_for_old_pending_booking(self):
        """Просроченное PENDING бронирование возвращает True"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=25)
        )
        assert booking.is_expired(24) is True

    def test_is_expired_returns_false_for_fresh_pending_booking(self):
        """Свежее PENDING бронирование возвращает False"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=5)
        )
        assert booking.is_expired(24) is False

    def test_is_expired_returns_false_for_confirmed_booking(self):
        """Подтверждённое бронирование не считается просроченным"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.CONFIRMED,
            created_at=datetime.now() - timedelta(hours=25),
            confirmed_at=datetime.now() - timedelta(hours=24)
        )
        assert booking.is_expired(24) is False

    def test_is_expired_returns_false_for_cancelled_booking(self):
        """Отменённое бронирование не считается просроченным"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.CANCELLED,
            created_at=datetime.now() - timedelta(hours=25),
            cancelled_at=datetime.now() - timedelta(hours=24)
        )
        assert booking.is_expired(24) is False

    def test_is_expired_respects_custom_timeout(self):
        """Учитывается пользовательский таймаут"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=12)
        )
        # С таймаутом 24 часа — ещё не просрочено
        assert booking.is_expired(24) is False
        # С таймаутом 8 часов — уже просрочено
        assert booking.is_expired(8) is True

    def test_is_expired_considers_confirmed_at(self):
        """Если confirmed_at установлен, бронирование не просрочено"""
        booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=25),
            confirmed_at=datetime.now() - timedelta(hours=1)
        )
        assert booking.is_expired(24) is False
