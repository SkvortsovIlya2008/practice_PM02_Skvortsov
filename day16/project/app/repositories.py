"""Order repository implementation."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
import httpx

from app.models import Order, OrderItem
from app.exceptions import EntityNotFoundException, DeliveryCalculationException


class OrderRepository:
    """Repository for Order operations with database session management."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with a database session.
        
        Args:
            session: SQLAlchemy session object
        """
        self.session = session
    
    def create(self, order_data: Dict[str, Any]) -> Order:
        """
        Create an order with associated items.
        
        Args:
            order_data: Dictionary containing order fields and 'items' list
            
        Returns:
            Created Order object
            
        Raises:
            ValueError: If order_data is invalid
        """
        # Extract items data
        items_data = order_data.pop("items", [])
        
        # Create Order object
        order = Order(**order_data)
        self.session.add(order)
        self.session.flush()  # Get order.id without committing
        
        # Create OrderItem objects
        for item_data in items_data:
            order_item = OrderItem(order_id=order.id, **item_data)
            self.session.add(order_item)
        
        # Calculate total amount from items
        self.session.flush()  # Ensure items are in session
        total = sum(item.quantity * item.price for item in order.items)
        order.total_amount = total
        
        # Commit transaction
        self.session.commit()
        self.session.refresh(order)
        
        return order
    
    def find_by_id(self, order_id: int) -> Optional[Order]:
        """
        Find an order by ID with its items loaded.
        
        Args:
            order_id: Order ID to find
            
        Returns:
            Order object or None if not found
        """
        return self.session.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.id == order_id).first()
    
    def find_all_by_status(self, status: str) -> List[Order]:
        """
        Find all orders with the given status.
        
        Args:
            status: Order status to filter by
            
        Returns:
            List of Order objects with the given status
        """
        return self.session.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.status == status).all()
    
    def update_status(self, order_id: int, new_status: str) -> Order:
        """
        Update the status of an order.
        
        Args:
            order_id: ID of the order to update
            new_status: New status value
            
        Returns:
            Updated Order object
            
        Raises:
            EntityNotFoundException: If order not found
        """
        order = self.find_by_id(order_id)
        if order is None:
            raise EntityNotFoundException(f"Order with id {order_id} not found")
        
        order.status = new_status
        self.session.commit()
        self.session.refresh(order)
        return order
    
    def delete(self, order_id: int) -> None:
        """
        Hard delete an order and its items (cascade).
        
        Args:
            order_id: ID of the order to delete
            
        Raises:
            EntityNotFoundException: If order not found
        """
        order = self.find_by_id(order_id)
        if order is None:
            raise EntityNotFoundException(f"Order with id {order_id} not found")
        
        self.session.delete(order)
        self.session.commit()
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """
        Find orders created within the given date range (inclusive).
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of Order objects in the date range
        """
        return self.session.query(Order).options(
            joinedload(Order.items)
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        ).all()
    
    def get_total_amount_for_order(self, order_id: int) -> float:
        """
        Calculate total amount for an order using SQL aggregation.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Total amount as float, or 0.0 if order has no items
        """
        result = self.session.query(
            func.sum(OrderItem.quantity * OrderItem.price).label("total")
        ).filter(OrderItem.order_id == order_id).first()
        
        return float(result.total) if result.total is not None else 0.0
    
    def calculate_delivery_cost(self, order_id: int) -> float:
        """
        Calculate delivery cost by calling external delivery API.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Delivery cost in rubles
            
        Raises:
            EntityNotFoundException: If order not found
            DeliveryCalculationException: If API call fails
        """
        # Find order with items
        order = self.find_by_id(order_id)
        if order is None:
            raise EntityNotFoundException(f"Order with id {order_id} not found")
        
        # Calculate total weight (each item weighs 0.5kg)
        total_weight = sum(item.quantity * 0.5 for item in order.items)
        
        # Prepare request
        url = "https://api.delivery.com/calculate"
        payload = {
            "address": order.delivery_address,
            "weight": total_weight
        }
        
        try:
            # Use synchronous HTTP client
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Validate response
                if "cost" not in data:
                    raise DeliveryCalculationException(
                        "Invalid response from delivery API: missing 'cost' field"
                    )
                
                return float(data["cost"])
                
        except httpx.HTTPStatusError as e:
            raise DeliveryCalculationException(
                f"Delivery API returned error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise DeliveryCalculationException(
                f"Delivery API request failed: {str(e)}"
            )
        except (KeyError, ValueError, TypeError) as e:
            raise DeliveryCalculationException(
                f"Invalid response from delivery API: {str(e)}"
            )
    
    def get_order_summary(self, order_id: int) -> Dict[str, Any]:
        """
        Get a summary of the order including items and totals.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Dictionary with order summary
            
        Raises:
            EntityNotFoundException: If order not found
        """
        order = self.find_by_id(order_id)
        if order is None:
            raise EntityNotFoundException(f"Order with id {order_id} not found")
        
        return {
            'order_id': order.id,
            'customer': order.customer_name,
            'status': order.status,
            'total_amount': order.total_amount,
            'item_count': len(order.items),
            'items': [item.to_dict() for item in order.items]
        }
