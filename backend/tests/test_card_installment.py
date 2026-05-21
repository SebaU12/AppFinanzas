"""
Tests for CardInstallment API endpoints.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime


def test_create_installment_manually(client, test_db):
    """Test creating a card installment manually."""
    # Create prerequisites
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test Category",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Test Purchase",
        "amount": 1000.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    }).json()

    # Create manual installment
    response = client.post("/installments/", json={
        "transaction_id": transaction["id"],
        "month": "2024-02",
        "amount": 100.00,
        "paid": False
    })
    assert response.status_code == 201
    data = response.json()
    assert data["month"] == "2024-02"
    assert float(data["amount"]) == 100.00
    assert data["paid"] is False


def test_create_installment_invalid_month_format(client, test_db):
    """Test that invalid month formats are rejected."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test Category",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Test Purchase",
        "amount": 1000.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    }).json()

    # Invalid month format
    response = client.post("/installments/", json={
        "transaction_id": transaction["id"],
        "month": "2024-1",  # should be 2024-01
        "amount": 100.00
    })
    assert response.status_code == 422


def test_installments_auto_generated_on_credit_transaction(client, test_db):
    """Test that installments are automatically generated when creating a credit transaction."""
    # Create prerequisites
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Electronics",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Mastercard",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create credit transaction with 6 installments
    transaction = client.post("/transactions/", json={
        "description": "Laptop",
        "amount": 3000.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 6
    }).json()

    # Get installments for this transaction
    response = client.get(f"/installments/?transaction_id={transaction['id']}")
    assert response.status_code == 200
    installments = response.json()

    # Should have 6 installments
    assert len(installments) == 6

    # Each should be 500.00
    for inst in installments:
        assert float(inst["amount"]) == 500.00
        assert inst["paid"] is False

    # Check month progression
    assert installments[0]["month"] == "2024-02"
    assert installments[1]["month"] == "2024-03"
    assert installments[2]["month"] == "2024-04"
    assert installments[3]["month"] == "2024-05"
    assert installments[4]["month"] == "2024-06"
    assert installments[5]["month"] == "2024-07"


def test_installments_with_rounding(client, test_db):
    """Test that installment amounts handle rounding correctly."""
    # Create prerequisites
    participant = client.post("/participants/", json={"name": "Seba"}).json()
    category = client.post("/categories/", json={
        "name": "Shopping",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create transaction with amount that doesn't divide evenly
    transaction = client.post("/transactions/", json={
        "description": "Test Purchase",
        "amount": 100.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    }).json()

    # Get installments
    response = client.get(f"/installments/?transaction_id={transaction['id']}")
    installments = response.json()

    # Should have 3 installments
    assert len(installments) == 3

    # Each should be 33.33 (except last which gets adjustment)
    assert float(installments[0]["amount"]) == 33.33
    assert float(installments[1]["amount"]) == 33.33
    assert float(installments[2]["amount"]) == 33.34  # Last gets the adjustment

    # Total should equal original amount
    total = sum(Decimal(str(inst["amount"])) for inst in installments)
    assert total == Decimal("100.00")


def test_installments_cross_year_boundary(client, test_db):
    """Test that installments correctly handle year boundaries."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Transaction in November 2024 with 4 installments
    transaction = client.post("/transactions/", json={
        "description": "Year-end Purchase",
        "amount": 1200.00,
        "date": "2024-11-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 4
    }).json()

    response = client.get(f"/installments/?transaction_id={transaction['id']}")
    installments = response.json()

    assert len(installments) == 4
    # Should roll over to 2025
    assert installments[0]["month"] == "2024-12"
    assert installments[1]["month"] == "2025-01"
    assert installments[2]["month"] == "2025-02"
    assert installments[3]["month"] == "2025-03"


def test_get_all_installments(client, test_db):
    """Test retrieving all installments."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create 2 transactions
    client.post("/transactions/", json={
        "description": "Purchase 1",
        "amount": 600.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 2
    })

    client.post("/transactions/", json={
        "description": "Purchase 2",
        "amount": 900.00,
        "date": "2024-01-20",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    })

    response = client.get("/installments/")
    assert response.status_code == 200
    assert len(response.json()) == 5  # 2 + 3 installments


def test_filter_installments_by_month(client, test_db):
    """Test filtering installments by month."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    client.post("/transactions/", json={
        "description": "Purchase",
        "amount": 600.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    })

    response = client.get("/installments/?month=2024-02")
    assert response.status_code == 200
    installments = response.json()
    assert len(installments) == 1
    assert installments[0]["month"] == "2024-02"


def test_filter_installments_by_paid_status(client, test_db):
    """Test filtering installments by paid status."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Purchase",
        "amount": 300.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 3
    }).json()

    # Get all unpaid
    response = client.get("/installments/?paid=false")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Mark one as paid
    installments = client.get(f"/installments/?transaction_id={transaction['id']}").json()
    client.put(f"/installments/{installments[0]['id']}", json={"paid": True})

    # Get unpaid
    response = client.get("/installments/?paid=false")
    assert len(response.json()) == 2

    # Get paid
    response = client.get("/installments/?paid=true")
    assert len(response.json()) == 1


def test_get_installment_by_id(client, test_db):
    """Test retrieving a specific installment by ID."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Purchase",
        "amount": 300.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 1
    }).json()

    installments = client.get(f"/installments/?transaction_id={transaction['id']}").json()
    installment_id = installments[0]["id"]

    response = client.get(f"/installments/{installment_id}")
    assert response.status_code == 200
    assert response.json()["id"] == installment_id


def test_get_installment_not_found(client, test_db):
    """Test retrieving a non-existent installment."""
    fake_id = str(uuid4())
    response = client.get(f"/installments/{fake_id}")
    assert response.status_code == 404


def test_update_installment_mark_as_paid(client, test_db):
    """Test marking an installment as paid."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Purchase",
        "amount": 300.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 1
    }).json()

    installments = client.get(f"/installments/?transaction_id={transaction['id']}").json()
    installment_id = installments[0]["id"]

    # Mark as paid
    response = client.put(f"/installments/{installment_id}", json={"paid": True})
    assert response.status_code == 200
    assert response.json()["paid"] is True


def test_update_installment_not_found(client, test_db):
    """Test updating a non-existent installment."""
    fake_id = str(uuid4())
    response = client.put(f"/installments/{fake_id}", json={"paid": True})
    assert response.status_code == 404


def test_delete_installment(client, test_db):
    """Test deleting an installment."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()
    transaction = client.post("/transactions/", json={
        "description": "Purchase",
        "amount": 300.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 1
    }).json()

    installments = client.get(f"/installments/?transaction_id={transaction['id']}").json()
    installment_id = installments[0]["id"]

    response = client.delete(f"/installments/{installment_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/installments/{installment_id}")
    assert get_response.status_code == 404


def test_delete_installment_not_found(client, test_db):
    """Test deleting a non-existent installment."""
    fake_id = str(uuid4())
    response = client.delete(f"/installments/{fake_id}")
    assert response.status_code == 404


def test_get_monthly_installment_summary(client, test_db):
    """Test getting monthly installment summary."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create transactions
    client.post("/transactions/", json={
        "description": "Purchase 1",
        "amount": 600.00,
        "date": "2024-01-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 2
    })

    client.post("/transactions/", json={
        "description": "Purchase 2",
        "amount": 300.00,
        "date": "2024-01-20",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "is_credit": True,
        "installments": 1
    })

    # Get summary for February 2024 (should have 300 + 300 = 600)
    response = client.get("/installments/summary/2024-02")
    assert response.status_code == 200
    summary = response.json()

    assert summary["month"] == "2024-02"
    assert summary["total_count"] == 2
    assert float(summary["total_amount"]) == 600.00
    assert summary["unpaid_count"] == 2
    assert float(summary["unpaid_amount"]) == 600.00
    assert summary["paid_count"] == 0
    assert float(summary["paid_amount"]) == 0.00
