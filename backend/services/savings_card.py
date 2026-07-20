from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException, status

from models.savings_card import SavingsCard
from schemas.savings_card import SavingsCardCreate, SavingsCardUpdate


class SavingsCardService:

    @staticmethod
    def create(db: Session, card_data: SavingsCardCreate) -> SavingsCard:
        card = SavingsCard(**card_data.model_dump())
        db.add(card)
        db.commit()
        db.refresh(card)
        return card

    @staticmethod
    def get_by_id(db: Session, card_id: UUID) -> SavingsCard:
        card = db.query(SavingsCard).options(
            joinedload(SavingsCard.participant)
        ).filter(SavingsCard.id == card_id).first()
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Savings card with id {card_id} not found"
            )
        return card

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> list[SavingsCard]:
        query = db.query(SavingsCard).options(joinedload(SavingsCard.participant))
        if active_only:
            query = query.filter(SavingsCard.active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, card_id: UUID, card_data: SavingsCardUpdate) -> SavingsCard:
        card = SavingsCardService.get_by_id(db, card_id)
        for field, value in card_data.model_dump(exclude_unset=True).items():
            setattr(card, field, value)
        db.commit()
        db.refresh(card)
        return card

    @staticmethod
    def delete(db: Session, card_id: UUID) -> None:
        from models.transfer import Transfer

        card = SavingsCardService.get_by_id(db, card_id)

        transfer_count = db.query(Transfer).filter(
            or_(
                Transfer.from_savings_card_id == card_id,
                Transfer.to_savings_card_id == card_id,
            )
        ).count()

        if transfer_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete savings card: it has {transfer_count} associated transfer(s). "
                    "Delete or reassign those transfers first."
                ),
            )

        db.delete(card)
        db.commit()
