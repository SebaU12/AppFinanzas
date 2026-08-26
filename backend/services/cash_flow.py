"""
Cash Flow Service - Calculates real cash flow position.

This service implements hybrid cash flow and accrual accounting:
- Accrual accounting: Expenses count when consumed (used for budgets/reimbursements)
- Cash flow: Money counts when it actually moves (used for cash position tracking)

For credit card transactions:
- Accrual: The purchase date (when it was consumed)
- Cash: The installment payment date (when cash leaves the account)
"""
import calendar
from datetime import date
import calendar
from datetime import date
from decimal import Decimal
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload
from models.transaction import Transaction, PaymentMethod
from models.card_installment import CardInstallment
from models.category import Category


class CashFlowService:
    """Service for calculating real cash flow position"""

    PAYMENT_CATEGORY_NAME = "Pago Tarjeta de Credito"

    @staticmethod
    def calculate_monthly_cash_flow(db: Session, month: str) -> dict:
        """
        Calculate cash flow for a specific month.

        Cash flow includes:
        1. All cash transactions (immediate impact)
        2. All debit transactions (immediate impact)
        3. Credit card installments that are marked as paid (actual payment)

        Args:
            db: Database session
            month: Month in YYYY-MM format

        Returns:
            Dictionary with cash flow breakdown
        """
        # Get all transactions for the month
        transactions = db.query(Transaction).filter(
            Transaction.date >= f"{month}-01",
            Transaction.date < _get_next_month(month)
        ).join(Category).filter(
            Category.name != CashFlowService.PAYMENT_CATEGORY_NAME
        ).options(
            joinedload(Transaction.category),
            joinedload(Transaction.participant)
        ).all()

        # Calculate cash/debit income
        cash_income = sum(
            float(t.amount) for t in transactions
            if t.category.type == 'income' and t.payment_method in [PaymentMethod.CASH, PaymentMethod.DEBIT]
        )

        # Calculate cash/debit expenses
        cash_expenses = sum(
            float(t.amount) for t in transactions
            if t.category.type == 'expense' and t.payment_method in [PaymentMethod.CASH, PaymentMethod.DEBIT]
        )

        # Calculate total accrual income (including credit)
        total_income = sum(
            float(t.amount) for t in transactions
            if t.category.type == 'income'
        )

        # Calculate total accrual expenses (including credit)
        total_expenses = sum(
            float(t.amount) for t in transactions
            if t.category.type == 'expense'
        )

        # Get paid credit card installments for this month using actual payment date.
        # Fallback to billing month when paid_date is not recorded.
        year_num, month_num = map(int, month.split('-'))
        last_day = calendar.monthrange(year_num, month_num)[1]
        period_start = date(year_num, month_num, 1)
        period_end = date(year_num, month_num, last_day)

        paid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == True,
            or_(
                and_(CardInstallment.paid_date >= period_start, CardInstallment.paid_date <= period_end),
                and_(CardInstallment.paid_date == None, CardInstallment.month == month)
            )
        ).options(
            joinedload(CardInstallment.transaction).joinedload(Transaction.category),
            joinedload(CardInstallment.transaction).joinedload(Transaction.participant)
        ).all()

        # Calculate credit card payments (cash outflow)
        credit_card_payments = sum(float(inst.amount) for inst in paid_installments)

        # Get unpaid credit card installments for this month
        unpaid_installments_this_month = db.query(CardInstallment).filter(
            CardInstallment.month == month,
            CardInstallment.paid == False
        ).all()

        unpaid_installments_this_month_amount = sum(float(inst.amount) for inst in unpaid_installments_this_month)

        # Get ALL unpaid credit card installments (total pending debt)
        all_unpaid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == False
        ).all()

        total_unpaid_installments_amount = sum(float(inst.amount) for inst in all_unpaid_installments)

        # Calculate net cash flow
        net_cash_flow = cash_income - cash_expenses - credit_card_payments

        # Calculate accrual balance
        accrual_balance = total_income - total_expenses

        return {
            "month": month,
            "cash_flow": {
                "cash_income": cash_income,
                "cash_expenses": cash_expenses,
                "credit_card_payments": credit_card_payments,
                "net_cash_flow": net_cash_flow
            },
            "accrual": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "balance": accrual_balance
            },
            "credit_details": {
                "paid_installments_count": len(paid_installments),
                "paid_installments_amount": credit_card_payments,
                "unpaid_installments_this_month_count": len(unpaid_installments_this_month),
                "unpaid_installments_this_month_amount": unpaid_installments_this_month_amount,
                "total_unpaid_installments_count": len(all_unpaid_installments),
                "total_unpaid_installments_amount": total_unpaid_installments_amount
            },
            "summary": {
                "available_cash": net_cash_flow,
                "pending_credit_payments": total_unpaid_installments_amount,
                "pending_credit_payments_this_month": unpaid_installments_this_month_amount,
                "accrual_vs_cash_difference": accrual_balance - net_cash_flow
            }
        }

    @staticmethod
    def get_cash_position_summary(db: Session, month: str) -> dict:
        """
        Get a simplified cash position summary for dashboard display.

        Returns:
            Dictionary with key metrics for display
        """
        cash_flow_data = CashFlowService.calculate_monthly_cash_flow(db, month)

        return {
            "month": month,
            "available_cash": cash_flow_data["cash_flow"]["net_cash_flow"],
            "accrual_balance": cash_flow_data["accrual"]["balance"],
            "pending_credit_payments": cash_flow_data["summary"]["pending_credit_payments"],
            "cash_income": cash_flow_data["cash_flow"]["cash_income"],
            "cash_expenses": cash_flow_data["cash_flow"]["cash_expenses"],
            "credit_card_payments": cash_flow_data["cash_flow"]["credit_card_payments"]
        }


def _get_next_month(month: str) -> str:
    """
    Get the next month in YYYY-MM-DD format (first day of next month).

    Args:
        month: Month in YYYY-MM format

    Returns:
        First day of next month in YYYY-MM-DD format
    """
    year, month_num = map(int, month.split('-'))
    if month_num == 12:
        return f"{year + 1}-01-01"
    return f"{year}-{month_num + 1:02d}-01"
