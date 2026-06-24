"""Custom exceptions for the application."""


class EntityNotFoundException(Exception):
    """Exception raised when an entity is not found in the database."""
    def __init__(self, message: str = "Entity not found"):
        self.message = message
        super().__init__(self.message)


class DeliveryCalculationException(Exception):
    """Exception raised when delivery calculation fails."""
    def __init__(self, message: str = "Delivery calculation failed"):
        self.message = message
        super().__init__(self.message)
