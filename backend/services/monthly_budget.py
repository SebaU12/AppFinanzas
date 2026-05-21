"""
CRUD service for MonthlyBudget operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from decimal import Decimal

from models.monthly_budget import MonthlyBudget
from models.category import Category
from models.transaction import Transaction
from schemas.monthly_budget import MonthlyBudgetCreate, MonthlyBudgetUpdate


class MonthlyBudgetService:
    """Service for managing MonthlyBudget operations"""

    @staticmethod
    def create(db: Session, budget_data: MonthlyBudgetCreate) -> MonthlyBudget:
        """Create a new monthly budget"""
        # Verify category exists
        category = db.query(Category).filter(Category.id == budget_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {budget_data.category_id} not found"
            )

        try:
            budget = MonthlyBudget(**budget_data.model_dump())
            db.add(budget)
            db.commit()
            db.refresh(budget)
            return budget
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Budget for month {budget_data.month} and category already exists"
            )

    @staticmethod
    def get_by_id(db: Session, budget_id: UUID) -> MonthlyBudget:
        """Get monthly budget by ID"""
        budget = db.query(MonthlyBudget).filter(MonthlyBudget.id == budget_id).first()
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MonthlyBudget with id {budget_id} not found"
            )
        return budget

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        month: str | None = None,
        category_id: UUID | None = None
    ) -> list[MonthlyBudget]:
        """Get all monthly budgets with optional filtering"""
        query = db.query(MonthlyBudget)

        if month:
            query = query.filter(MonthlyBudget.month == month)
        if category_id:
            query = query.filter(MonthlyBudget.category_id == category_id)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_by_month_and_category(
        db: Session,
        month: str,
        category_id: UUID
    ) -> MonthlyBudget | None:
        """Get budget by month and category combination"""
        return db.query(MonthlyBudget).filter(
            MonthlyBudget.month == month,
            MonthlyBudget.category_id == category_id
        ).first()

    @staticmethod
    def update(db: Session, budget_id: UUID, budget_data: MonthlyBudgetUpdate) -> MonthlyBudget:
        """Update an existing monthly budget"""
        budget = MonthlyBudgetService.get_by_id(db, budget_id)

        update_data = budget_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)

        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def delete(db: Session, budget_id: UUID) -> None:
        """Delete a monthly budget"""
        budget = MonthlyBudgetService.get_by_id(db, budget_id)
        db.delete(budget)
        db.commit()

    @staticmethod
    def copy_budgets(db: Session, from_month: str, to_month: str) -> dict:
        """
        Copy all budgets from one month to another.

        Returns summary of copied budgets and skipped (already existing) budgets.
        """
        # Fetch all budgets from source month
        source_budgets = db.query(MonthlyBudget).filter(
            MonthlyBudget.month == from_month
        ).all()

        if not source_budgets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No budgets found for month {from_month}"
            )

        # Check which budgets already exist in target month
        existing_budgets = db.query(MonthlyBudget).filter(
            MonthlyBudget.month == to_month
        ).all()
        existing_category_ids = {str(budget.category_id) for budget in existing_budgets}

        copied_count = 0
        skipped_count = 0

        for source_budget in source_budgets:
            # Skip if budget already exists for this category in target month
            if str(source_budget.category_id) in existing_category_ids:
                skipped_count += 1
                continue

            # Create new budget entry for target month
            new_budget = MonthlyBudget(
                month=to_month,
                category_id=source_budget.category_id,
                budgeted_amount=source_budget.budgeted_amount
            )
            db.add(new_budget)
            copied_count += 1

        db.commit()

        return {
            "from_month": from_month,
            "to_month": to_month,
            "copied": copied_count,
            "skipped": skipped_count,
            "total_source": len(source_budgets)
        }

    @staticmethod
    def get_monthly_summary(db: Session, month: str) -> dict:
        """Get budget summary for a specific month"""
        budgets = db.query(MonthlyBudget).filter(MonthlyBudget.month == month).all()

        total_budgeted = sum(float(budget.budgeted_amount) for budget in budgets)

        return {
            "month": month,
            "total_budgeted": total_budgeted,
            "category_count": len(budgets),
            "budgets": budgets
        }

    @staticmethod
    def get_budget_vs_actual(db: Session, month: str) -> dict:
        """
        Get budget vs actual comparison for a month with hierarchical rollup.

        Returns budget and actual amounts for all categories and subcategories,
        with subcategories rolled up into parent categories.
        """
        from datetime import datetime
        from calendar import monthrange

        # Parse month and calculate date range
        year, month_num = map(int, month.split('-'))
        start_date = datetime(year, month_num, 1).date()

        # Calculate end date (last day of month)
        last_day = monthrange(year, month_num)[1]
        end_date = datetime(year, month_num, last_day).date()

        # Fetch all budgets for the month with category details
        budgets = db.query(MonthlyBudget).filter(
            MonthlyBudget.month == month
        ).options(
            joinedload(MonthlyBudget.category)
        ).all()

        # Fetch all transactions for the month using date range
        transactions = db.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).options(
            joinedload(Transaction.category)
        ).all()

        # Calculate actual amounts per category
        actual_by_category = {}
        for transaction in transactions:
            if transaction.category_id:
                cat_id = str(transaction.category_id)
                if cat_id not in actual_by_category:
                    actual_by_category[cat_id] = Decimal('0')
                actual_by_category[cat_id] += Decimal(str(transaction.amount))

        # Fetch all categories to build hierarchy
        all_categories = db.query(Category).options(
            joinedload(Category.subcategories),
            joinedload(Category.parent)
        ).all()

        # Organize categories by parent/child
        parent_categories = [cat for cat in all_categories if cat.parent_id is None]
        category_map = {str(cat.id): cat for cat in all_categories}

        # Build budget map
        budget_by_category = {}
        for budget in budgets:
            budget_by_category[str(budget.category_id)] = Decimal(str(budget.budgeted_amount))

        # Process income and expense separately
        income_data = []
        expense_data = []

        for parent in parent_categories:
            parent_id = str(parent.id)
            parent_budget = budget_by_category.get(parent_id, Decimal('0'))
            parent_actual = actual_by_category.get(parent_id, Decimal('0'))

            # Get subcategories
            subcategories_data = []
            for subcat in parent.subcategories:
                subcat_id = str(subcat.id)
                subcat_budget = budget_by_category.get(subcat_id, Decimal('0'))
                subcat_actual = actual_by_category.get(subcat_id, Decimal('0'))

                # Add to parent totals
                parent_budget += subcat_budget
                parent_actual += subcat_actual

                if subcat_budget > 0 or subcat_actual > 0:
                    variance = subcat_budget - subcat_actual
                    percentage = float((subcat_actual / subcat_budget * 100)) if subcat_budget > 0 else 0

                    subcategories_data.append({
                        'id': subcat_id,
                        'name': subcat.name,
                        'budgeted': float(subcat_budget),
                        'actual': float(subcat_actual),
                        'variance': float(variance),
                        'percentage': round(percentage, 1),
                        'is_subcategory': True
                    })

            # Only include parent if it has budget or actual data
            if parent_budget > 0 or parent_actual > 0:
                variance = parent_budget - parent_actual
                percentage = float((parent_actual / parent_budget * 100)) if parent_budget > 0 else 0

                parent_data = {
                    'id': parent_id,
                    'name': parent.name,
                    'budgeted': float(parent_budget),
                    'actual': float(parent_actual),
                    'variance': float(variance),
                    'percentage': round(percentage, 1),
                    'is_subcategory': False,
                    'subcategories': subcategories_data
                }

                if parent.type.value == 'income':
                    income_data.append(parent_data)
                else:
                    expense_data.append(parent_data)

        # Calculate totals
        total_income_budget = sum(item['budgeted'] for item in income_data)
        total_income_actual = sum(item['actual'] for item in income_data)
        total_expense_budget = sum(item['budgeted'] for item in expense_data)
        total_expense_actual = sum(item['actual'] for item in expense_data)

        return {
            'month': month,
            'income': {
                'categories': income_data,
                'total_budgeted': total_income_budget,
                'total_actual': total_income_actual,
                'variance': total_income_budget - total_income_actual
            },
            'expenses': {
                'categories': expense_data,
                'total_budgeted': total_expense_budget,
                'total_actual': total_expense_actual,
                'variance': total_expense_budget - total_expense_actual
            },
            'net': {
                'budgeted': total_income_budget - total_expense_budget,
                'actual': total_income_actual - total_expense_actual
            }
        }
