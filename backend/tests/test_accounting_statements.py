"""
Tests for Accounting Statements API endpoints.
"""
import pytest


def test_income_statement_basic(client, test_db):
    """Test generating basic income statement."""
    # Create test data
    participant = client.post("/participants/", json={"name": "Lu"}).json()

    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    expense_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    # Create transactions
    client.post("/transactions/", json={
        "description": "Monthly salary",
        "amount": 5000.00,
        "date": "2024-02-15",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Groceries",
        "amount": 300.00,
        "date": "2024-02-20",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Get income statement for February
    response = client.get("/statements/income-statement?start_date=2024-02-01&end_date=2024-02-29")
    assert response.status_code == 200
    data = response.json()

    assert data["statement_type"] == "Income Statement"
    assert data["revenues"]["total"] == 5000.00
    assert data["expenses"]["total"] == 300.00
    assert data["net_income"] == 4700.00

    # Check category breakdown
    assert len(data["revenues"]["items"]) == 1
    assert data["revenues"]["items"][0]["category"] == "Salary"

    assert len(data["expenses"]["items"]) == 1
    assert data["expenses"]["items"][0]["category"] == "Groceries"


def test_income_statement_multiple_categories(client, test_db):
    """Test income statement with multiple categories."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()

    # Multiple income categories
    salary_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    bonus_cat = client.post("/categories/", json={
        "name": "Bonus",
        "type": "INCOME"
    }).json()

    # Multiple expense categories
    grocery_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    transport_cat = client.post("/categories/", json={
        "name": "Transport",
        "type": "EXPENSE"
    }).json()

    # Create transactions
    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": salary_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Bonus",
        "amount": 1000.00,
        "date": "2024-02-15",
        "category_id": bonus_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Groceries",
        "amount": 400.00,
        "date": "2024-02-10",
        "category_id": grocery_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Gas",
        "amount": 100.00,
        "date": "2024-02-20",
        "category_id": transport_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    response = client.get("/statements/income-statement?start_date=2024-02-01&end_date=2024-02-29")
    data = response.json()

    assert data["revenues"]["total"] == 6000.00
    assert data["expenses"]["total"] == 500.00
    assert data["net_income"] == 5500.00


def test_income_statement_date_range_filter(client, test_db):
    """Test that income statement filters by date range correctly."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # February transaction
    client.post("/transactions/", json={
        "description": "Feb expense",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # March transaction
    client.post("/transactions/", json={
        "description": "Mar expense",
        "amount": 200.00,
        "date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Get February only
    response = client.get("/statements/income-statement?start_date=2024-02-01&end_date=2024-02-29")
    data = response.json()

    assert data["expenses"]["total"] == 100.00

    # Get March only
    response = client.get("/statements/income-statement?start_date=2024-03-01&end_date=2024-03-31")
    data = response.json()

    assert data["expenses"]["total"] == 200.00


def test_cash_flow_statement_basic(client, test_db):
    """Test generating basic cash flow statement."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()

    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    expense_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    # Cash transactions
    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Groceries",
        "amount": 300.00,
        "date": "2024-02-15",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "DEBIT"
    })

    response = client.get("/statements/cash-flow?start_date=2024-02-01&end_date=2024-02-29")
    assert response.status_code == 200
    data = response.json()

    assert data["statement_type"] == "Cash Flow Statement"
    assert data["operating_activities"]["cash_inflows"] == 5000.00
    assert data["operating_activities"]["cash_outflows"] == 300.00
    assert data["operating_activities"]["net_operating_cash_flow"] == 4700.00
    assert data["net_cash_flow"] == 4700.00


def test_cash_flow_excludes_credit_transactions(client, test_db):
    """Test that cash flow excludes credit transactions from operating activities."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    expense_cat = client.post("/categories/", json={
        "name": "Electronics",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Cash expense
    client.post("/transactions/", json={
        "description": "Cash purchase",
        "amount": 100.00,
        "date": "2024-02-10",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Credit expense (should not appear in cash flow)
    client.post("/transactions/", json={
        "description": "Credit purchase",
        "amount": 600.00,
        "date": "2024-02-15",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    })

    response = client.get("/statements/cash-flow?start_date=2024-02-01&end_date=2024-02-29")
    data = response.json()

    # Only cash expense should appear
    assert data["operating_activities"]["cash_outflows"] == 100.00


def test_balance_sheet_basic(client, test_db):
    """Test generating basic balance sheet."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()

    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    expense_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    # Income (increases cash)
    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Expense (decreases cash)
    client.post("/transactions/", json={
        "description": "Groceries",
        "amount": 300.00,
        "date": "2024-02-15",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    response = client.get("/statements/balance-sheet?as_of_date=2024-02-28")
    assert response.status_code == 200
    data = response.json()

    assert data["statement_type"] == "Balance Sheet"
    assert data["as_of_date"] == "2024-02-28"

    # Cash should be 5000 - 300 = 4700
    assert data["assets"]["current_assets"]["cash"] == 4700.00

    # Retained earnings should match net income
    assert data["equity"]["retained_earnings"] == 4700.00

    # Balance check
    assert data["balance_check"]["balanced"] is True


def test_balance_sheet_with_payables(client, test_db):
    """Test balance sheet includes accounts payable."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    # Income
    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Create accounts payable
    client.post("/accounts-payable/", json={
        "description": "Credit card bill",
        "amount": 500.00,
        "due_date": "2024-03",
        "paid": False
    })

    response = client.get("/statements/balance-sheet?as_of_date=2024-02-28")
    data = response.json()

    # Should have payable liability
    assert data["liabilities"]["current_liabilities"]["accounts_payable"] == 500.00

    # Balance check should still work
    assert data["balance_check"]["balanced"] is True


def test_balance_sheet_with_receivables(client, test_db):
    """Test balance sheet includes accounts receivable."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    # Income
    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Create accounts receivable
    client.post("/accounts-receivable/", json={
        "description": "Reimbursement due",
        "amount": 300.00,
        "due_date": "2024-03",
        "received": False,
        "participant_id": participant["id"]
    })

    response = client.get("/statements/balance-sheet?as_of_date=2024-02-28")
    data = response.json()

    # Should have receivable asset
    assert data["assets"]["current_assets"]["accounts_receivable"] == 300.00

    # Balance check should still work
    assert data["balance_check"]["balanced"] is True


def test_participant_summary(client, test_db):
    """Test generating participant summary."""
    lu = client.post("/participants/", json={"name": "Lu"}).json()
    seba = client.post("/participants/", json={"name": "Seba"}).json()

    grocery_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    transport_cat = client.post("/categories/", json={
        "name": "Transport",
        "type": "EXPENSE"
    }).json()

    # Lu's transactions
    client.post("/transactions/", json={
        "description": "Lu groceries",
        "amount": 200.00,
        "date": "2024-02-10",
        "category_id": grocery_cat["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Lu transport",
        "amount": 50.00,
        "date": "2024-02-15",
        "category_id": transport_cat["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    # Seba's transactions
    client.post("/transactions/", json={
        "description": "Seba groceries",
        "amount": 150.00,
        "date": "2024-02-12",
        "category_id": grocery_cat["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    response = client.get("/statements/participant-summary?start_date=2024-02-01&end_date=2024-02-29")
    assert response.status_code == 200
    data = response.json()

    assert data["report_type"] == "Participant Summary"
    assert len(data["participants"]) == 2

    # Find Lu's summary
    lu_summary = next(p for p in data["participants"] if p["participant_name"] == "Lu")
    assert lu_summary["total_expenses"] == 250.00
    assert len(lu_summary["category_breakdown"]) == 2

    # Find Seba's summary
    seba_summary = next(p for p in data["participants"] if p["participant_name"] == "Seba")
    assert seba_summary["total_expenses"] == 150.00
    assert len(seba_summary["category_breakdown"]) == 1


def test_participant_summary_with_income(client, test_db):
    """Test participant summary includes income."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()

    income_cat = client.post("/categories/", json={
        "name": "Salary",
        "type": "INCOME"
    }).json()

    expense_cat = client.post("/categories/", json={
        "name": "Groceries",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Salary",
        "amount": 5000.00,
        "date": "2024-02-01",
        "category_id": income_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Groceries",
        "amount": 300.00,
        "date": "2024-02-15",
        "category_id": expense_cat["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    response = client.get("/statements/participant-summary?start_date=2024-02-01&end_date=2024-02-29")
    data = response.json()

    participant_data = data["participants"][0]
    assert participant_data["total_income"] == 5000.00
    assert participant_data["total_expenses"] == 300.00
    assert participant_data["net"] == 4700.00
