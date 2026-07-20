"""
Transfer model - Records movements between accounts (not income/expense).

A transfer moves money between:
  - Cash -> debit card / savings account
  - Debit card -> debit card / savings account
  - Savings account -> debit card / savings account
"""
import uuid
import enum
from sqlalchemy import Column, String, Numeric, Date, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from models.transaction import Currency


class TransferSourceType(str, enum.Enum):
    CASH = "cash"
    DEBIT = "debit"
    SAVINGS = "savings"


class TransferDestinationType(str, enum.Enum):
    DEBIT = "debit"
    SAVINGS = "savings"


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")
    from_type = Column(SQLEnum(TransferSourceType, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    to_type = Column(SQLEnum(TransferDestinationType, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    from_debit_card_id = Column(UUID(as_uuid=True), ForeignKey("debit_cards.id"), nullable=True)
    from_savings_card_id = Column(UUID(as_uuid=True), ForeignKey("savings_cards.id"), nullable=True)
    to_debit_card_id = Column(UUID(as_uuid=True), ForeignKey("debit_cards.id"), nullable=True)
    to_savings_card_id = Column(UUID(as_uuid=True), ForeignKey("savings_cards.id"), nullable=True)
    description = Column(String, nullable=True)

    from_debit_card = relationship("DebitCard", foreign_keys=[from_debit_card_id])
    from_savings_card = relationship("SavingsCard", foreign_keys=[from_savings_card_id])
    to_debit_card = relationship("DebitCard", foreign_keys=[to_debit_card_id])
    to_savings_card = relationship("SavingsCard", foreign_keys=[to_savings_card_id])
