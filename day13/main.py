"""
Пример использования Booking System с автоматической отменой просроченных бронирований.
"""

import logging
import time
from datetime import date, timedelta

from src.uow.unit_of_work import UnitOfWork
from src.services.booking_service import BookingService
from src.services.pricing_service import PricingService
from src.services.scheduler import BookingScheduler
from src.dto.booking_dto import BookingCreateDTO
from src.domain.models import Room, Hotel
from src.config import config

# Настройка логирования
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_test_data(uow: UnitOfWork):
    """Создание тестовых данных"""
    
    # Создаём отель
    hotel = Hotel(
        id=None,
        name="Grand Hotel",
        address="ул. Центральная, 1",
        phone="+7-999-123-45-67",
        rating=4.5
    )
    uow.hotels.add(hotel)
    
    # Создаём номера
    rooms = [
        Room(id=None, hotel_id=1, number="101", capacity=2, price_per_night=100.0),
        Room(id=None, hotel_id=1, number="102", capacity=4, price_per_night=150.0),
        Room(id=None, hotel_id=1, number="103", capacity=2, price_per_night=120.0),
        Room(id=None, hotel_id=1, number="104", capacity=3, price_per_night=130.0),
    ]
    for room in rooms:
        uow.rooms.add(room)
    
    uow.commit()
    logger.info("Тестовые данные созданы")


def main():
    """Основная функция демонстрации"""
    
    # Инициализация
    uow = UnitOfWork()
    pricing_service = PricingService()
    booking_service = BookingService(
        uow, 
        pricing_service,
        confirmation_timeout_hours=config.CONFIRMATION_TIMEOUT_HOURS
    )
    
    # Подготовка данных
    setup_test_data(uow)
    
    # Запуск планировщика
    scheduler = BookingScheduler(
        booking_service,
        interval_seconds=config.SCHEDULER_INTERVAL_SECONDS,
        enabled=config.SCHEDULER_ENABLED
    )
    scheduler.start()
    
    try:
        # Создаём тестовое бронирование
        logger.info("\n=== Создание бронирования ===")
        dto = BookingCreateDTO(
            room_id=1,
            guest_name="Иван Петров",
            guest_email="ivan@example.com",
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=15)
        )
        booking = booking_service.create(dto)
        logger.info(f"Создано бронирование #{booking.id}")
        logger.info(f"Статус: {booking.status}")
        logger.info(f"Просрочено: {booking.is_expired}")
        
        # Проверяем доступные номера
        logger.info("\n=== Доступные номера ===")
        available = booking_service.get_available_rooms(
            hotel_id=1,
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=15)
        )
        logger.info(f"Доступно номеров: {len(available)}")
        
        # Ждём, чтобы планировщик мог сработать (в демонстрационных целях)
        logger.info("\n=== Ожидание работы планировщика ===")
        logger.info("Планировщик запущен и будет проверять бронирования...")
        logger.info("(В реальном приложении планировщик работает в фоне)")
        
        # Демонстрация: создаём ещё одно бронирование, которое будет просрочено
        logger.info("\n=== Создание просроченного бронирования ===")
        # Создаём бронирование с искусственно старым created_at (только для демонстрации)
        old_booking = Booking(
            id=None,
            room_id=2,
            guest_name="Пётр Сидоров",
            guest_email="petr@example.com",
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=7),
            total_price=300.0,
            status=BookingStatus.PENDING,
            created_at=datetime.now() - timedelta(hours=25)  # просрочено
        )
        uow.bookings.add(old_booking)
        uow.commit()
        logger.info(f"Создано просроченное бронирование #{old_booking.id}")
        
        # Запускаем ручную проверку
        logger.info("\n=== Ручная проверка просроченных бронирований ===")
        cancelled = booking_service.auto_cancel_expired()
        logger.info(f"Отменено бронирований: {len(cancelled)}")
        if cancelled:
            logger.info(f"ID отменённых: {cancelled}")
        
        # Проверяем статус
        logger.info("\n=== Текущие бронирования ===")
        all_bookings = booking_service.get_all()
        for b in all_bookings:
            logger.info(
                f"ID: {b.id}, Статус: {b.status}, "
                f"Гость: {b.guest_name}, Просрочено: {b.is_expired}"
            )
            
    except KeyboardInterrupt:
        logger.info("Остановка приложения...")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
