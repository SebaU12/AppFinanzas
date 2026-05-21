"""
API routes for MonthlyBudget operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.monthly_budget import MonthlyBudgetCreate, MonthlyBudgetUpdate, MonthlyBudgetResponse
from services.monthly_budget import MonthlyBudgetService

router = APIRouter(
    prefix="/budget",
    tags=["budget"]
)


@router.post("/", response_model=MonthlyBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_monthly_budget(
    budget: MonthlyBudgetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new monthly budget.

    - **month**: Month in YYYY-MM format (required)
    - **category_id**: Category ID (required)
    - **budgeted_amount**: Budget amount (required, non-negative)

    Note: The combination of month and category must be unique.
    """
    return MonthlyBudgetService.create(db, budget)


@router.get("/", response_model=list[MonthlyBudgetResponse])
def get_monthly_budgets(
    skip: int = 0,
    limit: int = 100,
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Filter by month (YYYY-MM)"),
    category_id: UUID | None = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db)
):
    """
    Get all monthly budgets with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **month**: Filter by specific month (YYYY-MM format)
    - **category_id**: Filter by category
    """
    return MonthlyBudgetService.get_all(
        db,
        skip=skip,
        limit=limit,
        month=month,
        category_id=category_id
    )


@router.get("/month/{month}", response_model=list[MonthlyBudgetResponse])
def get_budgets_by_month(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get all budgets for a specific month.

    - **month**: Month in YYYY-MM format (e.g., "2026-02")

    Returns all budget entries for the specified month.
    """
    return MonthlyBudgetService.get_all(db, month=month, skip=0, limit=1000)


@router.get("/summary/{month}")
def get_monthly_summary(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get budget summary for a specific month.

    Returns total budgeted amount and list of all budgets for the month.
    """
    return MonthlyBudgetService.get_monthly_summary(db, month)


@router.get("/vs-actual/{month}")
def get_budget_vs_actual(
    month: str,
    db: Session = Depends(get_db)
):
    """
    Get budget vs actual comparison for a specific month.

    Returns hierarchical budget vs actual data with:
    - Income categories and subcategories
    - Expense categories and subcategories
    - Budgeted amounts, actual amounts, variance, and percentage used
    - Subcategories rolled up into parent totals
    """
    return MonthlyBudgetService.get_budget_vs_actual(db, month)


@router.get("/{budget_id}", response_model=MonthlyBudgetResponse)
def get_monthly_budget(
    budget_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific monthly budget by ID.
    """
    return MonthlyBudgetService.get_by_id(db, budget_id)


@router.put("/{budget_id}", response_model=MonthlyBudgetResponse)
def update_monthly_budget(
    budget_id: UUID,
    budget: MonthlyBudgetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing monthly budget.

    Currently only supports updating the budgeted amount.
    """
    return MonthlyBudgetService.update(db, budget_id, budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monthly_budget(
    budget_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a monthly budget.
    """
    MonthlyBudgetService.delete(db, budget_id)
    return None


@router.post("/copy/{from_month}/{to_month}")
def copy_budgets(
    from_month: str,
    to_month: str,
    db: Session = Depends(get_db)
):
    """
    Copy all budgets from one month to another.

    - **from_month**: Source month in YYYY-MM format (e.g., "2026-01")
    - **to_month**: Target month in YYYY-MM format (e.g., "2026-02")

    Creates new budget entries in the target month with the same amounts
    as the source month. Skips categories that already have budgets in
    the target month.

    Returns summary with number of copied and skipped budgets.
    """
    return MonthlyBudgetService.copy_budgets(db, from_month, to_month)
