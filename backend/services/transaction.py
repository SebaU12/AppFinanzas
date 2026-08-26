"""
CRUD service for Transaction operations.
"""
from uuid import UUID
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.transaction import Transaction, PaymentMethod
from models.credit_card import CreditCard
from models.category import Category, CategoryType
from models.participant import Participant
from models.card_installment import CardInstallment
from schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    """Service for managing Transaction operations"""

    PAYMENT_CATEGORY_NAME = "Pago Tarjeta de Credito"

    @staticmethod
    def create(db: Session, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction"""
        # Verify category exists and get its type
        category = db.query(Category).filter(Category.id == transaction_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {transaction_data.category_id} not found"
            )

        # Verify participant exists
        participant = db.query(Participant).filter(Participant.id == transaction_data.participant_id).first()
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participant with id {transaction_data.participant_id} not found"
            )

        # Validate credit card usage for the category
        if transaction_data.payment_method == PaymentMethod.CREDIT and not category.allows_credit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' does not allow credit card payments"
            )

        # Auto-set is_credit for credit payment method
        data_dict = transaction_data.model_dump()
        if data_dict['payment_method'] == PaymentMethod.CREDIT:
            data_dict['is_credit'] = True

        transaction = Transaction(**data_dict)
        db.add(transaction)
        db.flush()  # Flush to get transaction ID

        # Create installments for credit transactions
        if transaction.payment_method == PaymentMethod.CREDIT and transaction.card_id:
            installment_count = transaction.installment_count or 1
            amount_per_installment = float(transaction.amount) / installment_count

            # Determine first installment month based on card closing day:
            # - Purchase before closing_day → charged next month (closing cycle not yet closed)
            # - Purchase on/after closing_day → charged two months out (cycle already closed)
            card = db.query(CreditCard).filter(CreditCard.id == transaction.card_id).first()
            closing_day = card.closing_day if card else 1
            if transaction.date.day < closing_day:
                first_installment = transaction.date + relativedelta(months=1)
            else:
                first_installment = transaction.date + relativedelta(months=2)
            # Normalize to first day for month string calculation
            first_installment = first_installment.replace(day=1)

            for i in range(installment_count):
                # Calculate the month for this installment
                installment_month = first_installment + relativedelta(months=i)
                month_str = installment_month.strftime("%Y-%m")

                installment = CardInstallment(
                    transaction_id=transaction.id,
                    credit_card_id=transaction.card_id,
                    installment_number=i + 1,  # 1-indexed installment number
                    month=month_str,
                    amount=amount_per_installment,
                    paid=False
                )
                db.add(installment)

        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def get_by_id(db: Session, transaction_id: UUID) -> Transaction:
        """Get transaction by ID"""
        transaction = db.query(Transaction).options(
            joinedload(Transaction.category),
            joinedload(Transaction.participant)
        ).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with id {transaction_id} not found"
            )
        return transaction

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: UUID | None = None,
        participant_id: UUID | None = None,
        payment_method: PaymentMethod | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_type: CategoryType | None = None
    ) -> list[Transaction]:
        """Get all transactions with optional filtering"""
        query = db.query(Transaction).options(
            joinedload(Transaction.category),
            joinedload(Transaction.participant)
        ).join(Category).filter(
            Category.name != TransactionService.PAYMENT_CATEGORY_NAME
        )

        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        if participant_id:
            query = query.filter(Transaction.participant_id == participant_id)
        if payment_method:
            query = query.filter(Transaction.payment_method == payment_method)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category_type:
            query = query.join(Category).filter(Category.type == category_type)

        return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, transaction_id: UUID, transaction_data: TransactionUpdate) -> Transaction:
        """Update an existing transaction"""
        transaction = TransactionService.get_by_id(db, transaction_id)

        if transaction_data.category_id:
            category = db.query(Category).filter(Category.id == transaction_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {transaction_data.category_id} not found"
                )

        if transaction_data.participant_id:
            participant = db.query(Participant).filter(Participant.id == transaction_data.participant_id).first()
            if not participant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Participant with id {transaction_data.participant_id} not found"
                )

        update_data = transaction_data.model_dump(exclude_unset=True)

        old_payment_method = transaction.payment_method
        new_payment_method = update_data.get('payment_method', old_payment_method)

        # Apply field changes
        for field, value in update_data.items():
            setattr(transaction, field, value)

        # Sync is_credit with payment_method
        transaction.is_credit = (new_payment_method == PaymentMethod.CREDIT)

        was_credit = old_payment_method == PaymentMethod.CREDIT
        is_credit_now = new_payment_method == PaymentMethod.CREDIT

        if was_credit and not is_credit_now:
            # Changed away from credit: delete all installments
            db.query(CardInstallment).filter(
                CardInstallment.transaction_id == transaction_id
            ).delete(synchronize_session=False)
            transaction.card_id = None
            transaction.installment_count = None

        elif is_credit_now and transaction.card_id:
            reinstallment_triggers = {'amount', 'card_id', 'installment_count', 'date', 'payment_method'}
            if reinstallment_triggers & update_data.keys():
                # Keep paid installments, delete and regenerate unpaid ones
                paid_installments = db.query(CardInstallment).filter(
                    CardInstallment.transaction_id == transaction_id,
                    CardInstallment.paid == True
                ).all()
                paid_numbers = {inst.installment_number for inst in paid_installments}

                db.query(CardInstallment).filter(
                    CardInstallment.transaction_id == transaction_id,
                    CardInstallment.paid == False
                ).delete(synchronize_session=False)

                total = transaction.installment_count or 1
                amount_per = float(transaction.amount) / total

                card = db.query(CreditCard).filter(CreditCard.id == transaction.card_id).first()
                closing_day = card.closing_day if card else 1
                if transaction.date.day < closing_day:
                    first_installment = transaction.date + relativedelta(months=1)
                else:
                    first_installment = transaction.date + relativedelta(months=2)
                first_installment = first_installment.replace(day=1)

                for i in range(total):
                    inst_num = i + 1
                    if inst_num in paid_numbers:
                        continue
                    installment_month = first_installment + relativedelta(months=i)
                    db.add(CardInstallment(
                        transaction_id=transaction.id,
                        credit_card_id=transaction.card_id,
                        installment_number=inst_num,
                        month=installment_month.strftime("%Y-%m"),
                        amount=amount_per,
                        paid=False
                    ))

        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def delete(db: Session, transaction_id: UUID) -> None:
        """Delete a transaction"""
        transaction = TransactionService.get_by_id(db, transaction_id)
        db.delete(transaction)
        db.commit()

    @staticmethod
    def get_summary_by_category(db: Session, start_date: date | None = None, end_date: date | None = None) -> dict:
        """Get transaction summary grouped by category"""
        query = db.query(Transaction).join(Category).filter(
            Category.name != TransactionService.PAYMENT_CATEGORY_NAME
        )

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        transactions = query.all()

        # Group by category
        summary = {}
        for transaction in transactions:
            category_id = str(transaction.category_id)
            if category_id not in summary:
                summary[category_id] = {
                    "category_id": category_id,
                    "category_name": transaction.category.name,
                    "category_type": transaction.category.type.value,
                    "total_amount": 0,
                    "transaction_count": 0
                }
            summary[category_id]["total_amount"] += float(transaction.amount)
            summary[category_id]["transaction_count"] += 1

        return {
            "summary": list(summary.values()),
            "total_transactions": len(transactions),
            "total_amount": sum(item["total_amount"] for item in summary.values())
        }
