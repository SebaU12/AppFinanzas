"""expand transfers for savings accounts

Revision ID: 009_expand_transfers_for_savings
Revises: 008_add_savings_cards
Create Date: 2026-07-20 00:00:00.000000
"""
from alembic import op


revision = '009_expand_transfers_for_savings'
down_revision = '008_add_savings_cards'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transfersourcetype ADD VALUE IF NOT EXISTS 'savings';")
    op.execute("CREATE TYPE transferdestinationtype AS ENUM ('debit', 'savings');")
    op.execute("ALTER TABLE transfers ADD COLUMN to_type transferdestinationtype;")
    op.execute("ALTER TABLE transfers ADD COLUMN from_savings_card_id UUID REFERENCES savings_cards(id) ON DELETE SET NULL;")
    op.execute("ALTER TABLE transfers ADD COLUMN to_savings_card_id UUID REFERENCES savings_cards(id) ON DELETE RESTRICT;")
    op.execute("UPDATE transfers SET to_type = 'debit';")
    op.execute("ALTER TABLE transfers ALTER COLUMN to_debit_card_id DROP NOT NULL;")
    op.execute("ALTER TABLE transfers ALTER COLUMN to_type SET NOT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE transfers DROP COLUMN IF EXISTS to_savings_card_id;")
    op.execute("ALTER TABLE transfers DROP COLUMN IF EXISTS from_savings_card_id;")
    op.execute("ALTER TABLE transfers DROP COLUMN IF EXISTS to_type;")
    op.execute("DROP TYPE IF EXISTS transferdestinationtype;")
