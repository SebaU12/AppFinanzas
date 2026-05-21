"""
Create test data for the finanzas application
Run with: python create_test_data.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from models.participant import Participant
from models.category import Category
from models.transaction import Transaction
from models.monthly_budget import MonthlyBudget
from models.credit_card import CreditCard


def create_participants(db):
    """Create test participants"""
    print("\n👥 Creating participants...")

    participants_data = [
        {"name": "Lu", "default_percentage": 25.0},
        {"name": "Chebos", "default_percentage": 75.0},
    ]

    participants = []
    for p_data in participants_data:
        # Check if exists
        existing = db.query(Participant).filter(Participant.name == p_data["name"]).first()
        if existing:
            print(f"   ✓ Participant '{p_data['name']}' already exists")
            participants.append(existing)
        else:
            participant = Participant(**p_data)
            db.add(participant)
            participants.append(participant)
            print(f"   ✓ Created participant '{p_data['name']}'")

    db.commit()
    return participants


def create_budget(db, categories):
    """Create sample budget for current month"""
    print("\n💰 Creating monthly budget...")

    current_month = datetime.now().strftime("%Y-%m")

    # Budget allocations
    budget_data = [
        ("Alimentacion", 800),
        ("Transporte", 400),
        ("Vivienda", 1200),
        ("Entretenimiento", 300),
        ("Salud", 200),
        ("Servicios", 500),
    ]

    budgets_created = 0
    for cat_name, amount in budget_data:
        category = next((c for c in categories if c.name == cat_name), None)
        if category:
            # Check if budget exists
            existing = db.query(MonthlyBudget).filter(
                MonthlyBudget.month == current_month,
                MonthlyBudget.category_id == category.id
            ).first()

            if not existing:
                budget = MonthlyBudget(
                    month=current_month,
                    category_id=category.id,
                    planned_amount=Decimal(str(amount))
                )
                db.add(budget)
                budgets_created += 1

    db.commit()
    print(f"   ✓ Created {budgets_created} budget entries for {current_month}")


def create_transactions(db, participants, categories):
    """Create sample transactions"""
    print("\n💳 Creating transactions...")

    lu = next(p for p in participants if p.name == "Lu")
    chebos = next(p for p in participants if p.name == "Chebos")

    # Helper to find category by name
    def get_category(name):
        return next((c for c in categories if c.name == name), None)

    # Sample transactions for current month
    today = datetime.now()
    transactions_data = [
        # Income
        {
            "date": today.replace(day=1),
            "description": "Salario Lu",
            "amount": Decimal("2500"),
            "category": "Salario",
            "participant": lu,
            "payment_method": "transfer"
        },
        {
            "date": today.replace(day=1),
            "description": "Salario Chebos",
            "amount": Decimal("3500"),
            "category": "Salario",
            "participant": chebos,
            "payment_method": "transfer"
        },
        # Expenses
        {
            "date": today - timedelta(days=2),
            "description": "Supermercado Wong",
            "amount": Decimal("150.50"),
            "category": "Alimentacion",
            "participant": lu,
            "payment_method": "debit",
            "subcategory": "Compras Depa"
        },
        {
            "date": today - timedelta(days=3),
            "description": "Restaurant La Rosa Nautica",
            "amount": Decimal("185.00"),
            "category": "Alimentacion",
            "participant": chebos,
            "payment_method": "credit",
            "subcategory": "Restaurant"
        },
        {
            "date": today - timedelta(days=5),
            "description": "Uber al trabajo",
            "amount": Decimal("25.50"),
            "category": "Transporte",
            "participant": lu,
            "payment_method": "debit",
            "subcategory": "Taxi"
        },
        {
            "date": today - timedelta(days=7),
            "description": "Netflix",
            "amount": Decimal("45.90"),
            "category": "Entretenimiento",
            "participant": chebos,
            "payment_method": "credit",
            "subcategory": "Streaming"
        },
        {
            "date": today - timedelta(days=10),
            "description": "Luz - Enel",
            "amount": Decimal("120.00"),
            "category": "Servicios",
            "participant": lu,
            "payment_method": "debit",
            "subcategory": "Luz"
        },
        {
            "date": today - timedelta(days=12),
            "description": "Internet Movistar",
            "amount": Decimal("89.90"),
            "category": "Servicios",
            "participant": chebos,
            "payment_method": "debit",
            "subcategory": "Internet"
        },
        {
            "date": today - timedelta(days=15),
            "description": "Farmacia - Vitaminas",
            "amount": Decimal("65.00"),
            "category": "Salud",
            "participant": lu,
            "payment_method": "debit",
            "subcategory": "Suplementos"
        },
    ]

    transactions_created = 0
    for t_data in transactions_data:
        category = get_category(t_data["category"])
        if category:
            transaction = Transaction(
                date=t_data["date"].date(),
                description=t_data["description"],
                amount=t_data["amount"],
                category_id=category.id,
                participant_id=t_data["participant"].id,
                payment_method=t_data["payment_method"],
                subcategory=t_data.get("subcategory")
            )
            db.add(transaction)
            transactions_created += 1

    db.commit()
    print(f"   ✓ Created {transactions_created} transactions")


def create_credit_cards(db, participants):
    """Create sample credit cards"""
    print("\n💳 Creating credit cards...")

    lu = next(p for p in participants if p.name == "Lu")
    chebos = next(p for p in participants if p.name == "Chebos")

    cards_data = [
        {
            "name": "Visa Banco Nacional",
            "closing_day": 15,
            "payment_day": 5
        },
        {
            "name": "Mastercard Premium",
            "closing_day": 20,
            "payment_day": 10
        },
    ]

    cards_created = 0
    for card_data in cards_data:
        # Check if exists
        existing = db.query(CreditCard).filter(
            CreditCard.name == card_data["name"]
        ).first()

        if not existing:
            card = CreditCard(**card_data)
            db.add(card)
            cards_created += 1

    db.commit()
    print(f"   ✓ Created {cards_created} credit cards")


def main():
    """Main function to create all test data"""
    print("🌱 Creating test data for Finanzas app...")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Check if categories exist
        categories = db.query(Category).all()
        if not categories:
            print("❌ No categories found! Please run load_seeds.py first.")
            return

        print(f"✓ Found {len(categories)} categories in database")

        # Create data
        participants = create_participants(db)
        create_budget(db, categories)
        create_transactions(db, participants, categories)
        create_credit_cards(db, participants)

        print("\n" + "=" * 60)
        print("✅ Test data created successfully!")
        print("\nYou can now:")
        print("  1. Start the backend: cd backend && ../. venv/bin/python -m uvicorn app.main:app --reload")
        print("  2. Start the frontend: cd frontend && npm run dev")
        print("  3. Visit http://localhost:5173 to see your data!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
