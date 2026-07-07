"""add transfers table

Revision ID: 006_add_transfers
Revises: 005_installment_payment_tracking
Create Date: 2026-07-07 00:00:00.000000
"""
from alembic import op

revision = '006_add_transfers'
down_revision = '005_installment_payment_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE transfersourcetype AS ENUM ('cash', 'debit');
    """)
    op.execute("""
        CREATE TABLE transfers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            date DATE NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            currency VARCHAR NOT NULL DEFAULT 'PEN',
            from_type transfersourcetype NOT NULL,
            from_debit_card_id UUID REFERENCES debit_cards(id) ON DELETE SET NULL,
            to_debit_card_id UUID NOT NULL REFERENCES debit_cards(id) ON DELETE RESTRICT,
            description VARCHAR
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS transfers;")
    op.execute("DROP TYPE IF EXISTS transfersourcetype;")
