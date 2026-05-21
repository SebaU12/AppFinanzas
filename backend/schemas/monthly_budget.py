"""
Pydantic schemas for MonthlyBudget operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
import re


class MonthlyBudgetBase(BaseModel):
    """Base schema for MonthlyBudget"""
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format")
    category_id: UUID = Field(..., description="Category ID")
    budgeted_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Budgeted amount")

    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v):
        """Validate month format YYYY-MM"""
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError('Month must be in YYYY-MM format with valid month (01-12)')
        return v

    @field_validator('budgeted_amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is non-negative"""
        if v < 0:
            raise ValueError('Budgeted amount must be non-negative')
        return v


class MonthlyBudgetCreate(MonthlyBudgetBase):
    """Schema for creating a new MonthlyBudget"""
    pass


class MonthlyBudgetUpdate(BaseModel):
    """Schema for updating a MonthlyBudget"""
    budgeted_amount: Decimal | None = Field(None, ge=0, decimal_places=2)

    @field_validator('budgeted_amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is non-negative"""
        if v is not None and v < 0:
            raise ValueError('Budgeted amount must be non-negative')
        return v


class MonthlyBudgetResponse(MonthlyBudgetBase):
    """Schema for MonthlyBudget response"""
    id: UUID

    class Config:
        from_attributes = True
