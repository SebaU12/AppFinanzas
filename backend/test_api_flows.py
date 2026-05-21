"""
Test API workflows end-to-end
Run with: python test_api_flows.py
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from models.participant import Participant
from models.category import Category
from models.transaction import Transaction
from models.monthly_budget import MonthlyBudget
from models.reimbursement import MonthlyReimbursement, ReimbursementDetail
from services.reimbursement_service import ReimbursementService


def test_transaction_flow(db):
    """Test: Create transaction and verify it appears in queries"""
    print("\n📝 Test 1: Transaction Flow")
    print("-" * 50)

    try:
        # Get participants and categories
        lu = db.query(Participant).filter(Participant.name == "Lu").first()
        category = db.query(Category).filter(Category.name == "Alimentacion").first()

        if not lu or not category:
            print("❌ Missing test data (participants or categories)")
            return False

        # Create transaction
        transaction = Transaction(
            date=datetime.now().date(),
            description="Test Transaction - Supermercado",
            amount=Decimal("99.99"),
            category_id=category.id,
            participant_id=lu.id,
            payment_method="debit",
            subcategory="Compras Depa"
        )
        db.add(transaction)
        db.commit()

        # Verify it was created
        found = db.query(Transaction).filter(Transaction.id == transaction.id).first()
        if found:
            print(f"✅ Transaction created: #{found.id} - {found.description} - ${found.amount}")
            print(f"   Category: {found.category.name}")
            print(f"   Participant: {found.participant.name}")

            # Clean up
            db.delete(found)
            db.commit()
            return True
        else:
            print("❌ Transaction not found after creation")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False


def test_budget_comparison(db):
    """Test: Compare budget vs actual spending"""
    print("\n💰 Test 2: Budget Comparison")
    print("-" * 50)

    try:
        current_month = datetime.now().strftime("%Y-%m")

        # Get budget for a category
        budget = db.query(MonthlyBudget).filter(
            MonthlyBudget.month == current_month
        ).first()

        if not budget:
            print("❌ No budget found for current month")
            return False

        # Get actual transactions for that category
        transactions = db.query(Transaction).filter(
            Transaction.category_id == budget.category_id,
            Transaction.date >= datetime.now().replace(day=1).date()
        ).all()

        actual_amount = sum(float(t.amount) for t in transactions)
        planned_amount = float(budget.planned_amount)
        percentage = (actual_amount / planned_amount * 100) if planned_amount > 0 else 0

        print(f"✅ Budget Analysis for {budget.category.name}:")
        print(f"   Planned: ${planned_amount:.2f}")
        print(f"   Actual: ${actual_amount:.2f}")
        print(f"   Usage: {percentage:.1f}%")
        print(f"   Status: {'⚠️ Over budget' if percentage > 100 else '✓ On track'}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_reimbursement_calculation(db):
    """Test: Calculate reimbursements for current month"""
    print("\n🤝 Test 3: Reimbursement Calculation")
    print("-" * 50)

    try:
        current_month = datetime.now().strftime("%Y-%m")

        # Calculate reimbursements
        service = ReimbursementService(db)
        reimbursement = service.calculate_monthly_reimbursement(current_month)

        if reimbursement:
            print(f"✅ Reimbursement calculated for {current_month}:")
            print(f"   Total Shared Expenses: ${reimbursement.total_shared_expenses}")
            print(f"   Number of categories: {len(reimbursement.details)}")

            # Show breakdown by participant
            participant_totals = {}
            for detail in reimbursement.details:
                for split in detail.participant_splits:
                    name = split.participant.name
                    amount = float(split.amount_owed)
                    participant_totals[name] = participant_totals.get(name, 0) + amount

            for name, total in participant_totals.items():
                print(f"   {name} owes: ${total:.2f}")

            return True
        else:
            print("❌ No reimbursement calculated")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_credit_card_flow(db):
    """Test: Credit card and installments"""
    print("\n💳 Test 4: Credit Card Flow")
    print("-" * 50)

    try:
        from models.credit_card import CreditCard
        from models.card_installment import CardInstallment

        # Get a credit card
        card = db.query(CreditCard).first()
        if not card:
            print("❌ No credit cards found")
            return False

        print(f"✅ Credit Card: {card.name} (*{card.last_four_digits})")
        print(f"   Owner: {card.participant.name}")
        print(f"   Closing Day: {card.closing_day}")
        print(f"   Payment Day: {card.payment_day}")

        # Get installments for this card
        installments = db.query(CardInstallment).filter(
            CardInstallment.credit_card_id == card.id
        ).all()

        if installments:
            print(f"\n   Active Installments: {len(installments)}")
            for inst in installments[:3]:  # Show first 3
                print(f"   - {inst.transaction.description if inst.transaction else 'Unknown'}")
                print(f"     {inst.installment_number}/{inst.total_installments} - ${inst.amount}")
        else:
            print("   No active installments")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_monthly_summary(db):
    """Test: Generate monthly summary statistics"""
    print("\n📊 Test 5: Monthly Summary")
    print("-" * 50)

    try:
        current_month = datetime.now().strftime("%Y-%m")
        month_start = datetime.now().replace(day=1).date()

        # Get all transactions for current month
        transactions = db.query(Transaction).filter(
            Transaction.date >= month_start
        ).all()

        # Calculate totals
        income = sum(float(t.amount) for t in transactions if t.category.type == 'income')
        expenses = sum(float(t.amount) for t in transactions if t.category.type == 'expense')
        balance = income - expenses

        print(f"✅ Summary for {current_month}:")
        print(f"   Total Income: ${income:.2f}")
        print(f"   Total Expenses: ${expenses:.2f}")
        print(f"   Balance: ${balance:.2f}")
        print(f"   Transactions: {len(transactions)}")

        # Breakdown by category
        category_totals = {}
        for t in transactions:
            if t.category.type == 'expense':
                cat_name = t.category.name
                category_totals[cat_name] = category_totals.get(cat_name, 0) + float(t.amount)

        if category_totals:
            print(f"\n   Top Expense Categories:")
            for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   - {cat}: ${amount:.2f}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing API Flows")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Check prerequisites
        participant_count = db.query(Participant).count()
        category_count = db.query(Category).count()
        transaction_count = db.query(Transaction).count()

        print(f"\n📊 Database Status:")
        print(f"   Participants: {participant_count}")
        print(f"   Categories: {category_count}")
        print(f"   Transactions: {transaction_count}")

        if participant_count == 0 or category_count == 0:
            print("\n⚠️  Insufficient test data!")
            print("   Run: python load_seeds.py")
            print("   Then: python create_test_data.py")
            return

        # Run tests
        results = {
            "Transaction Flow": test_transaction_flow(db),
            "Budget Comparison": test_budget_comparison(db),
            "Reimbursement Calculation": test_reimbursement_calculation(db),
            "Credit Card Flow": test_credit_card_flow(db),
            "Monthly Summary": test_monthly_summary(db),
        }

        # Summary
        print("\n" + "=" * 60)
        print("📋 Test Results Summary:")
        print("-" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"   {status} - {test_name}")

        print("-" * 60)
        print(f"   Total: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Your API is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
