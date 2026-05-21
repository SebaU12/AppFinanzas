"""
Tests for AccountPayable API endpoints.
"""
import pytest
from uuid import uuid4


def test_create_account_payable(client, test_db):
    """Test creating a new account payable."""
    response = client.post("/accounts-payable/", json={
        "description": "Credit card payment",
        "amount": 500.00,
        "due_date": "2024-02",
        "paid": False
    })
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Credit card payment"
    assert float(data["amount"]) == 500.00
    assert data["due_date"] == "2024-02"
    assert data["paid"] is False
    assert "id" in data


def test_create_account_payable_invalid_due_date(client, test_db):
    """Test that invalid due date formats are rejected."""
    response = client.post("/accounts-payable/", json={
        "description": "Payment",
        "amount": 100.00,
        "due_date": "2024-2"  # should be 2024-02
    })
    assert response.status_code == 422


def test_create_account_payable_with_paid_date(client, test_db):
    """Test creating a payable with paid date."""
    response = client.post("/accounts-payable/", json={
        "description": "Paid bill",
        "amount": 200.00,
        "due_date": "2024-02",
        "paid": True,
        "paid_date": "2024-02-15"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["paid"] is True
    assert data["paid_date"] == "2024-02-15"


def test_get_all_accounts_payable(client, test_db):
    """Test retrieving all accounts payable."""
    # Create test payables
    client.post("/accounts-payable/", json={
        "description": "Payment 1",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    client.post("/accounts-payable/", json={
        "description": "Payment 2",
        "amount": 200.00,
        "due_date": "2024-03"
    })

    response = client.get("/accounts-payable/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_filter_accounts_payable_by_due_date(client, test_db):
    """Test filtering accounts payable by due date."""
    client.post("/accounts-payable/", json={
        "description": "Feb Payment",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    client.post("/accounts-payable/", json={
        "description": "Mar Payment",
        "amount": 200.00,
        "due_date": "2024-03"
    })

    response = client.get("/accounts-payable/?due_date=2024-02")
    assert response.status_code == 200
    payables = response.json()
    assert len(payables) == 1
    assert payables[0]["due_date"] == "2024-02"


def test_filter_accounts_payable_by_paid_status(client, test_db):
    """Test filtering accounts payable by paid status."""
    client.post("/accounts-payable/", json={
        "description": "Unpaid",
        "amount": 100.00,
        "due_date": "2024-02",
        "paid": False
    })
    client.post("/accounts-payable/", json={
        "description": "Paid",
        "amount": 200.00,
        "due_date": "2024-02",
        "paid": True
    })

    # Get unpaid
    response = client.get("/accounts-payable/?paid=false")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Get paid
    response = client.get("/accounts-payable/?paid=true")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_account_payable_by_id(client, test_db):
    """Test retrieving a specific account payable by ID."""
    create_response = client.post("/accounts-payable/", json={
        "description": "Test Payment",
        "amount": 300.00,
        "due_date": "2024-02"
    })
    payable_id = create_response.json()["id"]

    response = client.get(f"/accounts-payable/{payable_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payable_id
    assert data["description"] == "Test Payment"


def test_get_account_payable_not_found(client, test_db):
    """Test retrieving a non-existent account payable."""
    fake_id = str(uuid4())
    response = client.get(f"/accounts-payable/{fake_id}")
    assert response.status_code == 404


def test_update_account_payable(client, test_db):
    """Test updating an account payable."""
    create_response = client.post("/accounts-payable/", json={
        "description": "Original",
        "amount": 100.00,
        "due_date": "2024-02",
        "paid": False
    })
    payable_id = create_response.json()["id"]

    # Mark as paid
    response = client.put(f"/accounts-payable/{payable_id}", json={
        "paid": True,
        "paid_date": "2024-02-20"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["paid"] is True
    assert data["paid_date"] == "2024-02-20"
    assert data["description"] == "Original"  # unchanged


def test_update_account_payable_not_found(client, test_db):
    """Test updating a non-existent account payable."""
    fake_id = str(uuid4())
    response = client.put(f"/accounts-payable/{fake_id}", json={
        "paid": True
    })
    assert response.status_code == 404


def test_delete_account_payable(client, test_db):
    """Test deleting an account payable."""
    create_response = client.post("/accounts-payable/", json={
        "description": "To Delete",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    payable_id = create_response.json()["id"]

    response = client.delete(f"/accounts-payable/{payable_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/accounts-payable/{payable_id}")
    assert get_response.status_code == 404


def test_delete_account_payable_not_found(client, test_db):
    """Test deleting a non-existent account payable."""
    fake_id = str(uuid4())
    response = client.delete(f"/accounts-payable/{fake_id}")
    assert response.status_code == 404


def test_generate_accounts_payable_from_installments(client, test_db):
    """Test generating accounts payable from credit card installments."""
    # Create prerequisites
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

    # Create credit transaction (will generate installments)
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

    # Generate payables from installments
    response = client.post("/accounts-payable/generate")
    assert response.status_code == 200
    payables = response.json()

    # Should have 3 payables (one for each installment)
    assert len(payables) == 3
    for payable in payables:
        assert float(payable["amount"]) == 200.00
        assert payable["paid"] is False


def test_get_monthly_summary(client, test_db):
    """Test getting monthly summary of accounts payable."""
    # Create payables for February
    client.post("/accounts-payable/", json={
        "description": "Payment 1",
        "amount": 100.00,
        "due_date": "2024-02",
        "paid": False
    })
    client.post("/accounts-payable/", json={
        "description": "Payment 2",
        "amount": 200.00,
        "due_date": "2024-02",
        "paid": True
    })

    response = client.get("/accounts-payable/summary/2024-02")
    assert response.status_code == 200
    summary = response.json()

    assert summary["month"] == "2024-02"
    assert summary["total_count"] == 2
    assert summary["total_amount"] == 300.00
    assert summary["paid_count"] == 1
    assert summary["paid_amount"] == 200.00
    assert summary["unpaid_count"] == 1
    assert summary["unpaid_amount"] == 100.00
