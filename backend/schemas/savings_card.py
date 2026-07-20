from uuid import UUID
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING
from models.transaction import Currency

if TYPE_CHECKING:
    from schemas.participant import ParticipantResponse


class SavingsCardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    participant_id: UUID
    last_four_digits: str | None = Field(None, min_length=4, max_length=4)
    active: bool = Field(default=True)
    currency: Currency = Field(default=Currency.PEN)


class SavingsCardCreate(SavingsCardBase):
    pass


class SavingsCardUpdate(BaseModel):
    name: str | None = None
    last_four_digits: str | None = None
    active: bool | None = None
    currency: Currency | None = None


class SavingsCardResponse(SavingsCardBase):
    id: UUID
    participant: 'ParticipantResponse | None' = None

    class Config:
        from_attributes = True


from schemas.participant import ParticipantResponse
SavingsCardResponse.model_rebuild()
