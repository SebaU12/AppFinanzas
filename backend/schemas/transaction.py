"""
Pydantic schemas for Transaction operations.
"""
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from pydantic import BaseModel, Field, field_validator
from models.transaction import PaymentMethod, Currency
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.category import CategoryResponse
    from schemas.participant import ParticipantResponse


class TransactionBase(BaseModel):
    """Base schema for Transaction"""
    date: date_type = Field(..., description="Transaction date")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    category_id: UUID = Field(..., description="Category ID")
    participant_id: UUID = Field(..., description="Participant ID")
    payment_method: PaymentMethod = Field(..., description="Payment method: cash, debit, or credit")
    card_id: UUID | None = Field(None, description="Credit card ID (required if payment_method is credit)")
    debit_card_id: UUID | None = Field(None, description="Debit card ID (optional for debit transactions)")
    is_credit: bool = Field(default=False, description="Whether this is a credit transaction")
    installment_count: int | None = Field(None, ge=1, le=36, description="Number of installments (1-36)")
    currency: Currency = Field(default=Currency.PEN, description="Transaction currency: PEN or USD")
    description: str | None = Field(None, max_length=500, description="Transaction description")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('installment_count')
    @classmethod
    def validate_installment_count(cls, v, info):
        """Validate installment_count logic"""
        if v is not None:
            if v < 1 or v > 36:
                raise ValueError('Installment count must be between 1 and 36')
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a new Transaction"""

    @field_validator('card_id')
    @classmethod
    def validate_card_id_for_credit(cls, v, info):
        """Validate card_id is provided for credit transactions"""
        payment_method = info.data.get('payment_method')
        is_credit = info.data.get('is_credit', False)

        if payment_method == PaymentMethod.CREDIT and not v:
            raise ValueError('card_id is required when payment_method is credit')

        if payment_method != PaymentMethod.CREDIT and v:
            raise ValueError('card_id should only be provided when payment_method is credit')

        return v

    @field_validator('is_credit')
    @classmethod
    def validate_is_credit_matches_payment_method(cls, v, info):
        """Validate is_credit matches payment_method"""
        payment_method = info.data.get('payment_method')

        if payment_method == PaymentMethod.CREDIT and not v:
            return True  # Auto-set to True for credit payments

        if payment_method != PaymentMethod.CREDIT and v:
            raise ValueError('is_credit should only be True when payment_method is credit')

        return v


class TransactionUpdate(BaseModel):
    """Schema for updating a Transaction"""
    date: date_type | None = None
    amount: Decimal | None = Field(None, gt=0)
    category_id: UUID | None = None
    participant_id: UUID | None = None
    description: str | None = Field(None, max_length=500)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v


class TransactionResponse(TransactionBase):
    """Schema for Transaction response"""
    id: UUID
    category: 'CategoryResponse | None' = None
    participant: 'ParticipantResponse | None' = None

    class Config:
        from_attributes = True


# Import to resolve forward references
from schemas.category import CategoryResponse
from schemas.participant import ParticipantResponse

# Update forward references
TransactionResponse.model_rebuild()
