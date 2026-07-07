"""
CRUD service for Transfer operations.
"""
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.transfer import Transfer, TransferSourceType
from models.debit_card import DebitCard
from schemas.transfer import TransferCreate


class TransferService:

    @staticmethod
    def create(db: Session, data: TransferCreate) -> dict:
        # Validate destination card exists
        to_card = db.query(DebitCard).filter(DebitCard.id == data.to_debit_card_id).first()
        if not to_card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Destination debit card {data.to_debit_card_id} not found")

        # Validate source card if debit
        if data.from_type == TransferSourceType.DEBIT:
            from_card = db.query(DebitCard).filter(DebitCard.id == data.from_debit_card_id).first()
            if not from_card:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Source debit card {data.from_debit_card_id} not found")
            if data.from_debit_card_id == data.to_debit_card_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Source and destination cards cannot be the same")

        transfer = Transfer(**data.model_dump())
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return TransferService._enrich(db, transfer)

    @staticmethod
    def get_all(db: Session, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
        query = db.query(Transfer).options(
            joinedload(Transfer.from_debit_card),
            joinedload(Transfer.to_debit_card)
        )
        if start_date:
            query = query.filter(Transfer.date >= start_date)
        if end_date:
            query = query.filter(Transfer.date <= end_date)
        transfers = query.order_by(Transfer.date.desc()).all()
        return [TransferService._enrich(db, t) for t in transfers]

    @staticmethod
    def get_by_id(db: Session, transfer_id: UUID) -> dict:
        transfer = db.query(Transfer).options(
            joinedload(Transfer.from_debit_card),
            joinedload(Transfer.to_debit_card)
        ).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Transfer {transfer_id} not found")
        return TransferService._enrich(db, transfer)

    @staticmethod
    def delete(db: Session, transfer_id: UUID) -> None:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Transfer {transfer_id} not found")
        db.delete(transfer)
        db.commit()

    @staticmethod
    def _enrich(db: Session, transfer: Transfer) -> dict:
        return {
            "id": transfer.id,
            "date": transfer.date,
            "amount": transfer.amount,
            "currency": transfer.currency,
            "from_type": transfer.from_type,
            "from_debit_card_id": transfer.from_debit_card_id,
            "to_debit_card_id": transfer.to_debit_card_id,
            "description": transfer.description,
            "from_debit_card_name": transfer.from_debit_card.name if transfer.from_debit_card else None,
            "to_debit_card_name": transfer.to_debit_card.name if transfer.to_debit_card else None,
        }
