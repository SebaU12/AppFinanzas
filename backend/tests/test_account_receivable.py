"""
Tests for AccountReceivable API endpoints.
"""
import pytest
from uuid import uuid4


def test_create_account_receivable(client, test_db):
    """Test creating a new account receivable."""
    response = client.post("/accounts-receivable/", json={
        "description": "Reimbursement expected",
        "amount": 500.00,
        "due_date": "2024-02",
        "received": False
    })
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Reimbursement expected"
    assert float(data["amount"]) == 500.00
    assert data["due_date"] == "2024-02"
    assert data["received"] is False
    assert "id" in data


def test_create_account_receivable_invalid_due_date(client, test_db):
    """Test that invalid due date formats are rejected."""
    response = client.post("/accounts-receivable/", json={
        "description": "Payment",
        "amount": 100.00,
        "due_date": "2024-2"  # should be 2024-02
    })
    assert response.status_code == 422


def test_create_account_receivable_with_participant(client, test_db):
    """Test creating a receivable linked to a participant."""
    participant = client.post("/participants/", json={"name": "Seba"}).json()

    response = client.post("/accounts-receivable/", json={
        "description": "Payment from Seba",
        "amount": 200.00,
        "due_date": "2024-02",
        "participant_id": participant["id"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["participant_id"] == participant["id"]


def test_create_account_receivable_with_received_date(client, test_db):
    """Test creating a receivable with received date."""
    response = client.post("/accounts-receivable/", json={
        "description": "Received payment",
        "amount": 200.00,
        "due_date": "2024-02",
        "received": True,
        "received_date": "2024-02-15"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["received"] is True
    assert data["received_date"] == "2024-02-15"


def test_get_all_accounts_receivable(client, test_db):
    """Test retrieving all accounts receivable."""
    # Create test receivables
    client.post("/accounts-receivable/", json={
        "description": "Payment 1",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    client.post("/accounts-receivable/", json={
        "description": "Payment 2",
        "amount": 200.00,
        "due_date": "2024-03"
    })

    response = client.get("/accounts-receivable/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_filter_accounts_receivable_by_due_date(client, test_db):
    """Test filtering accounts receivable by due date."""
    client.post("/accounts-receivable/", json={
        "description": "Feb Payment",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    client.post("/accounts-receivable/", json={
        "description": "Mar Payment",
        "amount": 200.00,
        "due_date": "2024-03"
    })

    response = client.get("/accounts-receivable/?due_date=2024-02")
    assert response.status_code == 200
    receivables = response.json()
    assert len(receivables) == 1
    assert receivables[0]["due_date"] == "2024-02"


def test_filter_accounts_receivable_by_received_status(client, test_db):
    """Test filtering accounts receivable by received status."""
    client.post("/accounts-receivable/", json={
        "description": "Pending",
        "amount": 100.00,
        "due_date": "2024-02",
        "received": False
    })
    client.post("/accounts-receivable/", json={
        "description": "Received",
        "amount": 200.00,
        "due_date": "2024-02",
        "received": True
    })

    # Get pending
    response = client.get("/accounts-receivable/?received=false")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Get received
    response = client.get("/accounts-receivable/?received=true")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_accounts_receivable_by_participant(client, test_db):
    """Test filtering accounts receivable by participant."""
    participant1 = client.post("/participants/", json={"name": "Lu"}).json()
    participant2 = client.post("/participants/", json={"name": "Seba"}).json()

    client.post("/accounts-receivable/", json={
        "description": "From Lu",
        "amount": 100.00,
        "due_date": "2024-02",
        "participant_id": participant1["id"]
    })
    client.post("/accounts-receivable/", json={
        "description": "From Seba",
        "amount": 200.00,
        "due_date": "2024-02",
        "participant_id": participant2["id"]
    })

    response = client.get(f"/accounts-receivable/?participant_id={participant1['id']}")
    assert response.status_code == 200
    receivables = response.json()
    assert len(receivables) == 1
    assert receivables[0]["participant_id"] == participant1["id"]


def test_get_account_receivable_by_id(client, test_db):
    """Test retrieving a specific account receivable by ID."""
    create_response = client.post("/accounts-receivable/", json={
        "description": "Test Payment",
        "amount": 300.00,
        "due_date": "2024-02"
    })
    receivable_id = create_response.json()["id"]

    response = client.get(f"/accounts-receivable/{receivable_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == receivable_id
    assert data["description"] == "Test Payment"


def test_get_account_receivable_not_found(client, test_db):
    """Test retrieving a non-existent account receivable."""
    fake_id = str(uuid4())
    response = client.get(f"/accounts-receivable/{fake_id}")
    assert response.status_code == 404


def test_update_account_receivable(client, test_db):
    """Test updating an account receivable."""
    create_response = client.post("/accounts-receivable/", json={
        "description": "Original",
        "amount": 100.00,
        "due_date": "2024-02",
        "received": False
    })
    receivable_id = create_response.json()["id"]

    # Mark as received
    response = client.put(f"/accounts-receivable/{receivable_id}", json={
        "received": True,
        "received_date": "2024-02-20"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["received"] is True
    assert data["received_date"] == "2024-02-20"
    assert data["description"] == "Original"  # unchanged


def test_update_account_receivable_not_found(client, test_db):
    """Test updating a non-existent account receivable."""
    fake_id = str(uuid4())
    response = client.put(f"/accounts-receivable/{fake_id}", json={
        "received": True
    })
    assert response.status_code == 404


def test_delete_account_receivable(client, test_db):
    """Test deleting an account receivable."""
    create_response = client.post("/accounts-receivable/", json={
        "description": "To Delete",
        "amount": 100.00,
        "due_date": "2024-02"
    })
    receivable_id = create_response.json()["id"]

    response = client.delete(f"/accounts-receivable/{receivable_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/accounts-receivable/{receivable_id}")
    assert get_response.status_code == 404


def test_delete_account_receivable_not_found(client, test_db):
    """Test deleting a non-existent account receivable."""
    fake_id = str(uuid4())
    response = client.delete(f"/accounts-receivable/{fake_id}")
    assert response.status_code == 404


def test_get_monthly_summary(client, test_db):
    """Test getting monthly summary of accounts receivable."""
    # Create receivables for February
    client.post("/accounts-receivable/", json={
        "description": "Payment 1",
        "amount": 100.00,
        "due_date": "2024-02",
        "received": False
    })
    client.post("/accounts-receivable/", json={
        "description": "Payment 2",
        "amount": 200.00,
        "due_date": "2024-02",
        "received": True
    })

    response = client.get("/accounts-receivable/summary/2024-02")
    assert response.status_code == 200
    summary = response.json()

    assert summary["month"] == "2024-02"
    assert summary["total_count"] == 2
    assert summary["total_amount"] == 300.00
    assert summary["received_count"] == 1
    assert summary["received_amount"] == 200.00
    assert summary["pending_count"] == 1
    assert summary["pending_amount"] == 100.00
