"""add amount_received to reimbursement_details

Revision ID: 007_reimbursement_income
Revises: 006_add_transfers
Create Date: 2026-07-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '007_reimbursement_income'
down_revision = '006_add_transfers'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE reimbursement_details
        ADD COLUMN IF NOT EXISTS amount_received NUMERIC(10, 2) NOT NULL DEFAULT 0
    """)


def downgrade():
    op.execute("""
        ALTER TABLE reimbursement_details
        DROP COLUMN IF EXISTS amount_received
    """)
