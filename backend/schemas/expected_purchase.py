"""
Pydantic schemas for ExpectedPurchase operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from models.transaction import PaymentMethod
import re


class ExpectedPurchaseBase(BaseModel):
    """Base schema for ExpectedPurchase"""
    description: str = Field(..., max_length=500, description="Purchase description")
    amount: Decimal = Field(..., gt=0, description="Purchase amount")
    expected_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Expected date in YYYY-MM-DD format")
    category_id: UUID = Field(..., description="Category ID")
    participant_id: UUID = Field(..., description="Participant ID")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    card_id: UUID | None = Field(None, description="Credit card ID (required if payment_method is credit)")
    installment_count: int | None = Field(None, ge=1, le=36, description="Number of installment_count (1-36)")

    @field_validator('expected_date')
    @classmethod
    def validate_expected_date(cls, v):
        """Validate expected_date format"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('expected_date must be in YYYY-MM-DD format')
        return v

    @field_validator('card_id')
    @classmethod
    def validate_card_id_for_credit(cls, v, info):
        """Validate card_id is provided for credit purchases"""
        payment_method = info.data.get('payment_method')
        if payment_method == PaymentMethod.CREDIT and not v:
            raise ValueError('card_id is required when payment_method is credit')
        if payment_method != PaymentMethod.CREDIT and v:
            raise ValueError('card_id should only be provided when payment_method is credit')
        return v

    @field_validator('installment_count')
    @classmethod
    def validate_installment_count_for_credit(cls, v, info):
        """Validate installment_count is provided for credit purchases"""
        payment_method = info.data.get('payment_method')
        if payment_method == PaymentMethod.CREDIT and not v:
            raise ValueError('installment_count is required when payment_method is credit')
        if payment_method != PaymentMethod.CREDIT and v:
            raise ValueError('installment_count should only be provided when payment_method is credit')
        return v


class ExpectedPurchaseCreate(ExpectedPurchaseBase):
    """Schema for creating a new ExpectedPurchase"""
    pass


class ExpectedPurchaseUpdate(BaseModel):
    """Schema for updating an ExpectedPurchase"""
    description: str | None = Field(None, max_length=500)
    amount: Decimal | None = Field(None, gt=0)
    expected_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    category_id: UUID | None = None
    participant_id: UUID | None = None
    payment_method: PaymentMethod | None = None
    card_id: UUID | None = None
    installment_count: int | None = Field(None, ge=1, le=36)


class ExpectedPurchaseResponse(ExpectedPurchaseBase):
    """Schema for ExpectedPurchase response"""
    id: UUID
    converted_to_transaction: bool
    transaction_id: UUID | None

    class Config:
        from_attributes = True


class SimulationResult(BaseModel):
    """Schema for simulation results"""
    expected_purchase: ExpectedPurchaseResponse
    impact_summary: dict
    monthly_impact: list[dict]
    budget_impact: list[dict] | None = None
