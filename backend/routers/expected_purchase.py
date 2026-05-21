"""
API routes for ExpectedPurchase operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.expected_purchase import ExpectedPurchaseCreate, ExpectedPurchaseUpdate, ExpectedPurchaseResponse
from schemas.transaction import TransactionResponse
from services.expected_purchase import ExpectedPurchaseService

router = APIRouter(
    prefix="/expected-purchases",
    tags=["expected-purchases"]
)


@router.post("/", response_model=ExpectedPurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_expected_purchase(
    purchase: ExpectedPurchaseCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new expected purchase for simulation.

    Expected purchases allow "what-if" analysis without creating actual transactions.

    - **description**: Purchase description (required)
    - **amount**: Purchase amount (required, positive)
    - **expected_date**: Expected date in YYYY-MM-DD format (required)
    - **category_id**: Category ID (required)
    - **participant_id**: Participant ID (required)
    - **payment_method**: Payment method (required: cash, debit, or credit)
    - **card_id**: Credit card ID (required if payment_method is credit)
    - **installments**: Number of installments (required if payment_method is credit, 1-36)
    """
    return ExpectedPurchaseService.create(db, purchase)


@router.get("/", response_model=list[ExpectedPurchaseResponse])
def get_expected_purchases(
    skip: int = 0,
    limit: int = 100,
    converted: bool | None = Query(None, description="Filter by conversion status"),
    db: Session = Depends(get_db)
):
    """
    Get all expected purchases.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **converted**: Filter by whether purchase has been converted to transaction
    """
    return ExpectedPurchaseService.get_all(
        db,
        skip=skip,
        limit=limit,
        converted=converted
    )


@router.get("/{purchase_id}", response_model=ExpectedPurchaseResponse)
def get_expected_purchase(
    purchase_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific expected purchase by ID.
    """
    return ExpectedPurchaseService.get_by_id(db, purchase_id)


@router.get("/{purchase_id}/simulate")
def simulate_expected_purchase(
    purchase_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Simulate the financial impact of an expected purchase.

    Returns detailed analysis including:
    - Monthly cash flow impact (especially for installment purchases)
    - Budget impact per category per month
    - Projected spending vs budget limits
    - Total cost breakdown

    This helps answer questions like:
    - "If I buy this laptop in 6 installments, will I exceed my budget?"
    - "How will this purchase affect my cash flow over the next year?"
    - "Which months will be tight if I make this purchase?"
    """
    return ExpectedPurchaseService.simulate(db, purchase_id)


@router.put("/{purchase_id}", response_model=ExpectedPurchaseResponse)
def update_expected_purchase(
    purchase_id: UUID,
    purchase: ExpectedPurchaseUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing expected purchase.

    Cannot update purchases that have been converted to transactions.
    """
    return ExpectedPurchaseService.update(db, purchase_id, purchase)


@router.post("/{purchase_id}/convert", response_model=TransactionResponse)
def convert_to_transaction(
    purchase_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Convert an expected purchase into an actual transaction.

    This creates a real transaction with all the details from the expected purchase
    and marks the expected purchase as converted.

    Useful workflow:
    1. Create expected purchase for planning
    2. Simulate to check impact
    3. Convert to transaction when ready to commit
    """
    return ExpectedPurchaseService.convert_to_transaction(db, purchase_id)


@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expected_purchase(
    purchase_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an expected purchase.

    Cannot delete purchases that have been converted to transactions.
    """
    ExpectedPurchaseService.delete(db, purchase_id)
    return None
