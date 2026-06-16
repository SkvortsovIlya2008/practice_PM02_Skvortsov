import pytest
from datetime import datetime, timedelta
import random
from freezegun import freeze_time
from hypothesis import given, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

from fake_validator import FakeValidator
from models import OrderInput, OrderCategory

def create_order(**kwargs):
    defaults = {
        "order_id": "test_order",
        "user_id": "test_user",
        "created_at": datetime.now(),
        "total_amount": 100.0,
        "items_count": 5,
        "category": OrderCategory.GROCERY.value,
        "age_verified": False,
        "user_email_changed_at": None,
        "delivery_country": "RU",
        "wallet_country": "RU",
        "user_created_at": datetime.now() - timedelta(days=365),
    }
    defaults.update(kwargs)
    return defaults

@pytest.mark.parametrize(
    "order_kwargs, expected_valid, expected_risk_min, expected_risk_max, reasons_substrings",
    [
        # Граничные значения сумм
        ({"total_amount": 0.01}, True, 0.0, 0.0, []),
        ({"total_amount": 999999.99}, True, 0.9, 0.9, []),
        ({"total_amount": 0}, False, 0.0, 0.0, ["больше 0"]),
        ({"total_amount": 1000000}, False, 0.9, 0.9, ["меньше"]),
        
        # Новый пользователь
        ({"user_created_at": datetime.now() - timedelta(days=6), "total_amount": 15000}, True, 0.0, 0.0, []),
        ({"user_created_at": datetime.now() - timedelta(days=6), "total_amount": 15000.01}, False, 0.0, 0.0, ["нового пользователя"]),
        ({"user_created_at": datetime.now() - timedelta(days=8), "total_amount": 15000}, True, 0.0, 0.0, []),
        ({"user_created_at": datetime.now() - timedelta(days=8), "total_amount": 15000.01}, False, 0.0, 0.0, ["нового пользователя"]),
        
        # Количество позиций
        ({"items_count": 50}, True, 0.0, 0.0, []),
        ({"items_count": 51}, False, 0.0, 0.0, ["превышает 50"]),
        
        # Alcohol - время и верификация
        ({"category": OrderCategory.ALCOHOL.value, "age_verified": True, "created_at": datetime.now().replace(hour=8, minute=0, second=0)}, True, 0.0, 0.0, []),
        ({"category": OrderCategory.ALCOHOL.value, "age_verified": True, "created_at": datetime.now().replace(hour=7, minute=59, second=59)}, False, 0.0, 0.0, ["08:00 до 23:00"]),
        ({"category": OrderCategory.ALCOHOL.value, "age_verified": True, "created_at": datetime.now().replace(hour=23, minute=0, second=0)}, True, 0.0, 0.0, []),
        ({"category": OrderCategory.ALCOHOL.value, "age_verified": True, "created_at": datetime.now().replace(hour=23, minute=0, second=1)}, False, 0.0, 0.0, ["08:00 до 23:00"]),
        ({"category": OrderCategory.ALCOHOL.value, "age_verified": False, "created_at": datetime.now().replace(hour=12, minute=0)}, False, 0.0, 0.0, ["подтверждение возраста"]),
        
        # Риск-скоринг
        ({"total_amount": 100001}, True, 0.9, 0.9, []),
        ({"total_amount": 100000}, True, 0.0, 0.0, []),
        ({"user_email_changed_at": datetime.now() - timedelta(minutes=30)}, True, 0.2, 0.2, []),
        ({"user_email_changed_at": datetime.now() - timedelta(hours=2)}, True, 0.0, 0.0, []),
        ({"delivery_country": "RU", "wallet_country": "US"}, True, 0.3, 0.3, []),
        ({"delivery_country": "RU", "wallet_country": "RU"}, True, 0.0, 0.0, []),
        
        # Комбинации рисков
        ({"total_amount": 200000, "user_email_changed_at": datetime.now() - timedelta(minutes=10), 
          "delivery_country": "RU", "wallet_country": "US"}, True, 1.0, 1.0, []),
        
        # Комбинации правил
        ({"user_created_at": datetime.now() - timedelta(days=10), "total_amount": 20000, 
          "category": OrderCategory.ALCOHOL.value, "age_verified": True, 
          "created_at": datetime.now().replace(hour=2, minute=0)}, False, 0.0, 0.0, 
          ["нового пользователя", "08:00 до 23:00"]),
    ]
)
def test_validate_order_decision_table(validator, order_kwargs, expected_valid, 
                                        expected_risk_min, expected_risk_max, 
                                        reasons_substrings):
    order = create_order(**order_kwargs)
    result = validator.validate_order(order)
    
    assert result["valid"] == expected_valid
    assert expected_risk_min <= result["risk_score"] <= expected_risk_max
    
    for substring in reasons_substrings:
        assert any(substring in reason for reason in result["reasons"])

# Стратегия для генерации заказов
@st.composite
def order_strategy(draw):
    return {
        "order_id": "test",
        "user_id": "user",
        "created_at": draw(st.datetimes(min_value=datetime(2020, 1, 1))),
        "total_amount": draw(st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False)),
        "items_count": draw(st.integers(min_value=1, max_value=100)),
        "category": draw(st.sampled_from([c.value for c in OrderCategory])),
        "age_verified": draw(st.booleans()),
        "user_email_changed_at": draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)))),
        "delivery_country": draw(st.text(min_size=2, max_size=2, alphabet=st.characters(whitelist_codes=range(65, 91)))),
        "wallet_country": draw(st.text(min_size=2, max_size=2, alphabet=st.characters(whitelist_codes=range(65, 91)))),
        "user_created_at": draw(st.datetimes(min_value=datetime(2020, 1, 1))),
    }

@given(order_strategy())
def test_risk_score_in_range(order):
    validator = FakeValidator(chaos_mode=False)
    result = validator.validate_order(order)
    assert 0.0 <= result["risk_score"] <= 1.0

@given(order_strategy())
def test_invariant_valid_implies_reason(order):
    validator = FakeValidator(chaos_mode=False)
    result = validator.validate_order(order)
    if not result["valid"]:
        assert len(result["reasons"]) > 0

@given(order_strategy())
def test_valid_orders_always_boolean(order):
    """Поле valid всегда булево"""
    validator = FakeValidator(chaos_mode=False)
    result = validator.validate_order(order)
    assert isinstance(result["valid"], bool)

def test_alcohol_time_boundary():
    validator = FakeValidator()
    
    with freeze_time("2026-06-16 07:59:59"):
        order = create_order(
            category=OrderCategory.ALCOHOL.value,
            age_verified=True,
            created_at=datetime.now()
        )
        result = validator.validate_order(order)
        assert result["valid"] is False
    
    with freeze_time("2026-06-16 08:00:00"):
        order = create_order(
            category=OrderCategory.ALCOHOL.value,
            age_verified=True,
            created_at=datetime.now()
        )
        result = validator.validate_order(order)
        assert result["valid"] is True

def test_duplicate_orders_stability():
    validator = FakeValidator()
    order = create_order()
    result1 = validator.validate_order(order)
    result2 = validator.validate_order(order)
    
    # Проверяем, что реализация не падает и результаты детерминированы
    assert result1["valid"] == result2["valid"]
    assert result1["risk_score"] == result2["risk_score"]
    assert result1["reasons"] == result2["reasons"]

def test_random_orders_robustness():
    validator = FakeValidator()
    categories = [c.value for c in OrderCategory]
    
    for _ in range(100):
        order = create_order(
            total_amount=random.uniform(-1000, 2000000),
            items_count=random.randint(-10, 100),
            category=random.choice(categories),
            age_verified=random.choice([True, False]),
            delivery_country=random.choice(["RU", "US", "GB", "DE"]),
            wallet_country=random.choice(["RU", "US", "GB", "DE"]),
            user_created_at=datetime.now() - timedelta(days=random.randint(-10, 365)),
            user_email_changed_at=datetime.now() - timedelta(seconds=random.randint(-3600, 7200))
        )
        result = validator.validate_order(order)
        
        # Проверяем основные инварианты
        assert 0.0 <= result["risk_score"] <= 1.0
        assert isinstance(result["valid"], bool)
        assert isinstance(result["reasons"], list)
