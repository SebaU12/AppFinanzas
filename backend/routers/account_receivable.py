"""
API routes for AccountReceivable operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.account_receivable import AccountReceivableCreate, AccountReceivableUpdate, AccountReceivableResponse
from services.account_receivable import AccountReceivableService

router = APIRouter(
    prefix="/accounts-receivable",
    tags=["accounts-receivable"]
)


@router.post("/", response_model=AccountReceivableResponse, status_code=status.HTTP_201_CREATED)
def create_account_receivable(
    receivable: AccountReceivableCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new account receivable.

    - **description**: Payment description (required)
    - **amount**: Payment amount (required, positive)
    - **due_date**: Due date in YYYY-MM format (required)
    - **received**: Whether this has been received (default: False)
    - **received_date**: Date received in YYYY-MM-DD format (optional)
    - **participant_id**: Associated participant ID (optional)
    """
    return AccountReceivableService.create(db, receivable)


@router.get("/", response_model=list[AccountReceivableResponse])
def get_accounts_receivable(
    skip: int = 0,
    limit: int = 100,
    due_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Filter by due date (YYYY-MM)"),
    received: bool | None = Query(None, description="Filter by received status"),
    participant_id: UUID | None = Query(None, description="Filter by participant ID"),
    db: Session = Depends(get_db)
):
    """
    Get all accounts receivable with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **due_date**: Filter by specific month
    - **received**: Filter by received/pending status
    - **participant_id**: Filter by participant
    """
    return AccountReceivableService.get_all(
        db,
        skip=skip,
        limit=limit,
        due_date=due_date,
        received=received,
        participant_id=participant_id
    )


@router.get("/summary/{month}")
def get_monthly_accounts_receivable_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get accounts receivable summary for a specific month.

    Returns total amounts, counts, and received/pending breakdowns for the month.
    """
    return AccountReceivableService.get_monthly_summary(db, month)


@router.get("/{receivable_id}", response_model=AccountReceivableResponse)
def get_account_receivable(
    receivable_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific account receivable by ID.
    """
    return AccountReceivableService.get_by_id(db, receivable_id)


@router.put("/{receivable_id}", response_model=AccountReceivableResponse)
def update_account_receivable(
    receivable_id: UUID,
    receivable: AccountReceivableUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing account receivable.

    Typically used to mark receivables as received.
    """
    return AccountReceivableService.update(db, receivable_id, receivable)


@router.delete("/{receivable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_receivable(
    receivable_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an account receivable.
    """
    AccountReceivableService.delete(db, receivable_id)
    return None
