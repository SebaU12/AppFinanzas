"""
Load category seeds into the database
Run with: python load_seeds.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from models.category import Category
from seeds.categories_seed import CATEGORIES_SEED


def load_categories():
    """Load categories from seed data into database"""
    db = SessionLocal()

    try:
        # Check if categories already exist
        existing_count = db.query(Category).count()

        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} categories.")
            response = input("Do you want to clear and reload? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled. No changes made.")
                return

            # Clear existing categories
            db.query(Category).delete()
            db.commit()
            print("🗑️  Cleared existing categories")

        # Load new categories
        categories_added = 0
        for cat_data in CATEGORIES_SEED:
            category = Category(**cat_data)
            db.add(category)
            categories_added += 1

        db.commit()
        print(f"✅ Successfully loaded {categories_added} categories!")

        # Display summary
        income_count = sum(1 for c in CATEGORIES_SEED if c['type'] == 'income')
        expense_count = sum(1 for c in CATEGORIES_SEED if c['type'] == 'expense')
        personal_count = sum(1 for c in CATEGORIES_SEED if c.get('is_personal', False))
        credit_allowed = sum(1 for c in CATEGORIES_SEED if c.get('allows_credit', False))

        print(f"\n📊 Category Summary:")
        print(f"   - Income categories: {income_count}")
        print(f"   - Expense categories: {expense_count}")
        print(f"   - Personal expenses: {personal_count}")
        print(f"   - Credit card allowed: {credit_allowed}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error loading categories: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Loading category seeds...")
    print("=" * 50)
    load_categories()
    print("=" * 50)
