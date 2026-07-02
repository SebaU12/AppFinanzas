"""
API routes for CardInstallment operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.card_installment import CardInstallmentCreate, CardInstallmentUpdate, CardInstallmentResponse
from services.card_installment import CardInstallmentService

router = APIRouter(
    prefix="/installments",
    tags=["installments"]
)


@router.post("/", response_model=CardInstallmentResponse, status_code=status.HTTP_201_CREATED)
def create_installment(
    installment: CardInstallmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new card installment manually.

    Note: Installments are automatically generated when creating credit transactions.
    This endpoint is for manual adjustments only.

    - **transaction_id**: Transaction ID (required)
    - **month**: Month in YYYY-MM format (required)
    - **amount**: Installment amount (required, positive)
    - **paid**: Whether this installment has been paid (default: False)
    """
    return CardInstallmentService.create(db, installment)


@router.get("/", response_model=list[CardInstallmentResponse])
def get_installments(
    skip: int = 0,
    limit: int = 100,
    transaction_id: UUID | None = Query(None, description="Filter by transaction ID"),
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Filter by month (YYYY-MM)"),
    paid: bool | None = Query(None, description="Filter by paid status"),
    db: Session = Depends(get_db)
):
    """
    Get all card installments with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **transaction_id**: Filter by transaction
    - **month**: Filter by specific month
    - **paid**: Filter by paid/unpaid status
    """
    return CardInstallmentService.get_all(
        db,
        skip=skip,
        limit=limit,
        transaction_id=transaction_id,
        month=month,
        paid=paid
    )


@router.get("/month/{month}", response_model=list[CardInstallmentResponse])
def get_installments_by_month(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get all card installments for a specific month.

    - **month**: Month in YYYY-MM format (e.g., "2026-02")

    Returns all installments scheduled for the specified month.
    """
    return CardInstallmentService.get_all(db, month=month, skip=0, limit=1000)


@router.get("/summary/{month}")
def get_monthly_installment_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get installment summary for a specific month.

    Returns total amounts, counts, and paid/unpaid breakdowns for the month.
    """
    return CardInstallmentService.get_monthly_summary(db, month)


@router.get("/{installment_id}", response_model=CardInstallmentResponse)
def get_installment(
    installment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific card installment by ID.
    """
    return CardInstallmentService.get_by_id(db, installment_id)


@router.put("/{installment_id}", response_model=CardInstallmentResponse)
def update_installment(
    installment_id: UUID,
    installment: CardInstallmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing card installment.

    Typically used to mark installments as paid.
    """
    return CardInstallmentService.update(db, installment_id, installment)


@router.patch("/{installment_id}/mark-paid", response_model=CardInstallmentResponse)
def mark_installment_paid(
    installment_id: UUID,
    paid: bool = True,
    db: Session = Depends(get_db)
):
    """
    Mark an installment as paid or unpaid.

    This endpoint is used to track when actual cash leaves the account
    to pay the credit card bill (cash flow), as opposed to when the
    purchase was made (accrual accounting).

    - **installment_id**: The installment to update
    - **paid**: True to mark as paid, False to mark as unpaid (default: True)
    """
    update_data = CardInstallmentUpdate(paid=paid)
    return CardInstallmentService.update(db, installment_id, update_data)


@router.patch("/bulk-mark-paid")
def bulk_mark_installments_paid(
    installment_ids: list[UUID],
    paid: bool = True,
    db: Session = Depends(get_db)
):
    """
    Mark multiple installments as paid or unpaid in a single request.
    """
    updated = 0
    for inst_id in installment_ids:
        try:
            CardInstallmentService.update(db, inst_id, CardInstallmentUpdate(paid=paid))
            updated += 1
        except Exception:
            pass
    return {"updated": updated}


@router.delete("/{installment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment(
    installment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a card installment.
    """
    CardInstallmentService.delete(db, installment_id)
    return None
