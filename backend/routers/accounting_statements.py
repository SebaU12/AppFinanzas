"""
API routes for Accounting Statements.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from services.accounting_statements import AccountingStatementsService

router = APIRouter(
    prefix="/statements",
    tags=["statements"]
)


@router.get("/income-statement")
def get_income_statement(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate Income Statement for a date range.

    The Income Statement shows:
    - **Revenues**: All income by category
    - **Expenses**: All expenses by category
    - **Net Income**: Profit or loss for the period

    Uses transaction dates (when the expense occurred), not payment dates.
    This follows accrual accounting principles.

    **Example**: If you bought something on credit in January, it appears
    in January's income statement, not when you pay the installments.

    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    """
    return AccountingStatementsService.generate_income_statement(db, start_date, end_date)


@router.get("/cash-flow")
def get_cash_flow_statement(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate Cash Flow Statement for a date range.

    The Cash Flow Statement shows actual cash movements:

    **Operating Activities**:
    - Cash inflows from income
    - Cash outflows from expenses
    - Only includes cash/debit transactions (actual cash movements)

    **Financing Activities**:
    - Credit card installment payments made in the period

    **Net Cash Flow**: Total change in cash position

    This helps answer: "How much actual cash came in and went out?"

    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    """
    return AccountingStatementsService.generate_cash_flow_statement(db, start_date, end_date)


@router.get("/balance-sheet")
def get_balance_sheet(
    as_of_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="As of date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate Balance Sheet as of a specific date.

    The Balance Sheet shows your financial position at a point in time:

    **Assets** (what you have):
    - Cash: Calculated from all cash/debit transactions minus credit payments
    - Accounts Receivable: Money owed to you (pending reimbursements)

    **Liabilities** (what you owe):
    - Accounts Payable: Unpaid credit card installments and other obligations

    **Equity** (net worth):
    - Retained Earnings: Cumulative profit/loss from inception

    **Accounting Equation**: Assets = Liabilities + Equity

    The balance_check section verifies this equation holds.

    - **as_of_date**: Date in YYYY-MM-DD format
    """
    return AccountingStatementsService.generate_balance_sheet(db, as_of_date)


@router.get("/participant-summary")
def get_participant_summary(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate participant-level spending summary.

    Shows each participant's activity broken down by category:
    - Total income
    - Total expenses
    - Net (income - expenses)
    - Category-by-category breakdown

    Useful for understanding who spent what and where.

    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    """
    return AccountingStatementsService.generate_participant_summary(db, start_date, end_date)
