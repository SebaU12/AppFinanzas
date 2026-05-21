"""
API routes for MonthlyReimbursement operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.monthly_reimbursement import (
    MonthlyReimbursementCreate,
    MonthlyReimbursementUpdate,
    MonthlyReimbursementResponse
)
from services.monthly_reimbursement import MonthlyReimbursementService

router = APIRouter(
    prefix="/reimbursements",
    tags=["reimbursements"]
)


@router.post("/calculate/{month}", response_model=MonthlyReimbursementResponse)
def calculate_reimbursement(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Calculate reimbursement for a specific month.

    Analyzes all shared (non-personal) transactions for the month,
    calculates each participant's contribution and expected share,
    and determines who owes whom.

    - **month**: Month in YYYY-MM format

    The calculation:
    1. Gets all transactions excluding personal categories
    2. Sums each participant's payments
    3. Calculates expected share based on participant percentages
    4. Computes balances (positive = owed to them, negative = they owe)
    """
    return MonthlyReimbursementService.calculate_for_month(db, month)


@router.get("/", response_model=list[MonthlyReimbursementResponse])
def get_reimbursements(
    skip: int = 0,
    limit: int = 100,
    finalized: bool | None = Query(None, description="Filter by finalized status"),
    db: Session = Depends(get_db)
):
    """
    Get all monthly reimbursements.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **finalized**: Filter by finalized status
    """
    return MonthlyReimbursementService.get_all(
        db,
        skip=skip,
        limit=limit,
        finalized=finalized
    )


@router.get("/month/{month}", response_model=MonthlyReimbursementResponse)
def get_reimbursement_by_month(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get reimbursement for a specific month.

    - **month**: Month in YYYY-MM format
    """
    return MonthlyReimbursementService.get_by_month(db, month)


@router.get("/{reimbursement_id}", response_model=MonthlyReimbursementResponse)
def get_reimbursement(
    reimbursement_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific reimbursement by ID.
    """
    return MonthlyReimbursementService.get_by_id(db, reimbursement_id)


@router.post("/finalize/{month}", response_model=MonthlyReimbursementResponse)
def finalize_reimbursement(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Finalize a reimbursement for a month.

    Once finalized, the reimbursement cannot be recalculated.
    This is typically done after all transactions for the month are entered
    and the settlement has been agreed upon.

    - **month**: Month in YYYY-MM format
    """
    return MonthlyReimbursementService.finalize(db, month)


@router.get("/balance/{month}")
def get_balance_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get a simplified balance summary for a month.

    Returns who owes whom and the optimal settlements to balance accounts.

    - **month**: Month in YYYY-MM format
    """
    return MonthlyReimbursementService.get_balance_summary(db, month)


@router.delete("/month/{month}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reimbursement(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Delete a reimbursement.

    Cannot delete finalized reimbursements.

    - **month**: Month in YYYY-MM format
    """
    MonthlyReimbursementService.delete(db, month)
    return None
