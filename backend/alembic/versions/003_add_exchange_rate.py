"""add exchange_rates table and currency to expected_purchases

Revision ID: 003_exchange_rate
Revises: 002_currency
Create Date: 2026-06-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_exchange_rate'
down_revision = '002_currency'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. New exchange_rates table
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('from_currency', sa.Enum('PEN', 'USD', name='currency'), nullable=False),
        sa.Column('to_currency', sa.Enum('PEN', 'USD', name='currency'), nullable=False),
        sa.Column('rate', sa.Numeric(12, 6), nullable=False),
        sa.UniqueConstraint('month', 'from_currency', 'to_currency',
                            name='uq_exchange_rate_month_pair'),
    )

    # 2. Add currency column to expected_purchases
    op.add_column(
        'expected_purchases',
        sa.Column(
            'currency',
            sa.Enum('PEN', 'USD', name='currency'),
            nullable=False,
            server_default='PEN',
        ),
    )


def downgrade() -> None:
    op.drop_column('expected_purchases', 'currency')
    op.drop_table('exchange_rates')
