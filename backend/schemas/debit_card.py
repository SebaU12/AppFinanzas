"""
Pydantic schemas for DebitCard operations.
"""
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.participant import ParticipantResponse


class DebitCardBase(BaseModel):
    """Base schema for DebitCard"""
    name: str = Field(..., min_length=1, max_length=100, description="Card/account name")
    participant_id: UUID = Field(..., description="Owner participant ID")
    initial_balance: Decimal = Field(default=0, decimal_places=2, description="Starting balance")
    last_four_digits: str | None = Field(None, min_length=4, max_length=4, description="Last 4 digits")
    active: bool = Field(default=True, description="Whether card is active")


class DebitCardCreate(DebitCardBase):
    """Schema for creating a new DebitCard"""
    pass


class DebitCardUpdate(BaseModel):
    """Schema for updating a DebitCard"""
    name: str | None = None
    initial_balance: Decimal | None = None
    last_four_digits: str | None = None
    active: bool | None = None


class DebitCardResponse(DebitCardBase):
    """Schema for DebitCard response"""
    id: UUID
    participant: 'ParticipantResponse | None' = None
    current_balance: Decimal | None = None  # Calculated from transactions

    class Config:
        from_attributes = True


# Import to resolve forward references
from schemas.participant import ParticipantResponse

# Update forward references
DebitCardResponse.model_rebuild()
