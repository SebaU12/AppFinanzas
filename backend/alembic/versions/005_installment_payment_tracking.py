"""add payment tracking to card_installments

Revision ID: 005_installment_payment_tracking
Revises: 004_debit_card_currency
Create Date: 2026-07-03 00:00:00.000000
"""
from alembic import op

revision = '005_installment_payment_tracking'
down_revision = '004_debit_card_currency'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE card_installments
        ADD COLUMN paid_with_debit_card_id UUID REFERENCES debit_cards(id) ON DELETE SET NULL,
        ADD COLUMN paid_date DATE
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE card_installments
        DROP COLUMN paid_with_debit_card_id,
        DROP COLUMN paid_date
    """)
