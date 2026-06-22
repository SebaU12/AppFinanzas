"""
SQLAlchemy model for ExpectedPurchase.

Represents simulated future purchases for planning purposes.
These don't affect actual transactions but help visualize financial impact.
"""
import uuid
from sqlalchemy import Column, String, Numeric, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum

from app.database import Base
from models.transaction import PaymentMethod, Currency


class ExpectedPurchase(Base):
    """
    Expected Purchase model - simulates future purchases.

    Allows "what-if" analysis of planned purchases, showing impact on
    budget, cash flow, and payables without creating actual transactions.
    """
    __tablename__ = "expected_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Purchase details
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expected_date = Column(String(10), nullable=False)  # YYYY-MM-DD format

    # References
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)

    # Payment details
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=True)
    installment_count = Column(Integer, nullable=True)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")

    # Status
    converted_to_transaction = Column(Boolean, default=False, nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
