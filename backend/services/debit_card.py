"""
CRUD service for DebitCard operations.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.category import CategoryType
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
        from models.transfer import Transfer
        from sqlalchemy import or_

        card = DebitCardService.get_by_id(db, card_id)

        transfer_count = db.query(Transfer).filter(
            or_(
                Transfer.from_debit_card_id == card_id,
                Transfer.to_debit_card_id == card_id,
            )
        ).count()

        if transfer_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete debit card: it has {transfer_count} associated transfer(s). "
                    "Delete or reassign those transfers first."
                ),
            )

        db.query(Transaction).filter(Transaction.debit_card_id == card_id).update(
            {Transaction.debit_card_id: None}, synchronize_session=False
        )
        db.delete(card)
        db.commit()

    @staticmethod
    def _calculate_balance(db: Session, card: DebitCard) -> Decimal:
        """
        Calculate current balance given an already-loaded DebitCard object.

        Balance = initial_balance
                + income_transactions (payment_method=DEBIT, debit_card_id=card.id)
                - expense_transactions (payment_method=DEBIT, debit_card_id=card.id)
                - credit_card_payments (installments paid using this debit card)
                + incoming_transfers (to_debit_card_id=card.id)
                - outgoing_transfers (from_debit_card_id=card.id)
        """
        from models.card_installment import CardInstallment
        from models.transfer import Transfer

        card_id = card.id

        transactions = db.query(Transaction).filter(
            Transaction.debit_card_id == card_id,
            Transaction.payment_method == PaymentMethod.DEBIT
        ).options(
            joinedload(Transaction.category)
        ).all()

        balance = Decimal(str(card.initial_balance))

        for transaction in transactions:
            if transaction.category.type == CategoryType.INCOME:
                balance += Decimal(str(transaction.amount))
            elif transaction.category.type == CategoryType.EXPENSE:
                balance -= Decimal(str(transaction.amount))

        credit_payments = db.query(CardInstallment).filter(
            CardInstallment.paid_with_debit_card_id == card_id,
            CardInstallment.paid == True
        ).all()

        for payment in credit_payments:
            balance -= Decimal(str(payment.amount))

        incoming = db.query(Transfer).filter(Transfer.to_debit_card_id == card_id).all()
        for t in incoming:
            balance += Decimal(str(t.amount))

        outgoing = db.query(Transfer).filter(
            Transfer.from_debit_card_id == card_id
        ).all()
        for t in outgoing:
            balance -= Decimal(str(t.amount))

        return balance.quantize(Decimal('0.01'))

    @staticmethod
    def get_current_balance(db: Session, card_id: UUID) -> Decimal:
        """Calculate current balance of a debit card by ID."""
        card = DebitCardService.get_by_id(db, card_id)
        return DebitCardService._calculate_balance(db, card)

    @staticmethod
    def get_all_with_balances(
        db: Session, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> list[dict]:
        """Get all debit cards with their current balances calculated."""
        cards = DebitCardService.get_all(db, skip, limit, active_only)

        return [
            {"card": card, "current_balance": DebitCardService._calculate_balance(db, card)}
            for card in cards
        ]
