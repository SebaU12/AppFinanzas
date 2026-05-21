"""
Pydantic schemas for MonthlyReimbursement operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from schemas.participant import ParticipantResponse


class ReimbursementDetailResponse(BaseModel):
    """Schema for ReimbursementDetail in responses"""
    id: UUID
    participant_id: UUID
    amount_paid: Decimal
    expected_share: Decimal
    balance: Decimal
    percentage: Decimal
    participant: 'ParticipantResponse | None' = None

    class Config:
        from_attributes = True


class MonthlyReimbursementBase(BaseModel):
    """Base schema for MonthlyReimbursement"""
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format")
    total_shared_expenses: Decimal = Field(default=0, description="Total shared expenses for the month")
    total_shared_income: Decimal = Field(default=0, description="Total shared income for the month")
    finalized: bool = Field(default=False, description="Whether reimbursement is finalized")
    finalized_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date finalized")

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('month must be in YYYY-MM format')
        return v


class MonthlyReimbursementCreate(BaseModel):
    """Schema for creating a new MonthlyReimbursement"""
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format")

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """Validate month format"""
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('month must be in YYYY-MM format')
        return v


class MonthlyReimbursementUpdate(BaseModel):
    """Schema for updating a MonthlyReimbursement"""
    finalized: bool | None = None
    finalized_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class MonthlyReimbursementResponse(MonthlyReimbursementBase):
    """Schema for MonthlyReimbursement response"""
    id: UUID
    details: list[ReimbursementDetailResponse] = []

    class Config:
        from_attributes = True


# Import to resolve forward references
from schemas.participant import ParticipantResponse

# Update forward references
ReimbursementDetailResponse.model_rebuild()
