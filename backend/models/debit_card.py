"""
DebitCard model - Represents bank accounts and debit cards.

Debit cards have direct cash impact (no installments like credit cards).
They track available liquid money.
"""
import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from models.transaction import Currency


class DebitCard(Base):
    """
    Debit Card / Bank Account entity.

    Tracks bank accounts and debit cards with their balances.
    Balance is calculated from income/expense transactions.
    """
    __tablename__ = "debit_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # e.g., "Checking Account", "Savings"
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    initial_balance = Column(Numeric(10, 2), nullable=False, default=0)  # Starting balance
    last_four_digits = Column(String(4), nullable=True)  # Last 4 digits of account/card
    active = Column(Boolean, nullable=False, default=True)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")

    # Relationships
    participant = relationship("Participant", backref="debit_cards")
