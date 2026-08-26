"""
CRUD service for CardInstallment operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.card_installment import CardInstallment
from models.transaction import Transaction
from schemas.card_installment import CardInstallmentCreate, CardInstallmentUpdate


class CardInstallmentService:
    """Service for managing CardInstallment operations"""

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
        credit_card_id: UUID | None = None,
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
        if credit_card_id:
            query = query.filter(CardInstallment.credit_card_id == credit_card_id)
        if month:
            query = query.filter(CardInstallment.month == month)
        if paid is not None:
            query = query.filter(CardInstallment.paid == paid)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, installment_id: UUID, installment_data: CardInstallmentUpdate) -> CardInstallment:
        """Update an existing card installment (typically to mark as paid)"""
        installment = CardInstallmentService.get_by_id(db, installment_id)

        update_data = installment_data.model_dump(exclude_unset=True)

        # Update the installment
        for field, value in update_data.items():
            setattr(installment, field, value)

        db.commit()
        db.refresh(installment)
        return installment

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
