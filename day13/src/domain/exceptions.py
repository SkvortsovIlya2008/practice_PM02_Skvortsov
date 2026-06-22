class DomainError(Exception):
    """Базовое исключение домена"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class HotelNotFoundError(DomainError):
    """Отель не найден"""
    pass


class RoomNotFoundError(DomainError):
    """Номер не найден"""
    pass


class RoomNotAvailableError(DomainError):
    """Номер недоступен"""
    pass


class BookingNotFoundError(DomainError):
    """Бронирование не найдено"""
    pass


class BookingConflictError(DomainError):
    """Конфликт бронирований (пересечение дат)"""
    pass


class BookingExpiredError(DomainError):
    """
    Бронирование просрочено (не подтверждено вовремя).
    
    Используется в BookingService.confirm() когда пользователь пытается
    подтвердить бронирование, срок которого истёк.
    """
    pass


class InvalidDatesError(DomainError):
    """Некорректные даты"""
    pass
