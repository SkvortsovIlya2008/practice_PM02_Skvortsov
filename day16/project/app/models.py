"""SQLAlchemy models for Order and OrderItem."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Order(Base):
    """Order model representing a customer order."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    customer_name = Column(String(100), nullable=False)
    delivery_address = Column(String(200), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # One-to-many relationship with OrderItem
    items = relationship(
        "OrderItem", 
        back_populates="order", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, status='{self.status}', customer='{self.customer_name}')>"
    
    def to_dict(self):
        """Convert order to dictionary."""
        return {
            'id': self.id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'customer_name': self.customer_name,
            'delivery_address': self.delivery_address,
            'total_amount': self.total_amount,
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(Base):
    """OrderItem model representing a line item in an order."""
    
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Many-to-one relationship with Order
    order = relationship("Order", back_populates="items")
    
    # Constraints to prevent invalid data
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("price >= 0", name="check_price_non_negative"),
    )
    
    @hybrid_property
    def subtotal(self) -> float:
        """Calculate subtotal for this item."""
        return self.quantity * self.price
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product='{self.product_name}', qty={self.quantity})>"
    
    def to_dict(self):
        """Convert order item to dictionary."""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.subtotal
        }
