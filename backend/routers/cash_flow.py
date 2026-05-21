"""
API routes for Cash Flow operations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from services.cash_flow import CashFlowService

router = APIRouter(
    prefix="/cash-flow",
    tags=["cash-flow"]
)


@router.get("/month/{month}")
def get_monthly_cash_flow(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed cash flow analysis for a specific month.

    This endpoint provides a hybrid view of finances:
    - **Cash Flow**: Actual money movement (cash/debit + paid credit installments)
    - **Accrual**: What was consumed/earned (all transactions including credit)

    The difference helps understand:
    - How much real cash you have available
    - How much you've committed to pay later (unpaid credit installments)

    Args:
        month: Month in YYYY-MM format (e.g., "2026-02")

    Returns:
        Detailed cash flow breakdown with both cash and accrual perspectives
    """
    return CashFlowService.calculate_monthly_cash_flow(db, month)


@router.get("/summary/{month}")
def get_cash_position_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get simplified cash position summary for dashboard display.

    Returns key metrics:
    - Available cash (real money position)
    - Accrual balance (budget perspective)
    - Pending credit payments

    Args:
        month: Month in YYYY-MM format (e.g., "2026-02")

    Returns:
        Simplified cash position metrics
    """
    return CashFlowService.get_cash_position_summary(db, month)
