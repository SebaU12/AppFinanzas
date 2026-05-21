"""
SQLAlchemy model for AccountPayable.

Represents future payment obligations, typically generated from credit card installments.
"""
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class AccountPayable(Base):
    """
    Account Payable model - tracks future payment obligations.

    Generated from credit card installments and other deferred payment obligations.
    """
    __tablename__ = "accounts_payable"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to the source (installment, transaction, etc.)
    installment_id = Column(UUID(as_uuid=True), ForeignKey("card_installments.id"), nullable=True)

    # Payment details
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(String(7), nullable=False)  # YYYY-MM format

    # Status tracking
    paid = Column(Boolean, default=False, nullable=False)
    paid_date = Column(String(10), nullable=True)  # YYYY-MM-DD format

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
