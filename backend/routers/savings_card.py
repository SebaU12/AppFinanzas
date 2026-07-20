from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.savings_card import SavingsCardCreate, SavingsCardUpdate, SavingsCardResponse
from services.savings_card import SavingsCardService

router = APIRouter(prefix="/savings-cards", tags=["savings-cards"])


@router.post("/", response_model=SavingsCardResponse, status_code=201)
def create_savings_card(card_data: SavingsCardCreate, db: Session = Depends(get_db)):
    return SavingsCardService.create(db, card_data)


@router.get("/", response_model=list[SavingsCardResponse])
def get_savings_cards(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    return SavingsCardService.get_all(db, skip, limit, active_only)


@router.get("/{card_id}", response_model=SavingsCardResponse)
def get_savings_card(card_id: UUID, db: Session = Depends(get_db)):
    return SavingsCardService.get_by_id(db, card_id)


@router.put("/{card_id}", response_model=SavingsCardResponse)
def update_savings_card(
    card_id: UUID, card_data: SavingsCardUpdate, db: Session = Depends(get_db)
):
    return SavingsCardService.update(db, card_id, card_data)


@router.delete("/{card_id}", status_code=204)
def delete_savings_card(card_id: UUID, db: Session = Depends(get_db)):
    SavingsCardService.delete(db, card_id)
    return None
