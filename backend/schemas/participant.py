"""
Pydantic schemas for Participant operations.
"""
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ParticipantBase(BaseModel):
    """Base schema for Participant"""
    name: str = Field(..., min_length=1, max_length=100, description="Participant name")
    active: bool = Field(default=True, description="Whether participant is active in current month")
    default_percentage: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Default percentage for reimbursements"
    )

    @field_validator('default_percentage')
    @classmethod
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class ParticipantCreate(ParticipantBase):
    """Schema for creating a new Participant"""
    pass


class ParticipantUpdate(BaseModel):
    """Schema for updating a Participant"""
    name: str | None = Field(None, min_length=1, max_length=100)
    active: bool | None = None
    default_percentage: float | None = Field(None, ge=0.0, le=100.0)

    @field_validator('default_percentage')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class ParticipantResponse(ParticipantBase):
    """Schema for Participant response"""
    id: UUID

    class Config:
        from_attributes = True
