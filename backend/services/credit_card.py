"""
CRUD service for CreditCard operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.credit_card import CreditCard
from models.card_installment import CardInstallment
from schemas.credit_card import CreditCardCreate, CreditCardUpdate


class CreditCardService:
    """Service for managing CreditCard operations"""

    @staticmethod
    def create(db: Session, card_data: CreditCardCreate) -> CreditCard:
        """Create a new credit card"""
        try:
            card = CreditCard(**card_data.model_dump())
            db.add(card)
            db.commit()
            db.refresh(card)
            return card
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit card with this name already exists"
            )

    @staticmethod
    def get_by_id(db: Session, card_id: UUID) -> CreditCard:
        """Get credit card by ID"""
        card = db.query(CreditCard).options(
            joinedload(CreditCard.participant)
        ).filter(CreditCard.id == card_id).first()
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credit card with id {card_id} not found"
            )
        return card

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[CreditCard]:
        """Get all credit cards"""
        return db.query(CreditCard).options(
            joinedload(CreditCard.participant)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, card_id: UUID, card_data: CreditCardUpdate) -> CreditCard:
        """Update an existing credit card"""
        card = CreditCardService.get_by_id(db, card_id)

        update_data = card_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        try:
            db.commit()
            db.refresh(card)
            return card
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit card with this name already exists"
            )

    @staticmethod
    def delete(db: Session, card_id: UUID) -> None:
        """Delete a credit card, blocked if there are unpaid installments"""
        card = CreditCardService.get_by_id(db, card_id)

        pending = db.query(CardInstallment).filter(
            CardInstallment.credit_card_id == card_id,
            CardInstallment.paid == False
        ).count()

        if pending > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede eliminar la tarjeta: tiene {pending} cuota(s) pendiente(s) de pago."
            )

        db.delete(card)
        db.commit()
