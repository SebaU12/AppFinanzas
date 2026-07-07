"""
Transfer model - Records movements between accounts (not income/expense).

A transfer moves money between:
  - Cash → debit card
  - Debit card → debit card
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


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")
    from_type = Column(SQLEnum(TransferSourceType, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    from_debit_card_id = Column(UUID(as_uuid=True), ForeignKey("debit_cards.id"), nullable=True)
    to_debit_card_id = Column(UUID(as_uuid=True), ForeignKey("debit_cards.id"), nullable=False)
    description = Column(String, nullable=True)

    from_debit_card = relationship("DebitCard", foreign_keys=[from_debit_card_id])
    to_debit_card = relationship("DebitCard", foreign_keys=[to_debit_card_id])
