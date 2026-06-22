import pytest
from unittest.mock import Mock

from src.services.pricing_service import PricingService
from src.uow.unit_of_work import UnitOfWork
from src.services.booking_service import BookingService


@pytest.fixture
def mock_uow():
    """Фикстура для мока UnitOfWork"""
    uow = Mock(spec=UnitOfWork)
    uow.bookings = Mock()
    uow.rooms = Mock()
    uow.commit = Mock()
    return uow


@pytest.fixture
def pricing_service():
    """Фикстура для PricingService"""
    return PricingService()


@pytest.fixture
def booking_service(mock_uow, pricing_service):
    """Фикстура для BookingService с таймаутом 24 часа"""
    return BookingService(mock_uow, pricing_service, confirmation_timeout_hours=24)
