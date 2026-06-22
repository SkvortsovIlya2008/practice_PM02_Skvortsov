from typing import List, Optional

from src.domain.models import Hotel
from src.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    """In-Memory репозиторий для отелей"""
    
    def __init__(self):
        self._storage: dict[int, Hotel] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Optional[Hotel]:
        return self._storage.get(id)

    def get_all(self, **filters) -> List[Hotel]:
        result = list(self._storage.values())
        if 'name' in filters:
            result = [h for h in result if filters['name'].lower() in h.name.lower()]
        if 'min_rating' in filters:
            result = [h for h in result if h.rating >= filters['min_rating']]
        return result

    def add(self, hotel: Hotel) -> Hotel:
        hotel.id = self._next_id
        self._storage[hotel.id] = hotel
        self._next_id += 1
        return hotel

    def update(self, hotel: Hotel) -> Hotel:
        if hotel.id not in self._storage:
            raise ValueError(f"Hotel with id {hotel.id} not found")
        self._storage[hotel.id] = hotel
        return hotel

    def delete(self, id: int) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False
