from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator

class OrderCategory(str, Enum):
    ALCOHOL = "Alcohol"
    GROCERY = "Grocery"
    ELECTRONICS = "Electronics"
    CLOTHING = "Clothing"

class OrderInput(BaseModel):
    order_id: str = Field(..., description="Уникальный идентификатор заказа")
    user_id: str = Field(..., description="Идентификатор пользователя")
    created_at: datetime = Field(..., description="Время создания заказа")
    total_amount: float = Field(..., description="Сумма заказа")
    items_count: int = Field(..., description="Количество позиций в заказе")
    category: OrderCategory = Field(..., description="Категория товара")
    age_verified: bool = Field(False, description="Подтверждён ли возраст пользователя")
    user_email_changed_at: Optional[datetime] = Field(None, description="Время последней смены email")
    delivery_country: str = Field(..., min_length=2, max_length=2, description="Код страны доставки")
    wallet_country: str = Field(..., min_length=2, max_length=2, description="Код страны кошелька")
    user_created_at: datetime = Field(..., description="Дата регистрации пользователя")

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v <= 0 or v >= 1_000_000:
            raise ValueError('Сумма должна быть между 0 и 1,000,000')
        return v

    @validator('items_count')
    def validate_items_count(cls, v):
        if not (1 <= v <= 50):
            raise ValueError('Количество позиций должно быть от 1 до 50')
        return v

class OrderValidationResult(BaseModel):
    valid: bool = Field(..., description="Флаг валидности заказа")
    reasons: List[str] = Field(..., description="Список причин невалидности")
    risk_score: float = Field(..., ge=0, le=1, description="Оценка риска (0..1)")
