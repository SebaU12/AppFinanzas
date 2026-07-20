import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from models.transaction import Currency


class SavingsCard(Base):
    """
    Savings Card / Savings Account entity.

    Tracks savings accounts used as a financial cushion.
    Cannot be used for transactions (payments). Money moves
    in/out exclusively through transfers.
    """
    __tablename__ = "savings_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    initial_balance = Column(Numeric(10, 2), nullable=False, default=0)
    last_four_digits = Column(String(4), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")

    participant = relationship("Participant", backref="savings_cards")
