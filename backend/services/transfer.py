"""
CRUD service for Transfer operations.
"""
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from models.transfer import Transfer, TransferSourceType, TransferDestinationType
from models.debit_card import DebitCard
from models.savings_card import SavingsCard
from schemas.transfer import TransferCreate


class TransferService:

    @staticmethod
    def create(db: Session, data: TransferCreate) -> dict:
        source_account = None
        if data.from_type == TransferSourceType.DEBIT:
            source_account = db.query(DebitCard).filter(DebitCard.id == data.from_debit_card_id).first()
            if not source_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Source debit card {data.from_debit_card_id} not found")
        elif data.from_type == TransferSourceType.SAVINGS:
            source_account = db.query(SavingsCard).filter(SavingsCard.id == data.from_savings_card_id).first()
            if not source_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Source savings account {data.from_savings_card_id} not found")

        destination_account = None
        if data.to_type == TransferDestinationType.DEBIT:
            destination_account = db.query(DebitCard).filter(DebitCard.id == data.to_debit_card_id).first()
            if not destination_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Destination debit card {data.to_debit_card_id} not found")
        elif data.to_type == TransferDestinationType.SAVINGS:
            destination_account = db.query(SavingsCard).filter(SavingsCard.id == data.to_savings_card_id).first()
            if not destination_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Destination savings account {data.to_savings_card_id} not found")

        if source_account and destination_account and source_account.id == destination_account.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Source and destination accounts cannot be the same")

        transfer = Transfer(**data.model_dump())
        db.add(transfer)
        db.commit()
        # Reload with relationships for enrichment
        transfer = db.query(Transfer).options(
            joinedload(Transfer.from_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.from_savings_card).joinedload(SavingsCard.participant),
            joinedload(Transfer.to_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.to_savings_card).joinedload(SavingsCard.participant),
        ).filter(Transfer.id == transfer.id).first()
        return TransferService._enrich(db, transfer)

    @staticmethod
    def get_all(db: Session, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
        query = db.query(Transfer).options(
            joinedload(Transfer.from_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.from_savings_card).joinedload(SavingsCard.participant),
            joinedload(Transfer.to_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.to_savings_card).joinedload(SavingsCard.participant),
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
            joinedload(Transfer.from_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.from_savings_card).joinedload(SavingsCard.participant),
            joinedload(Transfer.to_debit_card).joinedload(DebitCard.participant),
            joinedload(Transfer.to_savings_card).joinedload(SavingsCard.participant),
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
        def account_label(account):
            if not account:
                return None
            participant_name = account.participant.name if account.participant else None
            return f"{account.name} ({participant_name})" if participant_name else account.name

        from_account = transfer.from_debit_card if transfer.from_type == TransferSourceType.DEBIT else transfer.from_savings_card
        to_account = transfer.to_debit_card if transfer.to_type == TransferDestinationType.DEBIT else transfer.to_savings_card

        return {
            "id": transfer.id,
            "date": transfer.date,
            "amount": transfer.amount,
            "currency": transfer.currency,
            "from_type": transfer.from_type,
            "to_type": transfer.to_type,
            "from_debit_card_id": transfer.from_debit_card_id,
            "from_savings_card_id": transfer.from_savings_card_id,
            "to_debit_card_id": transfer.to_debit_card_id,
            "to_savings_card_id": transfer.to_savings_card_id,
            "description": transfer.description,
            "from_account_name": account_label(from_account),
            "to_account_name": account_label(to_account),
        }
