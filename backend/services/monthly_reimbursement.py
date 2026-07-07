"""
Business logic for MonthlyReimbursement operations.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from fastapi import HTTPException, status
from datetime import datetime

from models.monthly_reimbursement import MonthlyReimbursement
from models.reimbursement_detail import ReimbursementDetail
from models.transaction import Transaction, Currency
from models.category import Category, CategoryType
from models.participant import Participant
from schemas.monthly_reimbursement import MonthlyReimbursementCreate, MonthlyReimbursementUpdate
from services.exchange_rate import ExchangeRateService


class MonthlyReimbursementService:
    """Service for managing monthly reimbursements"""

    @staticmethod
    def calculate_for_month(db: Session, month: str) -> MonthlyReimbursement:
        """
        Calculate reimbursement for a specific month.

        This is the core logic that:
        1. Gets all non-personal transactions for the month
        2. Calculates each participant's contribution
        3. Determines expected shares based on percentages
        4. Computes balances (positive = owed to them, negative = they owe)
        """
        # Parse month
        year, month_num = map(int, month.split('-'))

        # Check if reimbursement already exists
        existing = db.query(MonthlyReimbursement).filter(
            MonthlyReimbursement.month == month
        ).first()

        # Allow recalculation even if finalized (unfinalize automatically)
        if existing and existing.finalized:
            existing.finalized = False
            existing.finalized_date = None

        # Get all active participants
        participants = db.query(Participant).filter(Participant.active == True).all()

        if not participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active participants found"
            )

        # Validate percentages sum to 100
        total_percentage = sum(p.default_percentage for p in participants)
        if abs(total_percentage - 100.0) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Participant percentages must sum to 100, currently: {total_percentage}"
            )

        # Get all expense transactions for the month, excluding personal categories
        expense_transactions = db.query(Transaction).join(Category).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month_num,
            Category.is_personal == False,
            Category.type == CategoryType.EXPENSE
        ).all()

        # Get all income transactions for the month, excluding personal categories
        income_transactions = db.query(Transaction).join(Category).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month_num,
            Category.is_personal == False,
            Category.type == CategoryType.INCOME
        ).all()

        # Calculate each participant's gross expenses (all amounts converted to PEN)
        participant_payments = {p.id: Decimal('0') for p in participants}
        for transaction in expense_transactions:
            amount_pen = ExchangeRateService.convert_to_pen(
                db,
                Decimal(str(transaction.amount)),
                transaction.currency,
                month,
            )
            participant_payments[transaction.participant_id] += amount_pen

        # Calculate each participant's shared income (all amounts converted to PEN)
        participant_income = {p.id: Decimal('0') for p in participants}
        for transaction in income_transactions:
            amount_pen = ExchangeRateService.convert_to_pen(
                db,
                Decimal(str(transaction.amount)),
                transaction.currency,
                month,
            )
            participant_income[transaction.participant_id] += amount_pen

        # Calculate totals
        total_shared_expenses = sum(participant_payments.values())
        total_shared_income = sum(participant_income.values())
        total_shared_net = total_shared_expenses - total_shared_income

        # Calculate expected shares and balances using net amounts
        details_data = []
        for participant in participants:
            amount_paid = participant_payments[participant.id]
            amount_received = participant_income[participant.id]
            net_paid = amount_paid - amount_received
            expected_share = (total_shared_net * Decimal(str(participant.default_percentage))) / Decimal('100')
            balance = net_paid - expected_share

            details_data.append({
                'participant_id': participant.id,
                'amount_paid': amount_paid,
                'amount_received': amount_received,
                'expected_share': expected_share,
                'balance': balance,
                'percentage': Decimal(str(participant.default_percentage))
            })

        # Create or update reimbursement
        if existing:
            reimbursement = existing
            reimbursement.total_shared_expenses = total_shared_expenses
            reimbursement.total_shared_income = total_shared_income
            # Delete old details
            db.query(ReimbursementDetail).filter(
                ReimbursementDetail.reimbursement_id == reimbursement.id
            ).delete()
        else:
            reimbursement = MonthlyReimbursement(
                month=month,
                total_shared_expenses=total_shared_expenses,
                total_shared_income=total_shared_income,
                finalized=False
            )
            db.add(reimbursement)
            db.flush()  # Get the ID

        # Create new details
        for detail_data in details_data:
            detail = ReimbursementDetail(
                reimbursement_id=reimbursement.id,
                **detail_data
            )
            db.add(detail)

        db.commit()
        db.refresh(reimbursement)
        return reimbursement

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        finalized: bool | None = None
    ) -> list[MonthlyReimbursement]:
        """Get all monthly reimbursements with optional filtering"""
        query = db.query(MonthlyReimbursement).options(
            joinedload(MonthlyReimbursement.details).joinedload(ReimbursementDetail.participant)
        )

        if finalized is not None:
            query = query.filter(MonthlyReimbursement.finalized == finalized)

        return query.order_by(MonthlyReimbursement.month.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_month(db: Session, month: str) -> MonthlyReimbursement:
        """Get reimbursement for a specific month"""
        reimbursement = db.query(MonthlyReimbursement).options(
            joinedload(MonthlyReimbursement.details).joinedload(ReimbursementDetail.participant)
        ).filter(
            MonthlyReimbursement.month == month
        ).first()

        if not reimbursement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reimbursement for month {month} not found"
            )

        return reimbursement

    @staticmethod
    def get_by_id(db: Session, reimbursement_id: UUID) -> MonthlyReimbursement:
        """Get a specific reimbursement by ID"""
        reimbursement = db.query(MonthlyReimbursement).options(
            joinedload(MonthlyReimbursement.details).joinedload(ReimbursementDetail.participant)
        ).filter(
            MonthlyReimbursement.id == reimbursement_id
        ).first()

        if not reimbursement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reimbursement with id {reimbursement_id} not found"
            )

        return reimbursement

    @staticmethod
    def finalize(db: Session, month: str) -> MonthlyReimbursement:
        """
        Finalize a reimbursement for a month.

        Once finalized, the reimbursement cannot be recalculated.
        """
        reimbursement = MonthlyReimbursementService.get_by_month(db, month)

        if reimbursement.finalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reimbursement for {month} is already finalized"
            )

        reimbursement.finalized = True
        reimbursement.finalized_date = datetime.now().strftime('%Y-%m-%d')

        db.commit()
        db.refresh(reimbursement)
        return reimbursement

    @staticmethod
    def delete(db: Session, month: str) -> None:
        """Delete a reimbursement"""
        reimbursement = MonthlyReimbursementService.get_by_month(db, month)

        if reimbursement.finalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete finalized reimbursement for {month}"
            )

        db.delete(reimbursement)
        db.commit()

    @staticmethod
    def get_balance_summary(db: Session, month: str) -> dict:
        """
        Get a simplified balance summary showing who owes whom.

        Returns settlements needed to balance accounts.
        """
        reimbursement = MonthlyReimbursementService.get_by_month(db, month)

        # Get participants with balances
        creditors = []  # People who are owed money (positive balance)
        debtors = []    # People who owe money (negative balance)

        for detail in reimbursement.details:
            participant = db.query(Participant).filter(
                Participant.id == detail.participant_id
            ).first()

            balance_info = {
                'participant_id': str(detail.participant_id),
                'participant_name': participant.name if participant else 'Unknown',
                'balance': float(detail.balance)
            }

            if detail.balance > 0:
                creditors.append(balance_info)
            elif detail.balance < 0:
                debtors.append(balance_info)

        # Calculate settlements
        settlements = []
        creditors.sort(key=lambda x: x['balance'], reverse=True)
        debtors.sort(key=lambda x: x['balance'])

        i, j = 0, 0
        while i < len(creditors) and j < len(debtors):
            creditor = creditors[i]
            debtor = debtors[j]

            amount = min(creditor['balance'], abs(debtor['balance']))

            settlements.append({
                'from': debtor['participant_name'],
                'to': creditor['participant_name'],
                'amount': round(amount, 2)
            })

            creditor['balance'] -= amount
            debtor['balance'] += amount

            if creditor['balance'] < 0.01:
                i += 1
            if abs(debtor['balance']) < 0.01:
                j += 1

        return {
            'month': month,
            'total_shared_expenses': float(reimbursement.total_shared_expenses),
            'settlements': settlements,
            'finalized': reimbursement.finalized
        }
