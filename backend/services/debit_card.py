"""
CRUD service for DebitCard operations.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.debit_card import DebitCard
from models.transaction import Transaction, PaymentMethod
from schemas.debit_card import DebitCardCreate, DebitCardUpdate


class DebitCardService:
    """Service for managing DebitCard operations"""

    @staticmethod
    def create(db: Session, card_data: DebitCardCreate) -> DebitCard:
        """Create a new debit card"""
        card = DebitCard(**card_data.model_dump())
        db.add(card)
        db.commit()
        db.refresh(card)
        return card

    @staticmethod
    def get_by_id(db: Session, card_id: UUID) -> DebitCard:
        """Get debit card by ID with participant"""
        card = db.query(DebitCard).options(
            joinedload(DebitCard.participant)
        ).filter(DebitCard.id == card_id).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Debit card with id {card_id} not found"
            )
        return card

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> list[DebitCard]:
        """Get all debit cards"""
        query = db.query(DebitCard).options(
            joinedload(DebitCard.participant)
        )

        if active_only:
            query = query.filter(DebitCard.active == True)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, card_id: UUID, card_data: DebitCardUpdate) -> DebitCard:
        """Update an existing debit card"""
        card = DebitCardService.get_by_id(db, card_id)

        update_data = card_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        db.commit()
        db.refresh(card)
        return card

    @staticmethod
    def delete(db: Session, card_id: UUID) -> None:
        """Delete a debit card, unlinking any transactions that reference it"""
        card = DebitCardService.get_by_id(db, card_id)
        db.query(Transaction).filter(Transaction.debit_card_id == card_id).update(
            {Transaction.debit_card_id: None}, synchronize_session=False
        )
        db.delete(card)
        db.commit()

    @staticmethod
    def get_current_balance(db: Session, card_id: UUID) -> Decimal:
        """
        Calculate current balance of a debit card.

        Balance = initial_balance
                + income_transactions (payment_method=DEBIT, debit_card_id=card_id)
                - expense_transactions (payment_method=DEBIT, debit_card_id=card_id)
                - credit_card_payments (installments paid using this debit card)
                + incoming_transfers (to_debit_card_id=card_id)
                - outgoing_transfers (from_debit_card_id=card_id)
        """
        from models.card_installment import CardInstallment
        from models.transfer import Transfer, TransferSourceType

        card = DebitCardService.get_by_id(db, card_id)

        # Get all debit transactions for this card
        transactions = db.query(Transaction).filter(
            Transaction.debit_card_id == card_id,
            Transaction.payment_method == PaymentMethod.DEBIT
        ).options(
            joinedload(Transaction.category)
        ).all()

        balance = float(card.initial_balance)

        for transaction in transactions:
            if transaction.category.type == 'income':
                balance += float(transaction.amount)
            elif transaction.category.type == 'expense':
                balance -= float(transaction.amount)

        # Subtract credit card payments made from this debit card
        credit_payments = db.query(CardInstallment).filter(
            CardInstallment.paid_with_debit_card_id == card_id,
            CardInstallment.paid == True
        ).all()

        for payment in credit_payments:
            balance -= float(payment.amount)

        # Add incoming transfers (money arriving to this card)
        incoming = db.query(Transfer).filter(Transfer.to_debit_card_id == card_id).all()
        for t in incoming:
            balance += float(t.amount)

        # Subtract outgoing transfers (money leaving this card)
        outgoing = db.query(Transfer).filter(
            Transfer.from_debit_card_id == card_id,
            Transfer.from_type == TransferSourceType.DEBIT.value
        ).all()
        for t in outgoing:
            balance -= float(t.amount)

        return Decimal(str(balance)).quantize(Decimal('0.01'))

    @staticmethod
    def get_all_with_balances(db: Session, skip: int = 0, limit: int = 100) -> list[dict]:
        """
        Get all debit cards with their current balances calculated.
        """
        cards = DebitCardService.get_all(db, skip, limit)

        result = []
        for card in cards:
            current_balance = DebitCardService.get_current_balance(db, card.id)
            result.append({
                "card": card,
                "current_balance": current_balance
            })

        return result
