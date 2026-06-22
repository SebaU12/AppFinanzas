"""
Transaction model - Records actual income and expense transactions.
"""
import uuid
import enum
from sqlalchemy import Column, String, Numeric, Date, Boolean, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CASH = "cash"
    DEBIT = "debit"
    CREDIT = "credit"


class Currency(str, enum.Enum):
    """Currency enumeration"""
    PEN = "PEN"  # Soles peruanos
    USD = "USD"  # Dólares estadounidenses


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=True)  # Credit card reference
    debit_card_id = Column(UUID(as_uuid=True), ForeignKey("debit_cards.id"), nullable=True)  # Debit card reference
    is_credit = Column(Boolean, default=False, nullable=False)
    installment_count = Column(Integer, nullable=True)  # Number of installments
    currency = Column(SQLEnum(Currency), nullable=False, server_default="PEN")
    description = Column(String, nullable=True)

    # Relationships
    category = relationship("Category", backref="transactions")
    participant = relationship("Participant", backref="transactions")

    def __repr__(self):
        return f"<Transaction(date={self.date}, amount={self.amount}, category_id={self.category_id})>"
