"""
API routes for DebitCard operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.debit_card import DebitCardCreate, DebitCardUpdate, DebitCardResponse
from services.debit_card import DebitCardService

router = APIRouter(
    prefix="/debit-cards",
    tags=["debit-cards"]
)


@router.post("/", response_model=DebitCardResponse, status_code=201)
def create_debit_card(
    card_data: DebitCardCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new debit card / bank account.
    """
    card = DebitCardService.create(db, card_data)
    return card


@router.get("/", response_model=list[DebitCardResponse])
def get_debit_cards(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all debit cards with calculated balances.
    """
    cards_with_balances = DebitCardService.get_all_with_balances(db, skip, limit, active_only)

    # Map to response schema with current_balance
    return [
        DebitCardResponse(
            **card["card"].__dict__,
            current_balance=card["current_balance"]
        )
        for card in cards_with_balances
    ]


@router.get("/{card_id}", response_model=DebitCardResponse)
def get_debit_card(
    card_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific debit card by ID with current balance.
    """
    card = DebitCardService.get_by_id(db, card_id)
    current_balance = DebitCardService.get_current_balance(db, card_id)

    return DebitCardResponse(
        **card.__dict__,
        current_balance=current_balance
    )


@router.get("/{card_id}/balance")
def get_debit_card_balance(
    card_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get the current balance of a debit card.
    """
    balance = DebitCardService.get_current_balance(db, card_id)
    return {"card_id": card_id, "current_balance": float(balance)}


@router.put("/{card_id}", response_model=DebitCardResponse)
def update_debit_card(
    card_id: UUID,
    card_data: DebitCardUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a debit card.
    """
    card = DebitCardService.update(db, card_id, card_data)
    current_balance = DebitCardService.get_current_balance(db, card_id)

    return DebitCardResponse(
        **card.__dict__,
        current_balance=current_balance
    )


@router.delete("/{card_id}", status_code=204)
def delete_debit_card(
    card_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a debit card.
    """
    DebitCardService.delete(db, card_id)
    return None
