"""
Business logic for generating accounting statements.

Provides Income Statement, Cash Flow, and Balance Sheet reports.
"""
import calendar
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func, or_, and_
from sqlalchemy.orm import Session, or_, and_

from models.transaction import Transaction, PaymentMethod
from models.category import Category, CategoryType
from models.card_installment import CardInstallment
from models.account_payable import AccountPayable
from models.account_receivable import AccountReceivable
from models.participant import Participant
from services.exchange_rate import ExchangeRateService


class AccountingStatementsService:
    """Service for generating accounting statements"""

    PAYMENT_CATEGORY_NAME = "Pago Tarjeta de Credito"

    @staticmethod
    def generate_income_statement(db: Session, start_date: str, end_date: str) -> dict:
        """
        Generate Income Statement for a date range.

        Shows revenues and expenses to calculate net income.
        Uses transaction dates (when expense occurred), not payment dates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Income statement with revenues, expenses, and net income
        """
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Get all transactions in the period
        transactions = db.query(Transaction, Category).join(Category).filter(
            Transaction.date >= start,
            Transaction.date <= end,
            Category.name != AccountingStatementsService.PAYMENT_CATEGORY_NAME
        ).all()

        # Separate income and expenses by category
        income_by_category = {}
        expenses_by_category = {}

        for transaction, category in transactions:
            month = transaction.date.strftime('%Y-%m')
            amount = ExchangeRateService.convert_to_pen(
                db, Decimal(str(transaction.amount)), transaction.currency, month
            )

            if category.type == CategoryType.INCOME:
                if category.name not in income_by_category:
                    income_by_category[category.name] = Decimal('0')
                income_by_category[category.name] += amount
            else:  # EXPENSE
                if category.name not in expenses_by_category:
                    expenses_by_category[category.name] = Decimal('0')
                expenses_by_category[category.name] += amount

        # Calculate totals
        total_income = sum(income_by_category.values())
        total_expenses = sum(expenses_by_category.values())
        net_income = total_income - total_expenses

        # Format output
        income_items = [
            {"category": cat, "amount": float(amt)}
            for cat, amt in sorted(income_by_category.items())
        ]

        expense_items = [
            {"category": cat, "amount": float(amt)}
            for cat, amt in sorted(expenses_by_category.items())
        ]

        return {
            "statement_type": "Income Statement",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "revenues": {
                "items": income_items,
                "total": float(total_income)
            },
            "expenses": {
                "items": expense_items,
                "total": float(total_expenses)
            },
            "net_income": float(net_income)
        }

    @staticmethod
    def generate_cash_flow_statement(db: Session, start_date: str, end_date: str) -> dict:
        """
        Generate Cash Flow Statement for a date range.

        Shows actual cash movements:
        - Operating activities: Cash transactions (cash/debit payments)
        - Financing activities: Credit card payments (installments paid)

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Cash flow statement with operating and financing activities
        """
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Operating Activities: Cash and Debit transactions
        cash_transactions = db.query(Transaction, Category).join(Category).filter(
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.payment_method.in_([PaymentMethod.CASH, PaymentMethod.DEBIT]),
            Category.name != AccountingStatementsService.PAYMENT_CATEGORY_NAME
        ).all()

        cash_inflows = Decimal('0')
        cash_outflows = Decimal('0')

        for transaction, category in cash_transactions:
            month = transaction.date.strftime('%Y-%m')
            amount = ExchangeRateService.convert_to_pen(
                db, Decimal(str(transaction.amount)), transaction.currency, month
            )
            if category.type == CategoryType.INCOME:
                cash_inflows += amount
            else:
                cash_outflows += amount

        net_operating_cash_flow = cash_inflows - cash_outflows

        # Financing Activities: Credit card installments paid in this period.
        # Use actual paid_date; fall back to billing month when paid_date is absent.
        paid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == True,
            or_(
                and_(CardInstallment.paid_date >= start, CardInstallment.paid_date <= end),
                and_(CardInstallment.paid_date == None,
                     CardInstallment.month >= start.strftime('%Y-%m'),
                     CardInstallment.month <= end.strftime('%Y-%m'))
            )
        ).all()

        credit_payments = sum(Decimal(str(inst.amount)) for inst in paid_installments)

        # Net cash flow
        net_cash_flow = net_operating_cash_flow - credit_payments

        return {
            "statement_type": "Cash Flow Statement",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "operating_activities": {
                "cash_inflows": float(cash_inflows),
                "cash_outflows": float(cash_outflows),
                "net_operating_cash_flow": float(net_operating_cash_flow)
            },
            "financing_activities": {
                "credit_card_payments": float(credit_payments),
                "net_financing_cash_flow": float(-credit_payments)
            },
            "net_cash_flow": float(net_cash_flow)
        }

    @staticmethod
    def generate_balance_sheet(db: Session, as_of_date: str) -> dict:
        """
        Generate Balance Sheet as of a specific date.

        Shows financial position:
        - Assets: Cash (assumed), Accounts Receivable
        - Liabilities: Accounts Payable
        - Equity: Net Income (calculated from inception to date)

        Args:
            as_of_date: Date in YYYY-MM-DD format

        Returns:
            Balance sheet with assets, liabilities, and equity
        """
        as_of = datetime.strptime(as_of_date, '%Y-%m-%d').date()

        # Assets: Accounts Receivable (pending)
        accounts_receivable = db.query(AccountReceivable).filter(
            AccountReceivable.received == False
        ).all()

        total_receivables = sum(Decimal(str(ar.amount)) for ar in accounts_receivable)

        # Get all transactions up to date for cash calculation
        all_transactions = db.query(Transaction, Category).join(Category).filter(
            Transaction.date <= as_of,
            Category.name != AccountingStatementsService.PAYMENT_CATEGORY_NAME
        ).all()

        # Calculate cumulative cash (income - expenses for cash/debit), all in PEN
        cash_balance = Decimal('0')
        for transaction, category in all_transactions:
            t_month = transaction.date.strftime('%Y-%m')
            amount = ExchangeRateService.convert_to_pen(
                db, Decimal(str(transaction.amount)), transaction.currency, t_month
            )
            if transaction.payment_method in [PaymentMethod.CASH, PaymentMethod.DEBIT]:
                if category.type == CategoryType.INCOME:
                    cash_balance += amount
                else:
                    cash_balance -= amount

        # Subtract paid credit installments (use paid_date if available, else billing month)
        as_of_month = as_of.strftime('%Y-%m')
        paid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == True,
            or_(
                CardInstallment.paid_date <= as_of,
                and_(CardInstallment.paid_date == None, CardInstallment.month <= as_of_month)
            )
        ).all()

        credit_payments = sum(Decimal(str(inst.amount)) for inst in paid_installments)
        cash_balance -= credit_payments

        total_assets = cash_balance + total_receivables

        # Liabilities: Accounts Payable (unpaid)
        accounts_payable = db.query(AccountPayable).filter(
            AccountPayable.paid == False
        ).all()
        total_payables = sum(Decimal(str(ap.amount)) for ap in accounts_payable)

        # Liabilities: Unpaid credit card installments
        unpaid_installments = db.query(CardInstallment).filter(
            CardInstallment.paid == False
        ).all()
        credit_card_debt = sum(Decimal(str(inst.amount)) for inst in unpaid_installments)

        total_liabilities = total_payables + credit_card_debt

        # Equity: Retained Earnings (net income from inception)
        total_income = Decimal('0')
        total_expenses = Decimal('0')

        for transaction, category in all_transactions:
            t_month = transaction.date.strftime('%Y-%m')
            amount = ExchangeRateService.convert_to_pen(
                db, Decimal(str(transaction.amount)), transaction.currency, t_month
            )
            if category.type == CategoryType.INCOME:
                total_income += amount
            else:
                total_expenses += amount

        retained_earnings = total_income - total_expenses

        total_equity = retained_earnings

        # Balance check
        total_liabilities_and_equity = total_liabilities + total_equity

        return {
            "statement_type": "Balance Sheet",
            "as_of_date": as_of_date,
            "assets": {
                "current_assets": {
                    "cash": float(cash_balance),
                    "accounts_receivable": float(total_receivables),
                    "total_current_assets": float(total_assets)
                },
                "total_assets": float(total_assets)
            },
            "liabilities": {
                "current_liabilities": {
                    "accounts_payable": float(total_payables),
                    "credit_card_debt": float(credit_card_debt),
                    "total_current_liabilities": float(total_liabilities)
                },
                "total_liabilities": float(total_liabilities)
            },
            "equity": {
                "retained_earnings": float(retained_earnings),
                "total_equity": float(total_equity)
            },
            "total_liabilities_and_equity": float(total_liabilities_and_equity),
            "balance_check": {
                "assets": float(total_assets),
                "liabilities_and_equity": float(total_liabilities_and_equity),
                "balanced": abs(float(total_assets - total_liabilities_and_equity)) < 0.01
            }
        }

    @staticmethod
    def generate_participant_summary(db: Session, start_date: str, end_date: str) -> dict:
        """
        Generate participant-level spending summary.

        Shows each participant's spending broken down by category.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Participant spending summary
        """
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        participants = db.query(Participant).all()

        summary = []

        for participant in participants:
            # Get participant's transactions
            transactions = db.query(Transaction, Category).join(Category).filter(
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.participant_id == participant.id,
                Category.name != AccountingStatementsService.PAYMENT_CATEGORY_NAME
            ).all()

            by_category = {}
            total_income = Decimal('0')
            total_expenses = Decimal('0')

            for transaction, category in transactions:
                t_month = transaction.date.strftime('%Y-%m')
                amount = ExchangeRateService.convert_to_pen(
                    db, Decimal(str(transaction.amount)), transaction.currency, t_month
                )

                if category.name not in by_category:
                    by_category[category.name] = {
                        'type': category.type.value,
                        'amount': Decimal('0')
                    }

                by_category[category.name]['amount'] += amount

                if category.type == CategoryType.INCOME:
                    total_income += amount
                else:
                    total_expenses += amount

            category_breakdown = [
                {
                    'category': cat,
                    'type': data['type'],
                    'amount': float(data['amount'])
                }
                for cat, data in sorted(by_category.items())
            ]

            summary.append({
                'participant_id': str(participant.id),
                'participant_name': participant.name,
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net': float(total_income - total_expenses),
                'category_breakdown': category_breakdown
            })

        return {
            "report_type": "Participant Summary",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "participants": summary
        }
