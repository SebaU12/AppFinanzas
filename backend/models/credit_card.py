"""
CreditCard model - Manages credit cards with closing and payment days.
"""
import uuid
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from models.transaction import Currency


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    closing_day = Column(Integer, nullable=False)
    payment_day = Column(Integer, nullable=False)
    credit_limit = Column(Numeric(12, 2), nullable=False, default=5000)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")

    # Relationships
    participant = relationship("Participant", back_populates="credit_cards")

    def __repr__(self):
        return f"<CreditCard(name={self.name}, closing_day={self.closing_day}, payment_day={self.payment_day})>"
