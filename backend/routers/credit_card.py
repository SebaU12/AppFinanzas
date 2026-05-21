"""
API routes for CreditCard operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.credit_card import CreditCardCreate, CreditCardUpdate, CreditCardResponse
from services.credit_card import CreditCardService

router = APIRouter(
    prefix="/credit-cards",
    tags=["credit-cards"]
)


@router.post("/", response_model=CreditCardResponse, status_code=status.HTTP_201_CREATED)
def create_credit_card(
    card: CreditCardCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new credit card.

    - **name**: Credit card name (required, unique)
    - **closing_day**: Closing day of month (1-31)
    - **payment_day**: Payment day of month (1-31)
    """
    return CreditCardService.create(db, card)


@router.get("/", response_model=list[CreditCardResponse])
def get_credit_cards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all credit cards.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    return CreditCardService.get_all(db, skip=skip, limit=limit)


@router.get("/{card_id}", response_model=CreditCardResponse)
def get_credit_card(
    card_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific credit card by ID.
    """
    return CreditCardService.get_by_id(db, card_id)


@router.put("/{card_id}", response_model=CreditCardResponse)
def update_credit_card(
    card_id: UUID,
    card: CreditCardUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing credit card.

    All fields are optional. Only provided fields will be updated.
    """
    return CreditCardService.update(db, card_id, card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credit_card(
    card_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a credit card.
    """
    CreditCardService.delete(db, card_id)
    return None
