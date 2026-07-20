"""add savings_cards table

Revision ID: 008_add_savings_cards
Revises: 007_reimbursement_income
Create Date: 2026-07-20 00:00:00.000000
"""
from alembic import op

revision = '008_add_savings_cards'
down_revision = '007_reimbursement_income'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE savings_cards (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE RESTRICT,
            last_four_digits VARCHAR(4),
            active BOOLEAN NOT NULL DEFAULT TRUE,
            currency VARCHAR NOT NULL DEFAULT 'PEN'
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS savings_cards;")
