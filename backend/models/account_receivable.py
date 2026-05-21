"""
SQLAlchemy model for AccountReceivable.

Represents expected incoming payments, typically generated from reimbursements.
"""
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class AccountReceivable(Base):
    """
    Account Receivable model - tracks expected incoming payments.

    Generated from reimbursements and other expected income sources.
    """
    __tablename__ = "accounts_receivable"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to the source (reimbursement, participant, etc.)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=True)

    # Payment details
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(String(7), nullable=False)  # YYYY-MM format

    # Status tracking
    received = Column(Boolean, default=False, nullable=False)
    received_date = Column(String(10), nullable=True)  # YYYY-MM-DD format

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
