import os
from dataclasses import dataclass


@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Настройки бронирований
    CONFIRMATION_TIMEOUT_HOURS: int = int(os.getenv('CONFIRMATION_TIMEOUT_HOURS', 24))
    
    # Настройки планировщика
    SCHEDULER_INTERVAL_SECONDS: int = int(os.getenv('SCHEDULER_INTERVAL_SECONDS', 3600))
    SCHEDULER_ENABLED: bool = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')


# Глобальный экземпляр конфигурации
config = Config()
