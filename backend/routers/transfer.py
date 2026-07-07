"""
API routes for Transfer operations.
"""
from uuid import UUID
from datetime import date
from calendar import monthrange
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.transfer import TransferCreate, TransferResponse
from services.transfer import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(transfer: TransferCreate, db: Session = Depends(get_db)):
    """Create a new transfer between accounts."""
    return TransferService.create(db, transfer)


@router.get("/", response_model=list[TransferResponse])
def get_transfers(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db)
):
    """Get all transfers, optionally filtered by date range."""
    return TransferService.get_all(db, start_date, end_date)


@router.get("/month/{month}", response_model=list[TransferResponse])
def get_transfers_by_month(month: str, db: Session = Depends(get_db)):
    """Get all transfers for a specific month (YYYY-MM)."""
    year, month_num = map(int, month.split('-'))
    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, monthrange(year, month_num)[1])
    return TransferService.get_all(db, start_date, end_date)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(transfer_id: UUID, db: Session = Depends(get_db)):
    return TransferService.get_by_id(db, transfer_id)


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(transfer_id: UUID, db: Session = Depends(get_db)):
    TransferService.delete(db, transfer_id)
    return None
