"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('default_percentage', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    categorytype = sa.Enum('income', 'expense', name='categorytype')
    categorytype.create(op.get_bind())
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('income', 'expense', name='categorytype'), nullable=False),
        sa.Column('is_personal', sa.Boolean(), nullable=False),
        sa.Column('allows_credit', sa.Boolean(), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'credit_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('closing_day', sa.Integer(), nullable=False),
        sa.Column('payment_day', sa.Integer(), nullable=False),
        sa.Column('credit_limit', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'debit_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initial_balance', sa.Numeric(10, 2), nullable=False),
        sa.Column('last_four_digits', sa.String(4), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    paymentmethod = sa.Enum('cash', 'debit', 'credit', name='paymentmethod')
    paymentmethod.create(op.get_bind())
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_method', sa.Enum('cash', 'debit', 'credit', name='paymentmethod'), nullable=False),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('debit_card_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_credit', sa.Boolean(), nullable=False),
        sa.Column('installment_count', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['credit_cards.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['debit_card_id'], ['debit_cards.id'], ),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'card_installments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credit_card_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['credit_card_id'], ['credit_cards.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'monthly_budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('budgeted_amount', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('month', 'category_id', name='uq_month_category'),
    )

    op.create_table(
        'accounts_payable',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('installment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('due_date', sa.String(7), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.Column('paid_date', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['installment_id'], ['card_installments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'accounts_receivable',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('due_date', sa.String(7), nullable=False),
        sa.Column('received', sa.Boolean(), nullable=False),
        sa.Column('received_date', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'monthly_reimbursements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('total_shared_expenses', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_shared_income', sa.Numeric(10, 2), nullable=False),
        sa.Column('finalized', sa.Boolean(), nullable=False),
        sa.Column('finalized_date', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('month'),
    )

    op.create_table(
        'reimbursement_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reimbursement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('expected_share', sa.Numeric(10, 2), nullable=False),
        sa.Column('balance', sa.Numeric(10, 2), nullable=False),
        sa.Column('percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.ForeignKeyConstraint(['reimbursement_id'], ['monthly_reimbursements.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reimbursement_id', 'participant_id', name='uq_reimbursement_participant'),
    )

    op.create_table(
        'expected_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('expected_date', sa.String(10), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_method', sa.Enum('cash', 'debit', 'credit', name='paymentmethod'), nullable=False),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('installment_count', sa.Integer(), nullable=True),
        sa.Column('converted_to_transaction', sa.Boolean(), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['credit_cards.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('expected_purchases')
    op.drop_table('reimbursement_details')
    op.drop_table('monthly_reimbursements')
    op.drop_table('accounts_receivable')
    op.drop_table('accounts_payable')
    op.drop_table('monthly_budgets')
    op.drop_table('card_installments')
    op.drop_table('transactions')
    op.drop_table('debit_cards')
    op.drop_table('credit_cards')
    op.drop_table('categories')
    op.drop_table('participants')
    sa.Enum(name='paymentmethod').drop(op.get_bind())
    sa.Enum(name='categorytype').drop(op.get_bind())
