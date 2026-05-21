"""
Business logic for AccountPayable operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.account_payable import AccountPayable
from models.card_installment import CardInstallment
from schemas.account_payable import AccountPayableCreate, AccountPayableUpdate


class AccountPayableService:
    """Service for managing accounts payable"""

    @staticmethod
    def create(db: Session, payable: AccountPayableCreate) -> AccountPayable:
        """Create a new account payable"""
        db_payable = AccountPayable(**payable.model_dump())
        db.add(db_payable)
        db.commit()
        db.refresh(db_payable)
        return db_payable

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        due_date: str | None = None,
        paid: bool | None = None
    ) -> list[AccountPayable]:
        """Get all accounts payable with optional filtering"""
        query = db.query(AccountPayable)

        if due_date is not None:
            query = query.filter(AccountPayable.due_date == due_date)

        if paid is not None:
            query = query.filter(AccountPayable.paid == paid)

        return query.order_by(AccountPayable.due_date).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, payable_id: UUID) -> AccountPayable:
        """Get a specific account payable by ID"""
        payable = db.query(AccountPayable).filter(AccountPayable.id == payable_id).first()
        if not payable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AccountPayable with id {payable_id} not found"
            )
        return payable

    @staticmethod
    def update(db: Session, payable_id: UUID, payable_update: AccountPayableUpdate) -> AccountPayable:
        """Update an existing account payable"""
        db_payable = AccountPayableService.get_by_id(db, payable_id)

        update_data = payable_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payable, field, value)

        db.commit()
        db.refresh(db_payable)
        return db_payable

    @staticmethod
    def delete(db: Session, payable_id: UUID) -> None:
        """Delete an account payable"""
        db_payable = AccountPayableService.get_by_id(db, payable_id)
        db.delete(db_payable)
        db.commit()

    @staticmethod
    def generate_from_installments(db: Session) -> list[AccountPayable]:
        """
        Generate accounts payable from unpaid installments.

        Creates or updates payable records for all unpaid installments.
        """
        # Get all unpaid installments
        unpaid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == False
        ).all()

        created_payables = []

        for installment in unpaid_installments:
            # Check if payable already exists for this installment
            existing = db.query(AccountPayable).filter(
                AccountPayable.installment_id == installment.id
            ).first()

            if not existing:
                # Create new payable
                payable = AccountPayable(
                    installment_id=installment.id,
                    description=f"Credit card installment payment",
                    amount=installment.amount,
                    due_date=installment.month,
                    paid=False
                )
                db.add(payable)
                created_payables.append(payable)

        if created_payables:
            db.commit()
            for payable in created_payables:
                db.refresh(payable)

        return created_payables

    @staticmethod
    def get_monthly_summary(db: Session, month: str) -> dict:
        """Get summary of accounts payable for a specific month"""
        payables = db.query(AccountPayable).filter(
            AccountPayable.due_date == month
        ).all()

        total_amount = sum(p.amount for p in payables)
        paid_amount = sum(p.amount for p in payables if p.paid)
        unpaid_amount = sum(p.amount for p in payables if not p.paid)

        return {
            "month": month,
            "total_count": len(payables),
            "total_amount": float(total_amount),
            "paid_count": sum(1 for p in payables if p.paid),
            "paid_amount": float(paid_amount),
            "unpaid_count": sum(1 for p in payables if not p.paid),
            "unpaid_amount": float(unpaid_amount)
        }
