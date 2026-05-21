"""
CRUD service for CardInstallment operations and installment generation.
"""
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.card_installment import CardInstallment
from models.transaction import Transaction, PaymentMethod
from models.category import Category, CategoryType
from models.credit_card import CreditCard
from schemas.card_installment import CardInstallmentCreate, CardInstallmentUpdate


class CardInstallmentService:
    """Service for managing CardInstallment operations"""

    @staticmethod
    def generate_installments(db: Session, transaction: Transaction) -> list[CardInstallment]:
        """
        Generate installment records for a credit transaction.

        Creates installments spread across future months based on the transaction date
        and number of installments.
        """
        if not transaction.is_credit or not transaction.installment_count:
            return []

        installments = []
        installment_amount = Decimal(str(transaction.amount)) / transaction.installment_count

        # Round to 2 decimal places
        installment_amount = installment_amount.quantize(Decimal('0.01'))

        # Calculate adjustment for rounding
        total_rounded = installment_amount * transaction.installment_count
        adjustment = Decimal(str(transaction.amount)) - total_rounded

        # Generate installments for consecutive months
        current_date = transaction.date
        for i in range(transaction.installment_count):
            # Calculate the month for this installment
            year = current_date.year
            month = current_date.month + i

            # Handle year rollover
            while month > 12:
                month -= 12
                year += 1

            month_str = f"{year}-{month:02d}"

            # Add adjustment to last installment to ensure total matches exactly
            amount = installment_amount
            if i == transaction.installment_count - 1:
                amount += adjustment

            installment = CardInstallment(
                transaction_id=transaction.id,
                month=month_str,
                amount=amount,
                paid=False
            )
            db.add(installment)
            installments.append(installment)

        db.commit()
        return installments

    @staticmethod
    def create(db: Session, installment_data: CardInstallmentCreate) -> CardInstallment:
        """Create a new card installment manually"""
        # Verify transaction exists
        transaction = db.query(Transaction).filter(
            Transaction.id == installment_data.transaction_id
        ).first()
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with id {installment_data.transaction_id} not found"
            )

        installment = CardInstallment(**installment_data.model_dump())
        db.add(installment)
        db.commit()
        db.refresh(installment)
        return installment

    @staticmethod
    def get_by_id(db: Session, installment_id: UUID) -> CardInstallment:
        """Get card installment by ID"""
        installment = db.query(CardInstallment).options(
            joinedload(CardInstallment.transaction).joinedload(Transaction.category),
            joinedload(CardInstallment.transaction).joinedload(Transaction.participant)
        ).filter(CardInstallment.id == installment_id).first()
        if not installment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card installment with id {installment_id} not found"
            )
        return installment

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        transaction_id: UUID | None = None,
        month: str | None = None,
        paid: bool | None = None
    ) -> list[CardInstallment]:
        """Get all card installments with optional filtering"""
        query = db.query(CardInstallment).options(
            joinedload(CardInstallment.transaction).joinedload(Transaction.category),
            joinedload(CardInstallment.transaction).joinedload(Transaction.participant)
        )

        if transaction_id:
            query = query.filter(CardInstallment.transaction_id == transaction_id)
        if month:
            query = query.filter(CardInstallment.month == month)
        if paid is not None:
            query = query.filter(CardInstallment.paid == paid)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, installment_id: UUID, installment_data: CardInstallmentUpdate) -> CardInstallment:
        """Update an existing card installment (typically to mark as paid)"""
        installment = CardInstallmentService.get_by_id(db, installment_id)

        # Track if we're marking as paid (to create payment transaction)
        was_unpaid = not installment.paid
        update_data = installment_data.model_dump(exclude_unset=True)
        will_be_paid = update_data.get('paid', installment.paid)

        # Update the installment
        for field, value in update_data.items():
            setattr(installment, field, value)

        # If marking as paid, create a payment transaction
        if was_unpaid and will_be_paid:
            CardInstallmentService._create_payment_transaction(db, installment)

        db.commit()
        db.refresh(installment)
        return installment

    @staticmethod
    def _create_payment_transaction(db: Session, installment: CardInstallment) -> Transaction:
        """
        Create a payment transaction when an installment is marked as paid.

        This represents the actual cash leaving the account to pay the credit card bill.
        """
        # Get or create "Pago Tarjeta de Credito" category
        payment_category = db.query(Category).filter(
            Category.name == "Pago Tarjeta de Credito"
        ).first()

        if not payment_category:
            # Create the category if it doesn't exist
            payment_category = Category(
                name="Pago Tarjeta de Credito",
                type=CategoryType.EXPENSE,
                is_personal=True,  # Exclude from reimbursements to avoid double-counting
                allows_credit=False
            )
            db.add(payment_category)
            db.flush()  # Get the ID

        # Get the original transaction to extract details
        original_transaction = installment.transaction

        # Get the credit card to find the participant
        credit_card = db.query(CreditCard).filter(
            CreditCard.id == installment.credit_card_id
        ).first()

        # Create payment transaction
        payment_transaction = Transaction(
            date=date.today(),  # Payment date is today
            amount=installment.amount,
            category_id=payment_category.id,
            participant_id=credit_card.participant_id if credit_card else original_transaction.participant_id,
            payment_method=PaymentMethod.CASH,  # Could be DEBIT, but CASH for simplicity
            is_credit=False,
            installment_count=None,
            card_id=None,
            description=f"Pago cuota {installment.installment_number} - {original_transaction.description or 'Compra con tarjeta'}"
        )

        db.add(payment_transaction)
        db.flush()  # Ensure transaction is created

        return payment_transaction

    @staticmethod
    def delete(db: Session, installment_id: UUID) -> None:
        """Delete a card installment"""
        installment = CardInstallmentService.get_by_id(db, installment_id)
        db.delete(installment)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: str) -> dict:
        """Get summary of installments for a specific month"""
        installments = db.query(CardInstallment).filter(CardInstallment.month == month).all()

        total_amount = sum(float(inst.amount) for inst in installments)
        paid_amount = sum(float(inst.amount) for inst in installments if inst.paid)
        unpaid_amount = total_amount - paid_amount

        return {
            "month": month,
            "total_installments": len(installments),
            "total_amount": total_amount,
            "paid_count": sum(1 for inst in installments if inst.paid),
            "paid_amount": paid_amount,
            "unpaid_count": sum(1 for inst in installments if not inst.paid),
            "unpaid_amount": unpaid_amount
        }
