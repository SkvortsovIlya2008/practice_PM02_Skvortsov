import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BookingScheduler:
    """
    Планировщик для автоматической отмены просроченных бронирований.
    
    Работает в фоновом потоке и периодически вызывает
    BookingService.auto_cancel_expired().
    
    В реальных проектах используется:
    - Celery Beat (для распределённых систем)
    - APScheduler (для встроенных решений)
    - Cron (для простых систем)
    """
    
    def __init__(
        self, 
        booking_service: 'BookingService',
        interval_seconds: int = 3600,  # проверка каждый час
        enabled: bool = True
    ):
        """
        Инициализация планировщика.
        
        Аргументы:
            booking_service: Сервис бронирований
            interval_seconds: Интервал между проверками в секундах
            enabled: Включён ли планировщик при старте
        """
        self.booking_service = booking_service
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._enabled = enabled

    def start(self) -> None:
        """Запуск фонового планировщика"""
        if self._running:
            logger.warning("Планировщик уже запущен")
            return
        
        if not self._enabled:
            logger.info("Планировщик отключён в конфигурации")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Планировщик запущен (интервал: {self.interval_seconds} секунд)")

    def stop(self) -> None:
        """Остановка планировщика"""
        if not self._running:
            logger.warning("Планировщик уже остановлен")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Планировщик остановлен")

    def _run(self) -> None:
        """Основной цикл планировщика"""
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}", exc_info=True)
            time.sleep(self.interval_seconds)

    def _tick(self) -> None:
        """Один "тик" планировщика — проверка и отмена просроченных бронирований"""
        cancelled = self.booking_service.auto_cancel_expired()
        if cancelled:
            logger.info(f"Автоматически отменено {len(cancelled)} просроченных бронирований: {cancelled}")

    def is_running(self) -> bool:
        """Проверка, запущен ли планировщик"""
        return self._running
