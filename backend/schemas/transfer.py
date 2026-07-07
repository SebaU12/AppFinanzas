"""
Pydantic schemas for Transfer operations.
"""
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from pydantic import BaseModel, Field, field_validator
from models.transfer import TransferSourceType
from models.transaction import Currency


class TransferCreate(BaseModel):
    date: date_type
    amount: Decimal = Field(..., gt=0)
    currency: Currency = Currency.PEN
    from_type: TransferSourceType
    from_debit_card_id: UUID | None = None
    to_debit_card_id: UUID
    description: str | None = Field(None, max_length=500)

    @field_validator('from_debit_card_id')
    @classmethod
    def validate_from_card(cls, v, info):
        from_type = info.data.get('from_type')
        if from_type == TransferSourceType.DEBIT and not v:
            raise ValueError('from_debit_card_id is required when from_type is debit')
        if from_type == TransferSourceType.CASH and v:
            raise ValueError('from_debit_card_id must be empty when from_type is cash')
        return v


class TransferResponse(BaseModel):
    id: UUID
    date: date_type
    amount: Decimal
    currency: Currency
    from_type: TransferSourceType
    from_debit_card_id: UUID | None
    to_debit_card_id: UUID
    description: str | None
    from_debit_card_name: str | None = None
    to_debit_card_name: str | None = None

    class Config:
        from_attributes = True
