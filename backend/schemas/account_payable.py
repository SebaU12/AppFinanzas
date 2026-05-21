"""
Pydantic schemas for AccountPayable operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
import re


class AccountPayableBase(BaseModel):
    """Base schema for AccountPayable"""
    description: str = Field(..., max_length=500, description="Payment description")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Due date in YYYY-MM format")
    paid: bool = Field(default=False, description="Whether this has been paid")
    paid_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date paid in YYYY-MM-DD format")
    installment_id: UUID | None = Field(None, description="Associated installment ID")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date format"""
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('due_date must be in YYYY-MM format')
        return v

    @field_validator('paid_date')
    @classmethod
    def validate_paid_date(cls, v):
        """Validate paid_date format"""
        if v is not None and not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('paid_date must be in YYYY-MM-DD format')
        return v


class AccountPayableCreate(AccountPayableBase):
    """Schema for creating a new AccountPayable"""
    pass


class AccountPayableUpdate(BaseModel):
    """Schema for updating an AccountPayable"""
    description: str | None = Field(None, max_length=500)
    amount: Decimal | None = Field(None, gt=0)
    due_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}$")
    paid: bool | None = None
    paid_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class AccountPayableResponse(AccountPayableBase):
    """Schema for AccountPayable response"""
    id: UUID

    class Config:
        from_attributes = True
