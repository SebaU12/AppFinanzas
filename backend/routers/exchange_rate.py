"""
API routes for ExchangeRate management.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from services.exchange_rate import ExchangeRateService
from schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])


@router.get("/", response_model=list[ExchangeRateResponse])
def list_rates(
    month: str | None = Query(None, description="Filter by month (YYYY-MM)"),
    db: Session = Depends(get_db),
):
    """List all configured exchange rates, optionally filtered by month."""
    return ExchangeRateService.get_all(db, month=month)


@router.get("/month/{month}", response_model=list[ExchangeRateResponse])
def get_rates_for_month(month: str, db: Session = Depends(get_db)):
    """Get all exchange rates configured for a specific month."""
    return ExchangeRateService.get_by_month(db, month)


@router.post("/", response_model=ExchangeRateResponse, status_code=201)
def create_rate(data: ExchangeRateCreate, db: Session = Depends(get_db)):
    """Create a new exchange rate for a month."""
    return ExchangeRateService.create(db, data)


@router.post("/upsert", response_model=ExchangeRateResponse)
def upsert_rate(data: ExchangeRateCreate, db: Session = Depends(get_db)):
    """Create or update the exchange rate for a month+currency pair."""
    return ExchangeRateService.upsert(db, data)


@router.put("/{rate_id}", response_model=ExchangeRateResponse)
def update_rate(rate_id: UUID, data: ExchangeRateUpdate, db: Session = Depends(get_db)):
    """Update the rate value of an existing exchange rate."""
    return ExchangeRateService.update(db, rate_id, data)


@router.delete("/{rate_id}", status_code=204)
def delete_rate(rate_id: UUID, db: Session = Depends(get_db)):
    """Delete an exchange rate."""
    ExchangeRateService.delete(db, rate_id)
