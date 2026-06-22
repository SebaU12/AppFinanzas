"""add currency column to debit_cards

Revision ID: 004_debit_card_currency
Revises: 003_exchange_rate
Create Date: 2026-06-22 00:00:00.000000
"""
from alembic import op

revision = '004_debit_card_currency'
down_revision = '003_exchange_rate'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE debit_cards
        ADD COLUMN currency currency NOT NULL DEFAULT 'PEN'
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE debit_cards DROP COLUMN currency")
