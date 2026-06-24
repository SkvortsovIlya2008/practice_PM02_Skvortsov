"""Main application module with CLI interface."""

import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

from app.models import Base, Order
from app.repositories import OrderRepository
from app.exceptions import EntityNotFoundException, DeliveryCalculationException


def get_session(db_url: str = "sqlite:///orders.db"):
    """
    Create a database session.
    
    Args:
        db_url: Database URL (default: SQLite file)
        
    Returns:
        SQLAlchemy session
    """
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def create_test_data(repository: OrderRepository) -> None:
    """
    Create sample test data in the database.
    
    Args:
        repository: OrderRepository instance
    """
    orders_data = [
        {
            "customer_name": "Alice Johnson",
            "delivery_address": "101 Main St, Moscow",
            "status": "PENDING",
            "items": [
                {"product_name": "Laptop Pro", "quantity": 1, "price": 1500.00},
                {"product_name": "Wireless Mouse", "quantity": 2, "price": 30.00},
            ]
        },
        {
            "customer_name": "Bob Smith",
            "delivery_address": "202 Oak Ave, SPb",
            "status": "PAID",
            "items": [
                {"product_name": "Smartphone", "quantity": 2, "price": 800.00},
                {"product_name": "Phone Case", "quantity": 3, "price": 15.00},
            ]
        },
        {
            "customer_name": "Carol White",
            "delivery_address": "303 Pine St, Kazan",
            "status": "SHIPPED",
            "items": [
                {"product_name": "Tablet", "quantity": 1, "price": 400.00},
                {"product_name": "Keyboard", "quantity": 1, "price": 50.00},
                {"product_name": "Stylus Pen", "quantity": 2, "price": 25.00},
            ]
        },
        {
            "customer_name": "David Brown",
            "delivery_address": "404 Elm St, Novosibirsk",
            "status": "CANCELLED",
            "items": [
                {"product_name": "Monitor 27\"", "quantity": 1, "price": 300.00},
            ]
        }
    ]
    
    for order_data in orders_data:
        try:
            repository.create(order_data)
            print(f"✓ Created order for {order_data['customer_name']}")
        except Exception as e:
            print(f"✗ Failed to create order: {e}")


def print_order(order: Order) -> None:
    """Pretty print an order."""
    print("\n" + "=" * 60)
    print(f"ORDER #{order.id}")
    print("=" * 60)
    print(f"Customer: {order.customer_name}")
    print(f"Address: {order.delivery_address}")
    print(f"Status: {order.status}")
    print(f"Created: {order.created_at}")
    print(f"Total: ${order.total_amount:.2f}")
    print("-" * 60)
    print("Items:")
    for item in order.items:
        print(f"  • {item.quantity}x {item.product_name} @ ${item.price:.2f} = ${item.subtotal:.2f}")
    print("=" * 60)


def print_orders(orders: list, title: str = "Orders"):
    """Pretty print multiple orders."""
    print(f"\n{'=' * 60}")
    print(f"{title} ({len(orders)} orders)")
    print("=" * 60)
    for order in orders:
        print(f"#{order.id}: {order.customer_name} - {order.status} - ${order.total_amount:.2f}")
    print("=" * 60)


def main():
    """Main CLI entry point."""
    print("=" * 60)
    print("ORDER MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Create session and repository
    session = get_session()
    repository = OrderRepository(session)
    
    try:
        # Create test data
        print("\n📦 Creating test data...")
        create_test_data(repository)
        
        # Demo operations
        print("\n" + "=" * 60)
        print("DEMO OPERATIONS")
        print("=" * 60)
        
        # 1. Find all orders
        all_orders = session.query(Order).all()
        print_orders(all_orders, "All Orders")
        
        # 2. Find by status
        pending_orders = repository.find_all_by_status("PENDING")
        print_orders(pending_orders, "Pending Orders")
        
        # 3. Get order details by ID
        if all_orders:
            first_order_id = all_orders[0].id
            print(f"\n📄 Getting order #{first_order_id} details...")
            order_details = repository.get_order_summary(first_order_id)
            print_order(repository.find_by_id(first_order_id))
        
        # 4. Update status
        if all_orders:
            order_id = all_orders[0].id
            print(f"\n🔄 Updating order #{order_id} status to PAID...")
            updated = repository.update_status(order_id, "PAID")
            print(f"✓ Status updated to: {updated.status}")
        
        # 5. Calculate total for an order
        if all_orders:
            order_id = all_orders[0].id
            total = repository.get_total_amount_for_order(order_id)
            print(f"\n💰 Total amount for order #{order_id}: ${total:.2f}")
        
        # 6. Date range search
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(days=1)
        date_orders = repository.find_by_date_range(start_date, end_date)
        print_orders(date_orders, "Orders Created Today")
        
        # 7. Calculate delivery cost (mock)
        if all_orders:
            order_id = all_orders[0].id
            try:
                print(f"\n🚚 Calculating delivery cost for order #{order_id}...")
                print("   (Using mock API - actual API may not be available)")
                cost = repository.calculate_delivery_cost(order_id)
                print(f"✓ Delivery cost: ${cost:.2f}")
            except DeliveryCalculationException as e:
                print(f"⚠️  Delivery calculation failed: {e}")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
