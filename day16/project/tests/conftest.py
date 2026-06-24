"""Pytest fixtures for integration testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, Any
import warnings

from app.models import Base, Order, OrderItem
from app.repositories import OrderRepository


@pytest.fixture(scope="function")
def db_session():
    """
    Create an in-memory SQLite database session for testing.
    
    This fixture creates a new database for each test function,
    ensuring test isolation.
    """
    # Suppress ResourceWarning for unclosed databases
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Clean up
    session.rollback()
    session.close()
    
    # Dispose engine to close connections
    engine.dispose()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def repository(db_session: Session):
    """Create an OrderRepository instance with the test database session."""
    return OrderRepository(db_session)


@pytest.fixture(scope="function")
def sample_order_data() -> Dict[str, Any]:
    """Sample order data for testing."""
    return {
        "customer_name": "John Doe",
        "delivery_address": "123 Main St, Moscow",
        "status": "PENDING",
        "items": [
            {"product_name": "Laptop", "quantity": 1, "price": 999.99},
            {"product_name": "Mouse", "quantity": 2, "price": 25.50},
        ]
    }


@pytest.fixture(scope="function")
def created_order(repository, sample_order_data):
    """Create and return a sample order in the database."""
    return repository.create(sample_order_data)