from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.savings_card import SavingsCardCreate, SavingsCardUpdate, SavingsCardResponse
from services.savings_card import SavingsCardService

router = APIRouter(prefix="/savings-cards", tags=["savings-cards"])


@router.post("/", response_model=SavingsCardResponse, status_code=201)
def create_savings_card(card_data: SavingsCardCreate, db: Session = Depends(get_db)):
    card = SavingsCardService.create(db, card_data)
    return SavingsCardResponse(**card.__dict__, current_balance=card.initial_balance)


@router.get("/", response_model=list[SavingsCardResponse])
def get_savings_cards(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    cards_with_balances = SavingsCardService.get_all_with_balances(db, skip, limit, active_only)
    return [
        SavingsCardResponse(**c["card"].__dict__, current_balance=c["current_balance"])
        for c in cards_with_balances
    ]


@router.get("/{card_id}", response_model=SavingsCardResponse)
def get_savings_card(card_id: UUID, db: Session = Depends(get_db)):
    card = SavingsCardService.get_by_id(db, card_id)
    balance = SavingsCardService.get_current_balance(db, card_id)
    return SavingsCardResponse(**card.__dict__, current_balance=balance)


@router.get("/{card_id}/balance")
def get_savings_card_balance(card_id: UUID, db: Session = Depends(get_db)):
    balance = SavingsCardService.get_current_balance(db, card_id)
    return {"card_id": card_id, "current_balance": float(balance)}


@router.put("/{card_id}", response_model=SavingsCardResponse)
def update_savings_card(
    card_id: UUID, card_data: SavingsCardUpdate, db: Session = Depends(get_db)
):
    card = SavingsCardService.update(db, card_id, card_data)
    balance = SavingsCardService.get_current_balance(db, card_id)
    return SavingsCardResponse(**card.__dict__, current_balance=balance)


@router.delete("/{card_id}", status_code=204)
def delete_savings_card(card_id: UUID, db: Session = Depends(get_db)):
    SavingsCardService.delete(db, card_id)
    return None
