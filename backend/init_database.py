"""
Initialize the database - create all tables
Run with: python init_database.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base

# Import all models so they're registered with Base
from models.participant import Participant
from models.category import Category
from models.transaction import Transaction
from models.monthly_budget import MonthlyBudget
from models.credit_card import CreditCard
from models.card_installment import CardInstallment
from models.account_payable import AccountPayable
from models.account_receivable import AccountReceivable
from models.monthly_reimbursement import MonthlyReimbursement
from models.reimbursement_detail import ReimbursementDetail
from models.expected_purchase import ExpectedPurchase


def init_db():
    """Create all database tables"""
    print("🗄️  Initializing database...")
    print("=" * 60)

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ Successfully created all database tables!")
        print("\nTables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")

        print("\n" + "=" * 60)
        print("Next steps:")
        print("  1. Run: python load_seeds.py")
        print("  2. Run: python create_test_data.py")
        print("  3. Start the backend!")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    init_db()
