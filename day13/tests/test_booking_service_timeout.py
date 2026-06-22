import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch

from src.services.booking_service import BookingService
from src.services.pricing_service import PricingService
from src.uow.unit_of_work import UnitOfWork
from src.dto.booking_dto import BookingCreateDTO
from src.domain.models import Room, Booking, BookingStatus
from src.domain.exceptions import (
    BookingExpiredError,
    BookingNotFoundError,
    DomainError,
    BookingConflictError,
    RoomNotFoundError
)


class TestBookingServiceTimeout:
    """Тесты для функциональности автоматической отмены"""

    def test_confirm_valid_booking_success(self, booking_service, mock_uow):
        """Успешное подтверждение валидного бронирования"""
        # Arrange
        valid_booking = Booking(
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
        mock_uow.bookings.get_by_id.return_value = valid_booking

        # Act
        with patch('src.services.booking_service.datetime') as mock_datetime:
            fixed_now = datetime(2026, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            
            result = booking_service.confirm(1)

        # Assert
        assert valid_booking.status == BookingStatus.CONFIRMED
        assert valid_booking.confirmed_at == fixed_now
        mock_uow.bookings.update.assert_called_once_with(valid_booking)
        mock_uow.commit.assert_called_once()
        assert result.id == 1
        assert result.status == "confirmed"

    def test_confirm_expired_booking_raises_error_and_cancels(
        self, booking_service, mock_uow
    ):
        """
        Попытка подтвердить просроченное бронирование:
        - вызывает BookingExpiredError
        - автоматически отменяет бронирование
        """
        # Arrange
        expired_booking = Booking(
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
        mock_uow.bookings.get_by_id.return_value = expired_booking

        # Act & Assert
        with patch('src.services.booking_service.datetime') as mock_datetime:
            fixed_now = datetime(2026, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            
            with pytest.raises(BookingExpiredError) as exc_info:
                booking_service.confirm(1)

        assert "автоматически отменено" in str(exc_info.value)
        assert "24 часов" in str(exc_info.value)
        assert expired_booking.status == BookingStatus.CANCELLED
        assert expired_booking.cancelled_at == fixed_now
        mock_uow.bookings.update.assert_called_once_with(expired_booking)
        mock_uow.commit.assert_called_once()

    def test_confirm_non_pending_booking_raises_error(self, booking_service, mock_uow):
        """Попытка подтвердить уже подтверждённое бронирование вызывает ошибку"""
        # Arrange
        confirmed_booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.CONFIRMED,
            created_at=datetime.now() - timedelta(hours=5),
            confirmed_at=datetime.now() - timedelta(hours=4)
        )
        mock_uow.bookings.get_by_id.return_value = confirmed_booking

        # Act & Assert
        with pytest.raises(DomainError) as exc_info:
            booking_service.confirm(1)

        assert "нельзя подтвердить" in str(exc_info.value)
        mock_uow.commit.assert_not_called()

    def test_confirm_booking_not_found_raises_error(self, booking_service, mock_uow):
        """Попытка подтвердить несуществующее бронирование вызывает ошибку"""
        # Arrange
        mock_uow.bookings.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(BookingNotFoundError) as exc_info:
            booking_service.confirm(999)

        assert "999" in str(exc_info.value)
        mock_uow.commit.assert_not_called()

    def test_auto_cancel_expired_cancels_only_expired_bookings(
        self, booking_service, mock_uow
    ):
        """Автоматическая отмена отменяет только просроченные бронирования"""
        # Arrange
        expired_booking = Booking(
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
        
        valid_booking = Booking(
            id=2,
            room_id=2,
            guest_name="Jane",
            guest_email="jane@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=600.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=5)
        )
        
        mock_uow.bookings.get_all.return_value = [expired_booking, valid_booking]

        # Act
        with patch('src.services.booking_service.datetime') as mock_datetime:
            fixed_now = datetime(2026, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            
            cancelled_ids = booking_service.auto_cancel_expired()

        # Assert
        assert cancelled_ids == [1]
        assert expired_booking.status == BookingStatus.CANCELLED
        assert expired_booking.cancelled_at == fixed_now
        assert valid_booking.status == BookingStatus.PENDING
        assert valid_booking.cancelled_at is None
        
        mock_uow.bookings.update.assert_called_once_with(expired_booking)
        mock_uow.commit.assert_called_once()

    def test_auto_cancel_expired_with_no_expired_bookings(
        self, booking_service, mock_uow
    ):
        """Если просроченных бронирований нет, ничего не отменяется"""
        # Arrange
        valid_booking = Booking(
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
        mock_uow.bookings.get_all.return_value = [valid_booking]

        # Act
        cancelled_ids = booking_service.auto_cancel_expired()

        # Assert
        assert cancelled_ids == []
        mock_uow.bookings.update.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_auto_cancel_expired_ignores_non_pending_bookings(
        self, booking_service, mock_uow
    ):
        """Не-PENDING бронирования игнорируются при авто-отмене"""
        # Arrange
        confirmed_booking = Booking(
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
        
        cancelled_booking = Booking(
            id=2,
            room_id=2,
            guest_name="Jane",
            guest_email="jane@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=600.0,
            status=BookingStatus.CANCELLED,
            created_at=datetime.now() - timedelta(hours=25),
            cancelled_at=datetime.now() - timedelta(hours=24)
        )
        
        mock_uow.bookings.get_all.return_value = [confirmed_booking, cancelled_booking]

        # Act
        cancelled_ids = booking_service.auto_cancel_expired()

        # Assert
        assert cancelled_ids == []
        mock_uow.bookings.update.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_auto_cancel_expired_with_custom_timeout(
        self, mock_uow, pricing_service
    ):
        """Авто-отмена работает с пользовательским таймаутом"""
        # Arrange
        service = BookingService(mock_uow, pricing_service, confirmation_timeout_hours=12)
        
        expired_booking = Booking(
            id=1,
            room_id=1,
            guest_name="John",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            total_price=500.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=13)
        )
        
        mock_uow.bookings.get_all.return_value = [expired_booking]

        # Act
        with patch('src.services.booking_service.datetime') as mock_datetime:
            fixed_now = datetime(2026, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            
            cancelled_ids = service.auto_cancel_expired()

        # Assert
        assert cancelled_ids == [1]
        assert expired_booking.status == BookingStatus.CANCELLED

    def test_cancel_booking_after_expiry_works_normally(
        self, booking_service, mock_uow
    ):
        """Ручная отмена просроченного бронирования работает нормально"""
        # Arrange
        expired_booking = Booking(
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
        mock_uow.bookings.get_by_id.return_value = expired_booking

        # Act
        with patch('src.services.booking_service.datetime') as mock_datetime:
            fixed_now = datetime(2026, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            
            result = booking_service.cancel(1)

        # Assert
        assert result is True
        assert expired_booking.status == BookingStatus.CANCELLED
        assert expired_booking.cancelled_at == fixed_now
        mock_uow.bookings.update.assert_called_once_with(expired_booking)
        mock_uow.commit.assert_called_once()

    def test_get_by_id_shows_expired_status(self, booking_service, mock_uow):
        """Метод get_by_id возвращает информацию о просроченности"""
        # Arrange
        expired_booking = Booking(
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
        mock_uow.bookings.get_by_id.return_value = expired_booking

        # Act
        result = booking_service.get_by_id(1)

        # Assert
        assert result is not None
        assert result.is_expired is True
        assert result.status == "pending"

    def test_get_by_id_for_valid_booking_shows_not_expired(
        self, booking_service, mock_uow
    ):
        """Метод get_by_id показывает что валидное бронирование не просрочено"""
        # Arrange
        valid_booking = Booking(
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
        mock_uow.bookings.get_by_id.return_value = valid_booking

        # Act
        result = booking_service.get_by_id(1)

        # Assert
        assert result is not None
        assert result.is_expired is False
