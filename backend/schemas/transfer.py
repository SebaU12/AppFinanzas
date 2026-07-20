"""
Pydantic schemas for Transfer operations.
"""
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from pydantic import BaseModel, Field, model_validator
from models.transfer import TransferSourceType, TransferDestinationType
from models.transaction import Currency


class TransferCreate(BaseModel):
    date: date_type
    amount: Decimal = Field(..., gt=0)
    currency: Currency = Currency.PEN
    from_type: TransferSourceType
    to_type: TransferDestinationType
    from_debit_card_id: UUID | None = None
    from_savings_card_id: UUID | None = None
    to_debit_card_id: UUID | None = None
    to_savings_card_id: UUID | None = None
    description: str | None = Field(None, max_length=500)

    @model_validator(mode='after')
    def validate_accounts(self):
        if self.from_type == TransferSourceType.DEBIT and not self.from_debit_card_id:
            raise ValueError('from_debit_card_id is required when from_type is debit')
        if self.from_type != TransferSourceType.DEBIT and self.from_debit_card_id:
            raise ValueError('from_debit_card_id must be empty unless from_type is debit')

        if self.from_type == TransferSourceType.SAVINGS and not self.from_savings_card_id:
            raise ValueError('from_savings_card_id is required when from_type is savings')
        if self.from_type != TransferSourceType.SAVINGS and self.from_savings_card_id:
            raise ValueError('from_savings_card_id must be empty unless from_type is savings')

        if self.to_type == TransferDestinationType.DEBIT and not self.to_debit_card_id:
            raise ValueError('to_debit_card_id is required when to_type is debit')
        if self.to_type != TransferDestinationType.DEBIT and self.to_debit_card_id:
            raise ValueError('to_debit_card_id must be empty unless to_type is debit')

        if self.to_type == TransferDestinationType.SAVINGS and not self.to_savings_card_id:
            raise ValueError('to_savings_card_id is required when to_type is savings')
        if self.to_type != TransferDestinationType.SAVINGS and self.to_savings_card_id:
            raise ValueError('to_savings_card_id must be empty unless to_type is savings')

        return self


class TransferResponse(BaseModel):
    id: UUID
    date: date_type
    amount: Decimal
    currency: Currency
    from_type: TransferSourceType
    to_type: TransferDestinationType
    from_debit_card_id: UUID | None
    from_savings_card_id: UUID | None
    to_debit_card_id: UUID | None
    to_savings_card_id: UUID | None
    description: str | None
    from_account_name: str | None = None
    to_account_name: str | None = None

    class Config:
        from_attributes = True
