"""
Business logic for ExpectedPurchase operations and simulation.
"""
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.expected_purchase import ExpectedPurchase
from models.transaction import Transaction, PaymentMethod
from models.category import Category
from models.participant import Participant
from models.credit_card import CreditCard
from models.monthly_budget import MonthlyBudget
from schemas.expected_purchase import ExpectedPurchaseCreate, ExpectedPurchaseUpdate


class ExpectedPurchaseService:
    """Service for managing expected purchases and simulations"""

    @staticmethod
    def create(db: Session, purchase: ExpectedPurchaseCreate) -> ExpectedPurchase:
        """Create a new expected purchase"""
        # Validate category exists
        category = db.query(Category).filter(Category.id == purchase.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {purchase.category_id} not found"
            )

        # Validate participant exists
        participant = db.query(Participant).filter(Participant.id == purchase.participant_id).first()
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participant with id {purchase.participant_id} not found"
            )

        # Validate credit card if needed
        if purchase.payment_method == PaymentMethod.CREDIT:
            if not purchase.card_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="card_id is required for credit purchases"
                )

            card = db.query(CreditCard).filter(CreditCard.id == purchase.card_id).first()
            if not card:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Credit card with id {purchase.card_id} not found"
                )

            if not category.allows_credit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{category.name}' does not allow credit card payments"
                )

        db_purchase = ExpectedPurchase(**purchase.model_dump())
        db.add(db_purchase)
        db.commit()
        db.refresh(db_purchase)
        return db_purchase

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        converted: bool | None = None
    ) -> list[ExpectedPurchase]:
        """Get all expected purchases with optional filtering"""
        query = db.query(ExpectedPurchase)

        if converted is not None:
            query = query.filter(ExpectedPurchase.converted_to_transaction == converted)

        return query.order_by(ExpectedPurchase.expected_date).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, purchase_id: UUID) -> ExpectedPurchase:
        """Get a specific expected purchase by ID"""
        purchase = db.query(ExpectedPurchase).filter(ExpectedPurchase.id == purchase_id).first()
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ExpectedPurchase with id {purchase_id} not found"
            )
        return purchase

    @staticmethod
    def update(db: Session, purchase_id: UUID, purchase_update: ExpectedPurchaseUpdate) -> ExpectedPurchase:
        """Update an existing expected purchase"""
        db_purchase = ExpectedPurchaseService.get_by_id(db, purchase_id)

        if db_purchase.converted_to_transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a purchase that has been converted to a transaction"
            )

        update_data = purchase_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_purchase, field, value)

        db.commit()
        db.refresh(db_purchase)
        return db_purchase

    @staticmethod
    def delete(db: Session, purchase_id: UUID) -> None:
        """Delete an expected purchase"""
        db_purchase = ExpectedPurchaseService.get_by_id(db, purchase_id)

        if db_purchase.converted_to_transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a purchase that has been converted to a transaction"
            )

        db.delete(db_purchase)
        db.commit()

    @staticmethod
    def simulate(db: Session, purchase_id: UUID) -> dict:
        """
        Simulate the financial impact of an expected purchase.

        Returns detailed analysis of:
        - Monthly cash flow impact (for installment purchases)
        - Budget impact per category
        - Total cost breakdown
        """
        purchase = ExpectedPurchaseService.get_by_id(db, purchase_id)

        # Get related entities
        category = db.query(Category).filter(Category.id == purchase.category_id).first()
        participant = db.query(Participant).filter(Participant.id == purchase.participant_id).first()

        # Parse expected date
        expected_date = datetime.strptime(purchase.expected_date, '%Y-%m-%d')

        # Calculate installment breakdown if credit
        monthly_impact = []
        if purchase.payment_method == PaymentMethod.CREDIT and purchase.installment_count:
            installment_amount = Decimal(str(purchase.amount)) / purchase.installment_count
            installment_amount = installment_amount.quantize(Decimal('0.01'))

            # Calculate adjustment for last installment
            total_rounded = installment_amount * purchase.installment_count
            adjustment = Decimal(str(purchase.amount)) - total_rounded

            # Generate monthly impact
            current_month = expected_date + relativedelta(months=1)
            for i in range(purchase.installment_count):
                amount = installment_amount
                if i == purchase.installment_count - 1:
                    amount += adjustment

                month_str = current_month.strftime('%Y-%m')

                # Check if budget exists for this month/category
                budget = db.query(MonthlyBudget).filter(
                    MonthlyBudget.month == month_str,
                    MonthlyBudget.category_id == purchase.category_id
                ).first()

                # Get existing transactions for this month/category
                existing_transactions = db.query(Transaction).filter(
                    Transaction.category_id == purchase.category_id
                ).all()

                existing_amount = sum(
                    Decimal(str(t.amount)) for t in existing_transactions
                    if t.date.strftime('%Y-%m') == month_str
                )

                monthly_impact.append({
                    'month': month_str,
                    'installment_number': i + 1,
                    'amount': float(amount),
                    'budget_limit': float(budget.limit) if budget else None,
                    'current_spending': float(existing_amount),
                    'projected_spending': float(existing_amount + amount),
                    'remaining_budget': float(budget.limit - existing_amount - amount) if budget else None,
                    'over_budget': float(existing_amount + amount) > float(budget.limit) if budget else False
                })

                current_month += relativedelta(months=1)
        else:
            # Single payment
            month_str = expected_date.strftime('%Y-%m')

            budget = db.query(MonthlyBudget).filter(
                MonthlyBudget.month == month_str,
                MonthlyBudget.category_id == purchase.category_id
            ).first()

            existing_transactions = db.query(Transaction).filter(
                Transaction.category_id == purchase.category_id
            ).all()

            existing_amount = sum(
                Decimal(str(t.amount)) for t in existing_transactions
                if t.date.strftime('%Y-%m') == month_str
            )

            monthly_impact.append({
                'month': month_str,
                'installment_number': 1,
                'amount': float(purchase.amount),
                'budget_limit': float(budget.limit) if budget else None,
                'current_spending': float(existing_amount),
                'projected_spending': float(existing_amount + Decimal(str(purchase.amount))),
                'remaining_budget': float(budget.limit - existing_amount - Decimal(str(purchase.amount))) if budget else None,
                'over_budget': float(existing_amount + Decimal(str(purchase.amount))) > float(budget.limit) if budget else False
            })

        # Impact summary
        impact_summary = {
            'total_amount': float(purchase.amount),
            'payment_method': purchase.payment_method.value,
            'number_of_installments': purchase.installment_count if purchase.payment_method == PaymentMethod.CREDIT else 1,
            'monthly_payment': float(monthly_impact[0]['amount']) if monthly_impact else 0,
            'category_name': category.name if category else 'Unknown',
            'participant_name': participant.name if participant else 'Unknown',
            'expected_date': purchase.expected_date,
            'affects_months': len(monthly_impact),
            'total_months_over_budget': sum(1 for m in monthly_impact if m['over_budget'])
        }

        return {
            'expected_purchase_id': str(purchase.id),
            'description': purchase.description,
            'impact_summary': impact_summary,
            'monthly_impact': monthly_impact
        }

    @staticmethod
    def convert_to_transaction(db: Session, purchase_id: UUID) -> Transaction:
        """
        Convert an expected purchase into an actual transaction.

        This creates a real transaction and marks the expected purchase as converted.
        """
        purchase = ExpectedPurchaseService.get_by_id(db, purchase_id)

        if purchase.converted_to_transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This purchase has already been converted to a transaction"
            )

        # Create the transaction
        transaction = Transaction(
            description=purchase.description,
            amount=purchase.amount,
            date=datetime.strptime(purchase.expected_date, '%Y-%m-%d').date(),
            category_id=purchase.category_id,
            participant_id=purchase.participant_id,
            payment_method=purchase.payment_method,
            card_id=purchase.card_id,
            is_credit=(purchase.payment_method == PaymentMethod.CREDIT),
            installments=purchase.installment_count
        )

        db.add(transaction)
        db.flush()

        # Mark purchase as converted
        purchase.converted_to_transaction = True
        purchase.transaction_id = transaction.id

        db.commit()
        db.refresh(transaction)
        return transaction
