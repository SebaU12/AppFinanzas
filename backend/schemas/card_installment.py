"""
Pydantic schemas for CardInstallment operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from schemas.transaction import TransactionResponse


class CardInstallmentBase(BaseModel):
    """Base schema for CardInstallment"""
    transaction_id: UUID = Field(..., description="Transaction ID")
    credit_card_id: UUID = Field(..., description="Credit Card ID")
    installment_number: int = Field(..., ge=1, description="Installment number (1, 2, 3, etc.)")
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Installment amount")
    paid: bool = Field(default=False, description="Whether this installment has been paid")

    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v):
        """Validate month format YYYY-MM"""
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError('Month must be in YYYY-MM format with valid month (01-12)')
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class CardInstallmentCreate(CardInstallmentBase):
    """Schema for creating a new CardInstallment"""
    pass


class CardInstallmentUpdate(BaseModel):
    """Schema for updating a CardInstallment"""
    paid: bool | None = None


class CardInstallmentResponse(CardInstallmentBase):
    """Schema for CardInstallment response"""
    id: UUID
    transaction: 'TransactionResponse | None' = None

    class Config:
        from_attributes = True


# Import to resolve forward references
from schemas.transaction import TransactionResponse

# Update forward references
CardInstallmentResponse.model_rebuild()
