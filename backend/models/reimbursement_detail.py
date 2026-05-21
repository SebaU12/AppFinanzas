"""
SQLAlchemy model for ReimbursementDetail.

Represents individual participant's share in monthly reimbursement.
"""
import uuid
from sqlalchemy import Column, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ReimbursementDetail(Base):
    """
    Reimbursement Detail model - tracks individual participant balances.

    Shows how much each participant paid, their expected share,
    and the resulting balance (positive = owed to them, negative = they owe).
    """
    __tablename__ = "reimbursement_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    reimbursement_id = Column(UUID(as_uuid=True), ForeignKey("monthly_reimbursements.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)

    # Financial details
    amount_paid = Column(Numeric(10, 2), nullable=False)  # What they actually paid
    expected_share = Column(Numeric(10, 2), nullable=False)  # What they should pay (based on percentage)
    balance = Column(Numeric(10, 2), nullable=False)  # amount_paid - expected_share
    percentage = Column(Numeric(5, 2), nullable=False)  # Their percentage for this month

    # Relationships
    reimbursement = relationship("MonthlyReimbursement", back_populates="details")
    participant = relationship("Participant")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint("reimbursement_id", "participant_id", name="uq_reimbursement_participant"),
    )
