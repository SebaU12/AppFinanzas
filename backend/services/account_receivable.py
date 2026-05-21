"""
Business logic for AccountReceivable operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.account_receivable import AccountReceivable
from schemas.account_receivable import AccountReceivableCreate, AccountReceivableUpdate


class AccountReceivableService:
    """Service for managing accounts receivable"""

    @staticmethod
    def create(db: Session, receivable: AccountReceivableCreate) -> AccountReceivable:
        """Create a new account receivable"""
        db_receivable = AccountReceivable(**receivable.model_dump())
        db.add(db_receivable)
        db.commit()
        db.refresh(db_receivable)
        return db_receivable

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        due_date: str | None = None,
        received: bool | None = None,
        participant_id: UUID | None = None
    ) -> list[AccountReceivable]:
        """Get all accounts receivable with optional filtering"""
        query = db.query(AccountReceivable)

        if due_date is not None:
            query = query.filter(AccountReceivable.due_date == due_date)

        if received is not None:
            query = query.filter(AccountReceivable.received == received)

        if participant_id is not None:
            query = query.filter(AccountReceivable.participant_id == participant_id)

        return query.order_by(AccountReceivable.due_date).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, receivable_id: UUID) -> AccountReceivable:
        """Get a specific account receivable by ID"""
        receivable = db.query(AccountReceivable).filter(AccountReceivable.id == receivable_id).first()
        if not receivable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AccountReceivable with id {receivable_id} not found"
            )
        return receivable

    @staticmethod
    def update(db: Session, receivable_id: UUID, receivable_update: AccountReceivableUpdate) -> AccountReceivable:
        """Update an existing account receivable"""
        db_receivable = AccountReceivableService.get_by_id(db, receivable_id)

        update_data = receivable_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_receivable, field, value)

        db.commit()
        db.refresh(db_receivable)
        return db_receivable

    @staticmethod
    def delete(db: Session, receivable_id: UUID) -> None:
        """Delete an account receivable"""
        db_receivable = AccountReceivableService.get_by_id(db, receivable_id)
        db.delete(db_receivable)
        db.commit()

    @staticmethod
    def get_monthly_summary(db: Session, month: str) -> dict:
        """Get summary of accounts receivable for a specific month"""
        receivables = db.query(AccountReceivable).filter(
            AccountReceivable.due_date == month
        ).all()

        total_amount = sum(r.amount for r in receivables)
        received_amount = sum(r.amount for r in receivables if r.received)
        pending_amount = sum(r.amount for r in receivables if not r.received)

        return {
            "month": month,
            "total_count": len(receivables),
            "total_amount": float(total_amount),
            "received_count": sum(1 for r in receivables if r.received),
            "received_amount": float(received_amount),
            "pending_count": sum(1 for r in receivables if not r.received),
            "pending_amount": float(pending_amount)
        }
