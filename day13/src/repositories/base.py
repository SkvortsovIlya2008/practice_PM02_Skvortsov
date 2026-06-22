from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Абстрактный базовый репозиторий"""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Получить сущность по ID"""
        pass
    
    @abstractmethod
    def get_all(self, **filters) -> List[T]:
        """Получить все сущности с фильтрацией"""
        pass
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """Добавить сущность"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Обновить сущность"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Удалить сущность"""
        pass
