"""add exchange_rates table and currency to expected_purchases

Revision ID: 003_exchange_rate
Revises: 002_currency
Create Date: 2026-06-22 00:00:00.000000
"""
from alembic import op

revision = '003_exchange_rate'
down_revision = '002_currency'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL to avoid SQLAlchemy trying to CREATE the currency enum type
    # that already exists from migration 002_add_currency.

    # 1. New exchange_rates table
    op.execute("""
        CREATE TABLE exchange_rates (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            month       VARCHAR(7)  NOT NULL,
            from_currency currency  NOT NULL,
            to_currency   currency  NOT NULL,
            rate        NUMERIC(12, 6) NOT NULL,
            CONSTRAINT uq_exchange_rate_month_pair
                UNIQUE (month, from_currency, to_currency)
        )
    """)

    # 2. Add currency column to expected_purchases
    op.execute("""
        ALTER TABLE expected_purchases
        ADD COLUMN currency currency NOT NULL DEFAULT 'PEN'
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE expected_purchases DROP COLUMN currency")
    op.execute("DROP TABLE exchange_rates")
