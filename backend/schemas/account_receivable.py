"""
Pydantic schemas for AccountReceivable operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
import re


class AccountReceivableBase(BaseModel):
    """Base schema for AccountReceivable"""
    description: str = Field(..., max_length=500, description="Payment description")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Due date in YYYY-MM format")
    received: bool = Field(default=False, description="Whether this has been received")
    received_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date received in YYYY-MM-DD format")
    participant_id: UUID | None = Field(None, description="Associated participant ID")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date format"""
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('due_date must be in YYYY-MM format')
        return v

    @field_validator('received_date')
    @classmethod
    def validate_received_date(cls, v):
        """Validate received_date format"""
        if v is not None and not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('received_date must be in YYYY-MM-DD format')
        return v


class AccountReceivableCreate(AccountReceivableBase):
    """Schema for creating a new AccountReceivable"""
    pass


class AccountReceivableUpdate(BaseModel):
    """Schema for updating an AccountReceivable"""
    description: str | None = Field(None, max_length=500)
    amount: Decimal | None = Field(None, gt=0)
    due_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}$")
    received: bool | None = None
    received_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class AccountReceivableResponse(AccountReceivableBase):
    """Schema for AccountReceivable response"""
    id: UUID

    class Config:
        from_attributes = True
