"""
Pydantic schemas for ExchangeRate operations.
"""
import re
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from models.transaction import Currency


class ExchangeRateBase(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format")
    from_currency: Currency = Field(..., description="Source currency (e.g. USD)")
    to_currency: Currency = Field(Currency.PEN, description="Target currency (always PEN)")
    rate: Decimal = Field(..., gt=0, decimal_places=6, description="Units of to_currency per 1 from_currency")

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("month must be in YYYY-MM format")
        return v

    @field_validator("from_currency")
    @classmethod
    def validate_from_currency(cls, v: Currency) -> Currency:
        if v == Currency.PEN:
            raise ValueError("from_currency cannot be PEN (PEN is the base currency)")
        return v


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRateUpdate(BaseModel):
    rate: Decimal = Field(..., gt=0, description="New exchange rate")


class ExchangeRateResponse(ExchangeRateBase):
    id: UUID

    class Config:
        from_attributes = True
