"""
API routes for Transaction operations.
"""
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from models.transaction import PaymentMethod
from models.category import CategoryType
from schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from services.transaction import TransactionService

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction (income or expense).

    - **date**: Transaction date (required)
    - **amount**: Transaction amount (required, positive)
    - **category_id**: Category ID (required)
    - **participant_id**: Participant ID (required)
    - **payment_method**: Payment method: cash, debit, or credit (required)
    - **card_id**: Credit card ID (required if payment_method is credit)
    - **is_credit**: Whether this is a credit transaction (auto-set for credit payments)
    - **installments**: Number of installments for credit (1-36, optional)
    - **description**: Transaction description (optional)

    Note: Credit card usage is validated against category's allows_credit flag.
    """
    return TransactionService.create(db, transaction)


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    category_id: UUID | None = Query(None, description="Filter by category ID"),
    participant_id: UUID | None = Query(None, description="Filter by participant ID"),
    payment_method: PaymentMethod | None = Query(None, description="Filter by payment method"),
    start_date: date | None = Query(None, description="Filter from this date (inclusive)"),
    end_date: date | None = Query(None, description="Filter to this date (inclusive)"),
    category_type: CategoryType | None = Query(None, description="Filter by income or expense"),
    db: Session = Depends(get_db)
):
    """
    Get all transactions with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **category_id**: Filter by category
    - **participant_id**: Filter by participant
    - **payment_method**: Filter by cash, debit, or credit
    - **start_date**: Filter transactions from this date
    - **end_date**: Filter transactions up to this date
    - **category_type**: Filter by income or expense

    Results are ordered by date (newest first).
    """
    return TransactionService.get_all(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        participant_id=participant_id,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        category_type=category_type
    )


@router.get("/month/{month}", response_model=list[TransactionResponse])
def get_transactions_by_month(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get all transactions for a specific month.

    - **month**: Month in YYYY-MM format (e.g., "2026-02")

    Returns all transactions that occurred in the specified month.
    """
    from datetime import datetime
    from calendar import monthrange

    # Parse month string to get first and last day
    year, month_num = map(int, month.split('-'))
    start_date = date(year, month_num, 1)
    last_day = monthrange(year, month_num)[1]
    end_date = date(year, month_num, last_day)

    return TransactionService.get_all(
        db,
        start_date=start_date,
        end_date=end_date,
        skip=0,
        limit=1000
    )


@router.get("/summary")
def get_transaction_summary(
    start_date: date | None = Query(None, description="Summary from this date"),
    end_date: date | None = Query(None, description="Summary to this date"),
    db: Session = Depends(get_db)
):
    """
    Get transaction summary grouped by category.

    Returns total amounts and counts per category within the date range.
    """
    return TransactionService.get_summary_by_category(db, start_date, end_date)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific transaction by ID.
    """
    return TransactionService.get_by_id(db, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing transaction.

    Can update: date, amount, category, participant, and description.
    Cannot update: payment_method, card_id, is_credit, or installments.
    """
    return TransactionService.update(db, transaction_id, transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a transaction.
    """
    TransactionService.delete(db, transaction_id)
    return None
