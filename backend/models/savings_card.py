import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from models.transaction import Currency


class SavingsCard(Base):
    """
    Savings Card / Savings Account entity.

    Used exclusively as transfer source/destination.
    No balance tracking — interest logic is out of scope.
    """
    __tablename__ = "savings_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    last_four_digits = Column(String(4), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")

    participant = relationship("Participant", backref="savings_cards")
