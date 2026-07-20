"""add currency to transactions and credit_cards

Revision ID: 002_currency
Revises: 001_initial
Create Date: 2025-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_currency'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the currency enum type
    currency_enum = sa.Enum('PEN', 'USD', name='currency')
    currency_enum.create(op.get_bind(), checkfirst=True)

    # Add currency column to transactions (default PEN for existing rows)
    op.add_column(
        'transactions',
        sa.Column(
            'currency',
            sa.Enum('PEN', 'USD', name='currency'),
            nullable=False,
            server_default='PEN',
        )
    )

    # Add currency column to credit_cards (default PEN for existing rows)
    op.add_column(
        'credit_cards',
        sa.Column(
            'currency',
            sa.Enum('PEN', 'USD', name='currency'),
            nullable=False,
            server_default='PEN',
        )
    )


def downgrade() -> None:
    op.drop_column('credit_cards', 'currency')
    op.drop_column('transactions', 'currency')
    sa.Enum(name='currency').drop(op.get_bind())
