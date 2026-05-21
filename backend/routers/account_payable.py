"""
API routes for AccountPayable operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.account_payable import AccountPayableCreate, AccountPayableUpdate, AccountPayableResponse
from services.account_payable import AccountPayableService

router = APIRouter(
    prefix="/accounts-payable",
    tags=["accounts-payable"]
)


@router.post("/", response_model=AccountPayableResponse, status_code=status.HTTP_201_CREATED)
def create_account_payable(
    payable: AccountPayableCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new account payable.

    - **description**: Payment description (required)
    - **amount**: Payment amount (required, positive)
    - **due_date**: Due date in YYYY-MM format (required)
    - **paid**: Whether this has been paid (default: False)
    - **paid_date**: Date paid in YYYY-MM-DD format (optional)
    - **installment_id**: Associated installment ID (optional)
    """
    return AccountPayableService.create(db, payable)


@router.get("/", response_model=list[AccountPayableResponse])
def get_accounts_payable(
    skip: int = 0,
    limit: int = 100,
    due_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Filter by due date (YYYY-MM)"),
    paid: bool | None = Query(None, description="Filter by paid status"),
    db: Session = Depends(get_db)
):
    """
    Get all accounts payable with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **due_date**: Filter by specific month
    - **paid**: Filter by paid/unpaid status
    """
    return AccountPayableService.get_all(
        db,
        skip=skip,
        limit=limit,
        due_date=due_date,
        paid=paid
    )


@router.post("/generate", response_model=list[AccountPayableResponse])
def generate_accounts_payable_from_installments(
    db: Session = Depends(get_db)
):
    """
    Generate accounts payable from unpaid installments.

    Creates payable records for all unpaid credit card installments.
    """
    return AccountPayableService.generate_from_installments(db)


@router.get("/summary/{month}")
def get_monthly_accounts_payable_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get accounts payable summary for a specific month.

    Returns total amounts, counts, and paid/unpaid breakdowns for the month.
    """
    return AccountPayableService.get_monthly_summary(db, month)


@router.get("/{payable_id}", response_model=AccountPayableResponse)
def get_account_payable(
    payable_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific account payable by ID.
    """
    return AccountPayableService.get_by_id(db, payable_id)


@router.put("/{payable_id}", response_model=AccountPayableResponse)
def update_account_payable(
    payable_id: UUID,
    payable: AccountPayableUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing account payable.

    Typically used to mark payables as paid.
    """
    return AccountPayableService.update(db, payable_id, payable)


@router.delete("/{payable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_payable(
    payable_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an account payable.
    """
    AccountPayableService.delete(db, payable_id)
    return None
