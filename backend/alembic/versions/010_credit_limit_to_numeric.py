"""credit_limit column type Integer to Numeric

Revision ID: 010_credit_limit_to_numeric
Revises: 009_expand_transfers_for_savings
Create Date: 2026-08-26 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = '010_credit_limit_to_numeric'
down_revision = '009_expand_transfers_for_savings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'credit_cards',
        'credit_limit',
        existing_type=sa.Integer(),
        type_=sa.Numeric(12, 2),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'credit_cards',
        'credit_limit',
        existing_type=sa.Numeric(12, 2),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='credit_limit::integer',
    )
