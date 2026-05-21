"""
CardInstallment model - Tracks installment payments for credit card transactions.
"""
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CardInstallment(Base):
    __tablename__ = "card_installments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    credit_card_id = Column(UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=False)
    installment_number = Column(Integer, nullable=False, default=1)  # Which installment (1, 2, 3, etc.)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    amount = Column(Numeric(10, 2), nullable=False)
    paid = Column(Boolean, default=False, nullable=False)

    # Relationships
    transaction = relationship("Transaction", backref="installments")
    credit_card = relationship("CreditCard", backref="installments")

    def __repr__(self):
        return f"<CardInstallment(transaction_id={self.transaction_id}, month={self.month}, amount={self.amount})>"
