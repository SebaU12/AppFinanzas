"""
SQLAlchemy model for MonthlyReimbursement.

Represents monthly settlement calculations between participants.
"""
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class MonthlyReimbursement(Base):
    """
    Monthly Reimbursement model - tracks month-end settlements.

    Calculates how shared expenses should be split between participants,
    excluding personal categories.
    """
    __tablename__ = "monthly_reimbursements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Month identifier
    month = Column(String(7), nullable=False, unique=True)  # YYYY-MM format

    # Settlement totals
    total_shared_expenses = Column(Numeric(10, 2), nullable=False)
    total_shared_income = Column(Numeric(10, 2), nullable=False, default=0)

    # Status
    finalized = Column(Boolean, default=False, nullable=False)
    finalized_date = Column(String(10), nullable=True)  # YYYY-MM-DD format

    # Relationships
    details = relationship("ReimbursementDetail", back_populates="reimbursement", cascade="all, delete-orphan")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
