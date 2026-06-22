"""
Business logic for ExchangeRate operations.

Also provides convert_to_pen(), the central helper used by all services
that need to aggregate amounts across currencies.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.exchange_rate import ExchangeRate
from models.transaction import Currency
from schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate


class ExchangeRateService:

    # ------------------------------------------------------------------ #
    #  Core conversion helper — used by reimbursement, budget, statements  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def convert_to_pen(db: Session, amount: Decimal, currency: Currency, month: str) -> Decimal:
        """
        Convert an amount in any currency to PEN using the configured monthly rate.

        If currency is already PEN, the amount is returned unchanged.
        Raises HTTP 400 if the required rate has not been configured.
        """
        if currency == Currency.PEN:
            return amount

        rate_obj = db.query(ExchangeRate).filter(
            ExchangeRate.month == month,
            ExchangeRate.from_currency == currency,
            ExchangeRate.to_currency == Currency.PEN,
        ).first()

        if rate_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No hay tipo de cambio configurado para {currency.value}→PEN "
                    f"en el mes {month}. Configure el tipo de cambio antes de calcular."
                ),
            )

        return amount * Decimal(str(rate_obj.rate))

    # ------------------------------------------------------------------ #
    #  CRUD                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create(db: Session, data: ExchangeRateCreate) -> ExchangeRate:
        try:
            obj = ExchangeRate(**data.model_dump())
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Ya existe un tipo de cambio para "
                    f"{data.from_currency.value}→{data.to_currency.value} en {data.month}"
                ),
            )

    @staticmethod
    def upsert(db: Session, data: ExchangeRateCreate) -> ExchangeRate:
        """Create or update the rate for a given month+pair."""
        obj = db.query(ExchangeRate).filter(
            ExchangeRate.month == data.month,
            ExchangeRate.from_currency == data.from_currency,
            ExchangeRate.to_currency == data.to_currency,
        ).first()

        if obj:
            obj.rate = data.rate
        else:
            obj = ExchangeRate(**data.model_dump())
            db.add(obj)

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_all(db: Session, month: str | None = None) -> list[ExchangeRate]:
        query = db.query(ExchangeRate)
        if month:
            query = query.filter(ExchangeRate.month == month)
        return query.order_by(ExchangeRate.month.desc()).all()

    @staticmethod
    def get_by_id(db: Session, rate_id: UUID) -> ExchangeRate:
        obj = db.query(ExchangeRate).filter(ExchangeRate.id == rate_id).first()
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Tipo de cambio {rate_id} no encontrado")
        return obj

    @staticmethod
    def get_by_month(db: Session, month: str) -> list[ExchangeRate]:
        return db.query(ExchangeRate).filter(ExchangeRate.month == month).all()

    @staticmethod
    def update(db: Session, rate_id: UUID, data: ExchangeRateUpdate) -> ExchangeRate:
        obj = ExchangeRateService.get_by_id(db, rate_id)
        obj.rate = data.rate
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, rate_id: UUID) -> None:
        obj = ExchangeRateService.get_by_id(db, rate_id)
        db.delete(obj)
        db.commit()
