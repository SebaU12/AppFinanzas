"""
API route handlers for the Finanzas application.
"""
from .participant import router as participant_router
from .category import router as category_router
from .monthly_budget import router as budget_router
from .transaction import router as transaction_router
from .credit_card import router as credit_card_router
from .debit_card import router as debit_card_router
from .card_installment import router as installment_router
from .account_payable import router as account_payable_router
from .account_receivable import router as account_receivable_router
from .monthly_reimbursement import router as reimbursement_router
from .expected_purchase import router as expected_purchase_router
from .accounting_statements import router as statements_router
from .csv_ingestion import router as csv_ingestion_router
from .cash_flow import router as cash_flow_router
from .exchange_rate import router as exchange_rate_router
from .transfer import router as transfer_router
from .savings_card import router as savings_card_router

__all__ = [
    "participant_router", "category_router", "budget_router",
    "transaction_router", "credit_card_router", "debit_card_router", "installment_router",
    "account_payable_router", "account_receivable_router", "reimbursement_router",
    "expected_purchase_router", "statements_router", "csv_ingestion_router",
    "cash_flow_router", "exchange_rate_router", "transfer_router", "savings_card_router"
]
