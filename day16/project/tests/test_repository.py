"""Integration tests for OrderRepository."""

import pytest
from datetime import datetime, timedelta
import httpx

from app.models import Order, OrderItem
from app.exceptions import EntityNotFoundException, DeliveryCalculationException


class TestOrderRepository:
    """Test suite for OrderRepository."""
    
    # ============================================================
    # 1. CREATE TESTS
    # ============================================================
    
    def test_create_order_success(self, repository, sample_order_data):
        """Test successful order creation with items."""
        # Arrange
        assert repository.session.query(Order).count() == 0
        assert repository.session.query(OrderItem).count() == 0
        
        # Act
        order = repository.create(sample_order_data)
        
        # Assert
        assert order.id is not None
        assert order.customer_name == "John Doe"
        assert order.delivery_address == "123 Main St, Moscow"
        assert order.status == "PENDING"
        assert len(order.items) == 2
        expected_total = 999.99 + (2 * 25.50)  # 1050.99
        assert order.total_amount == expected_total
        
        # Verify in database
        db_order = repository.session.query(Order).filter(Order.id == order.id).first()
        assert db_order is not None
        assert db_order.customer_name == "John Doe"
        db_items = repository.session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        assert len(db_items) == 2
    
    def test_create_order_with_no_items(self, repository):
        """Test creating an order with no items."""
        # Arrange
        order_data = {
            "customer_name": "Jane Smith",
            "delivery_address": "456 Oak St, SPb",
            "status": "PENDING",
            "items": []
        }
        
        # Act
        order = repository.create(order_data)
        
        # Assert
        assert order.id is not None
        assert order.total_amount == 0.0
        assert len(order.items) == 0
    
    def test_create_order_rollback_on_invalid_data(self, repository):
        """Test that transaction rolls back when invalid data is provided."""
        # Arrange
        order_data = {
            "customer_name": "Invalid Order",
            "delivery_address": "Some Address",
            "status": "PENDING",
            "items": [
                {"product_name": "Invalid Item", "quantity": -1, "price": 10.0}
            ]
        }

        initial_order_count = repository.session.query(Order).count()
        initial_item_count = repository.session.query(OrderItem).count()

        # Act & Assert
        with pytest.raises(Exception):
            try:
                repository.create(order_data)
            except Exception:
                # Rollback the session to clear the error state
                repository.session.rollback()
                raise

        # Assert - nothing should be saved
        assert repository.session.query(Order).count() == initial_order_count
        assert repository.session.query(OrderItem).count() == initial_item_count
    
    def test_create_order_with_duplicate_items(self, repository):
        """Test creating an order with duplicate product names."""
        # Arrange
        order_data = {
            "customer_name": "Test User",
            "delivery_address": "Test Address",
            "status": "PENDING",
            "items": [
                {"product_name": "Item A", "quantity": 2, "price": 10.0},
                {"product_name": "Item A", "quantity": 1, "price": 15.0},
            ]
        }
        
        # Act
        order = repository.create(order_data)
        
        # Assert
        assert len(order.items) == 2
        assert order.total_amount == 2 * 10.0 + 1 * 15.0  # 35.0
    
    # ============================================================
    # 2. FIND BY ID TESTS
    # ============================================================
    
    def test_find_by_id_existing(self, repository, created_order):
        """Test finding an existing order by ID."""
        # Act
        found_order = repository.find_by_id(created_order.id)
        
        # Assert
        assert found_order is not None
        assert found_order.id == created_order.id
        assert found_order.customer_name == created_order.customer_name
        assert len(found_order.items) == 2
        assert found_order.items[0].product_name == "Laptop"
    
    def test_find_by_id_non_existing(self, repository):
        """Test finding a non-existing order returns None."""
        # Act
        found_order = repository.find_by_id(999)
        
        # Assert
        assert found_order is None
    
    # ============================================================
    # 3. FIND BY STATUS TESTS
    # ============================================================
    
    @pytest.mark.parametrize("status", ["PENDING", "PAID", "SHIPPED", "CANCELLED"])
    def test_find_by_status_all_statuses(self, repository, status):
        """Test finding orders by status for all valid statuses."""
        # Arrange - create orders with different statuses
        statuses = ["PENDING", "PAID", "SHIPPED", "CANCELLED"]
        for s in statuses:
            order_data = {
                "customer_name": f"Customer {s}",
                "delivery_address": "Some Address",
                "status": s,
                "items": [{"product_name": "Item", "quantity": 1, "price": 10.0}]
            }
            repository.create(order_data)
        
        # Act
        found_orders = repository.find_all_by_status(status)
        
        # Assert
        assert len(found_orders) == 1
        assert all(o.status == status for o in found_orders)
    
    def test_find_by_status_empty_result(self, repository):
        """Test finding orders with a status that has no orders."""
        # Act
        found_orders = repository.find_all_by_status("PAID")
        
        # Assert
        assert len(found_orders) == 0
    
    def test_find_by_status_multiple_orders(self, repository):
        """Test finding multiple orders with the same status."""
        # Arrange
        for i in range(3):
            order_data = {
                "customer_name": f"Customer {i}",
                "delivery_address": f"Address {i}",
                "status": "PENDING",
                "items": [{"product_name": "Item", "quantity": 1, "price": 10.0}]
            }
            repository.create(order_data)
        
        # Act
        found_orders = repository.find_all_by_status("PENDING")
        
        # Assert
        assert len(found_orders) == 3
        assert all(o.status == "PENDING" for o in found_orders)
    
    # ============================================================
    # 4. UPDATE STATUS TESTS
    # ============================================================
    
    def test_update_status_success(self, repository, created_order):
        """Test successful status update."""
        # Arrange
        assert created_order.status == "PENDING"
        
        # Act
        updated_order = repository.update_status(created_order.id, "PAID")
        
        # Assert
        assert updated_order.status == "PAID"
        assert updated_order.id == created_order.id
        
        # Verify in database
        db_order = repository.session.query(Order).filter(Order.id == created_order.id).first()
        assert db_order.status == "PAID"
    
    def test_update_status_not_found(self, repository):
        """Test updating status of non-existing order raises exception."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.update_status(999, "PAID")
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    def test_update_status_multiple_times(self, repository, created_order):
        """Test updating status multiple times."""
        # Act
        order1 = repository.update_status(created_order.id, "PAID")
        assert order1.status == "PAID"
        
        order2 = repository.update_status(created_order.id, "SHIPPED")
        assert order2.status == "SHIPPED"
        
        # Assert final state
        db_order = repository.session.query(Order).filter(Order.id == created_order.id).first()
        assert db_order.status == "SHIPPED"
    
    # ============================================================
    # 5. DELETE TESTS
    # ============================================================
    
    def test_delete_order_success(self, repository, created_order):
        """Test successful order deletion with cascade."""
        # Arrange
        order_id = created_order.id
        assert repository.session.query(Order).count() == 1
        item_count = repository.session.query(OrderItem).filter(OrderItem.order_id == order_id).count()
        assert item_count == 2
        
        # Act
        repository.delete(order_id)
        
        # Assert
        assert repository.session.query(Order).count() == 0
        assert repository.session.query(OrderItem).filter(OrderItem.order_id == order_id).count() == 0
    
    def test_delete_order_not_found(self, repository):
        """Test deleting non-existing order raises exception."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.delete(999)
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    def test_delete_order_then_create_new(self, repository, created_order):
        """Test deleting an order and creating a new one."""
        # Arrange
        old_id = created_order.id
        
        # Act
        repository.delete(old_id)
        
        # Create new order
        new_order_data = {
            "customer_name": "New Customer",
            "delivery_address": "New Address",
            "status": "PENDING",
            "items": [{"product_name": "New Item", "quantity": 1, "price": 100.0}]
        }
        new_order = repository.create(new_order_data)
        
        # Assert - IDs should be different because we deleted the old one
        # In SQLite with autoincrement, the ID might be reused if we deleted
        # Let's check that the new order exists and has correct data
        assert new_order.id is not None
        assert new_order.customer_name == "New Customer"
        assert new_order.total_amount == 100.0
        
        # Verify we have exactly one order in the database
        assert repository.session.query(Order).count() == 1
        
        # The new order should be the only one
        db_order = repository.session.query(Order).first()
        assert db_order.id == new_order.id
        assert db_order.customer_name == "New Customer"
    
    # ============================================================
    # 6. DATE RANGE TESTS
    # ============================================================
    
    def test_find_by_date_range(self, repository, db_session):
        """Test finding orders within a date range."""
        # Arrange - create orders with different dates
        base_date = datetime(2024, 1, 15, 10, 0, 0)
        
        orders_data = [
            {"customer_name": "Order 1", "delivery_address": "Address 1", "status": "PENDING", 
             "items": [{"product_name": "Item 1", "quantity": 1, "price": 10.0}]},
            {"customer_name": "Order 2", "delivery_address": "Address 2", "status": "PENDING",
             "items": [{"product_name": "Item 2", "quantity": 1, "price": 20.0}]},
            {"customer_name": "Order 3", "delivery_address": "Address 3", "status": "PENDING",
             "items": [{"product_name": "Item 3", "quantity": 1, "price": 30.0}]},
        ]
        
        created_orders = []
        for i, data in enumerate(orders_data):
            order = repository.create(data)
            # Manually update created_at
            order.created_at = base_date + timedelta(days=i)
            db_session.commit()
            db_session.refresh(order)
            created_orders.append(order)
        
        # Act - search for orders created on days 0 and 1 (inclusive)
        start_date = base_date
        end_date = base_date + timedelta(days=1, hours=23, minutes=59, seconds=59)
        found_orders = repository.find_by_date_range(start_date, end_date)
        
        # Assert
        found_ids = [o.id for o in found_orders]
        assert created_orders[0].id in found_ids
        assert created_orders[1].id in found_ids
        assert created_orders[2].id not in found_ids
        
        # Act - search for a range with no matches
        start_date = base_date + timedelta(days=10)
        end_date = base_date + timedelta(days=15)
        found_orders = repository.find_by_date_range(start_date, end_date)
        
        # Assert
        assert len(found_orders) == 0
    
    def test_find_by_date_range_inclusive(self, repository, db_session):
        """Test that date range includes boundary values."""
        # Arrange
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        order = repository.create({
            "customer_name": "Test Order",
            "delivery_address": "Test Address",
            "status": "PENDING",
            "items": [{"product_name": "Item", "quantity": 1, "price": 10.0}]
        })
        order.created_at = base_date
        db_session.commit()
        db_session.refresh(order)
        
        # Act - search with exact same date
        found_orders = repository.find_by_date_range(base_date, base_date)
        
        # Assert
        assert len(found_orders) == 1
        assert found_orders[0].id == order.id
    
    # ============================================================
    # 7. TOTAL AMOUNT TESTS
    # ============================================================
    
    def test_get_total_amount_for_order(self, repository, created_order):
        """Test calculating total amount for an order."""
        # Act
        total = repository.get_total_amount_for_order(created_order.id)
        
        # Assert
        expected_total = 999.99 + (2 * 25.50)  # 1050.99
        assert total == expected_total
    
    def test_get_total_amount_for_empty_order(self, repository):
        """Test calculating total for an order with no items."""
        # Arrange
        order_data = {
            "customer_name": "Empty Order",
            "delivery_address": "Some Address",
            "status": "PENDING",
            "items": []
        }
        order = repository.create(order_data)
        
        # Act
        total = repository.get_total_amount_for_order(order.id)
        
        # Assert
        assert total == 0.0
    
    def test_get_total_amount_for_non_existing_order(self, repository):
        """Test calculating total for a non-existing order returns 0."""
        # Act
        total = repository.get_total_amount_for_order(999)
        
        # Assert
        assert total == 0.0
    
    def test_get_total_amount_with_multiple_items(self, repository):
        """Test calculating total with multiple items of different quantities."""
        # Arrange
        order_data = {
            "customer_name": "Multi Items",
            "delivery_address": "Address",
            "status": "PENDING",
            "items": [
                {"product_name": "A", "quantity": 3, "price": 10.0},
                {"product_name": "B", "quantity": 2, "price": 25.0},
                {"product_name": "C", "quantity": 5, "price": 7.5},
            ]
        }
        order = repository.create(order_data)
        
        # Act
        total = repository.get_total_amount_for_order(order.id)
        
        # Assert
        expected_total = 3*10.0 + 2*25.0 + 5*7.5  # 30 + 50 + 37.5 = 117.5
        assert total == expected_total
    
    # ============================================================
    # 8. CONTRACT TESTS (EXTERNAL API)
    # ============================================================
    
    def test_calculate_delivery_cost_success(self, repository, created_order, httpx_mock):
        """Test successful delivery cost calculation."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"cost": 150.0},
            status_code=200
        )
        
        # Act
        cost = repository.calculate_delivery_cost(created_order.id)
        
        # Assert
        assert cost == 150.0
        
        # Verify request was made with correct data
        request = httpx_mock.get_request()
        assert request.url == "https://api.delivery.com/calculate"
        assert request.method == "POST"
        # Use request.content or request.read() to get the body
        import json
        payload = json.loads(request.content)
        assert payload["address"] == "123 Main St, Moscow"
        assert payload["weight"] == (1 * 0.5 + 2 * 0.5)  # 1.5 kg
    
    def test_calculate_delivery_cost_order_not_found(self, repository):
        """Test delivery cost calculation for non-existing order."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.calculate_delivery_cost(999)
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    def test_calculate_delivery_cost_server_error(self, repository, created_order, httpx_mock):
        """Test delivery cost calculation when API returns error."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"error": "Internal Server Error"},
            status_code=500
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(created_order.id)
        
        assert "Delivery API returned error: 500" in str(exc_info.value)
    
    def test_calculate_delivery_cost_network_error(self, repository, created_order, httpx_mock):
        """Test delivery cost calculation when network error occurs."""
        # Arrange
        httpx_mock.add_exception(
            url="https://api.delivery.com/calculate",
            method="POST",
            exception=httpx.ConnectError("Connection refused")
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(created_order.id)
        
        assert "Delivery API request failed" in str(exc_info.value)
    
    def test_calculate_delivery_cost_invalid_response(self, repository, created_order, httpx_mock):
        """Test delivery cost calculation when API returns invalid response."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"not_cost": 150.0},  # Missing 'cost' field
            status_code=200
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(created_order.id)
        
        assert "Invalid response from delivery API" in str(exc_info.value)
    
    def test_calculate_delivery_cost_zero_weight(self, repository, httpx_mock):
        """Test delivery cost calculation for order with zero weight."""
        # Arrange
        order_data = {
            "customer_name": "Zero Weight",
            "delivery_address": "Test Address",
            "status": "PENDING",
            "items": []  # No items = zero weight
        }
        order = repository.create(order_data)
        
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"cost": 50.0},
            status_code=200
        )
        
        # Act
        cost = repository.calculate_delivery_cost(order.id)
        
        # Assert
        assert cost == 50.0
        request = httpx_mock.get_request()
        import json
        payload = json.loads(request.content)
        assert payload["weight"] == 0.0
    
    # ============================================================
    # 9. GET ORDER SUMMARY TESTS
    # ============================================================
    
    def test_get_order_summary_success(self, repository, created_order):
        """Test getting order summary."""
        # Act
        summary = repository.get_order_summary(created_order.id)
        
        # Assert
        assert summary['order_id'] == created_order.id
        assert summary['customer'] == "John Doe"
        assert summary['status'] == "PENDING"
        assert summary['total_amount'] == 1050.99
        assert summary['item_count'] == 2
        assert len(summary['items']) == 2
        assert summary['items'][0]['product_name'] == "Laptop"
        assert summary['items'][0]['subtotal'] == 999.99
    
    def test_get_order_summary_not_found(self, repository):
        """Test getting summary for non-existing order."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.get_order_summary(999)
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    # ============================================================
    # 10. EDGE CASES AND ADDITIONAL TESTS
    # ============================================================
    
    def test_create_order_with_large_quantities(self, repository):
        """Test creating order with large quantities."""
        # Arrange
        order_data = {
            "customer_name": "Bulk Order",
            "delivery_address": "Bulk Address",
            "status": "PENDING",
            "items": [
                {"product_name": "Bulk Item", "quantity": 1000, "price": 0.99}
            ]
        }
        
        # Act
        order = repository.create(order_data)
        
        # Assert
        assert order.total_amount == 990.0
        assert order.items[0].quantity == 1000
    
    def test_create_order_with_zero_price_items(self, repository):
        """Test creating order with zero price items."""
        # Arrange
        order_data = {
            "customer_name": "Free Items",
            "delivery_address": "Free Address",
            "status": "PENDING",
            "items": [
                {"product_name": "Free Item", "quantity": 5, "price": 0.0}
            ]
        }
        
        # Act
        order = repository.create(order_data)
        
        # Assert
        assert order.total_amount == 0.0
        assert order.items[0].price == 0.0
    
    def test_find_all_by_status_with_items(self, repository):
        """Test that status search returns orders with items loaded."""
        # Arrange
        order_data = {
            "customer_name": "Status Test",
            "delivery_address": "Status Address",
            "status": "PAID",
            "items": [
                {"product_name": "Item 1", "quantity": 1, "price": 10.0},
                {"product_name": "Item 2", "quantity": 2, "price": 20.0},
            ]
        }
        order = repository.create(order_data)
        
        # Act
        found_orders = repository.find_all_by_status("PAID")
        
        # Assert
        assert len(found_orders) == 1
        found_order = found_orders[0]
        assert len(found_order.items) == 2
        assert found_order.items[0].product_name == "Item 1"
        assert found_order.items[1].product_name == "Item 2"
