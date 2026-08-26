"""
Pydantic schemas for CreditCard operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import TYPE_CHECKING
from models.transaction import Currency

if TYPE_CHECKING:
    from schemas.participant import ParticipantResponse


class CreditCardBase(BaseModel):
    """Base schema for CreditCard"""
    name: str = Field(..., min_length=1, max_length=100, description="Credit card name")
    participant_id: UUID = Field(..., description="Participant who owns this card")
    closing_day: int = Field(..., ge=1, le=31, description="Closing day of month (1-31)")
    payment_day: int = Field(..., ge=1, le=31, description="Payment day of month (1-31)")
    credit_limit: Decimal = Field(default=Decimal('5000'), gt=0, description="Credit limit in currency")
    currency: Currency = Field(default=Currency.PEN, description="Card currency: PEN or USD")

    @field_validator('closing_day', 'payment_day')
    @classmethod
    def validate_day(cls, v):
        """Validate day is between 1 and 31"""
        if not 1 <= v <= 31:
            raise ValueError('Day must be between 1 and 31')
        return v


class CreditCardCreate(CreditCardBase):
    """Schema for creating a new CreditCard"""
    pass


class CreditCardUpdate(BaseModel):
    """Schema for updating a CreditCard"""
    name: str | None = Field(None, min_length=1, max_length=100)
    participant_id: UUID | None = None
    closing_day: int | None = Field(None, ge=1, le=31)
    payment_day: int | None = Field(None, ge=1, le=31)
    credit_limit: Decimal | None = Field(None, gt=0)
    currency: Currency | None = None

    @field_validator('closing_day', 'payment_day')
    @classmethod
    def validate_day(cls, v):
        """Validate day is between 1 and 31"""
        if v is not None and not 1 <= v <= 31:
            raise ValueError('Day must be between 1 and 31')
        return v


class CreditCardResponse(CreditCardBase):
    """Schema for CreditCard response"""
    id: UUID
    participant: 'ParticipantResponse | None' = None

    class Config:
        from_attributes = True


# Import to resolve forward references
from schemas.participant import ParticipantResponse

# Update forward references
CreditCardResponse.model_rebuild()
