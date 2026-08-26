"""
Tests for Transaction API endpoints.
"""
import pytest
from fastapi import status
from datetime import date


@pytest.fixture
def sample_participant(client):
    """Create a sample participant for testing"""
    response = client.post(
        "/participants/",
        json={"name": "Test Person", "default_percentage": 50.0}
    )
    return response.json()


@pytest.fixture
def sample_category(client):
    """Create a sample category that allows credit"""
    response = client.post(
        "/categories/",
        json={"name": "Test Expense", "type": "expense", "allows_credit": True}
    )
    return response.json()


@pytest.fixture
def no_credit_category(client):
    """Create a category that doesn't allow credit"""
    response = client.post(
        "/categories/",
        json={"name": "No Credit Category", "type": "expense", "allows_credit": False}
    )
    return response.json()


def test_create_cash_transaction(client, sample_category, sample_participant):
    """Test creating a cash transaction"""
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.50,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash",
            "description": "Test cash purchase"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["date"] == "2026-01-15"
    assert float(data["amount"]) == 100.50
    assert data["payment_method"] == "cash"
    assert data["is_credit"] is False
    assert "id" in data


def test_create_debit_transaction(client, sample_category, sample_participant):
    """Test creating a debit card transaction"""
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 250.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "debit"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["payment_method"] == "debit"
    assert data["is_credit"] is False


def test_create_credit_transaction_with_card(client, sample_category, sample_participant):
    """Test creating a credit card transaction"""
    # For now, we'll use a UUID for card_id (will be validated when CreditCard module is implemented)
    fake_card_id = "12345678-1234-1234-1234-123456789012"

    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 500.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "credit",
            "card_id": fake_card_id,
            "installments": 3
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["payment_method"] == "credit"
    assert data["is_credit"] is True
    assert data["installments"] == 3


def test_create_credit_transaction_without_card_id(client, sample_category, sample_participant):
    """Test that credit transactions require card_id"""
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 500.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "credit"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_transaction_credit_not_allowed(client, no_credit_category, sample_participant):
    """Test that credit is rejected for categories that don't allow it"""
    fake_card_id = "12345678-1234-1234-1234-123456789012"

    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 500.00,
            "category_id": no_credit_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "credit",
            "card_id": fake_card_id
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not allow credit" in response.json()["detail"]


def test_create_transaction_negative_amount(client, sample_category, sample_participant):
    """Test that negative amounts are rejected"""
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": -100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_transaction_zero_amount(client, sample_category, sample_participant):
    """Test that zero amount is rejected"""
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 0.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_transaction_nonexistent_category(client, sample_participant):
    """Test creating transaction with non-existent category"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": fake_id,
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_transaction_nonexistent_participant(client, sample_category):
    """Test creating transaction with non-existent participant"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": fake_id,
            "payment_method": "cash"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_transactions(client, sample_category, sample_participant):
    """Test getting all transactions"""
    # Create test transactions
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-16",
            "amount": 200.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "debit"
        }
    )

    response = client.get("/transactions/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Should be ordered by date desc (newest first)
    assert data[0]["date"] == "2026-01-16"


def test_get_all_transactions_excludes_credit_card_payment_category(client, sample_participant):
    """Legacy credit card payment entries should not appear as regular transactions."""
    payment_category = client.post(
        "/categories/",
        json={
            "name": "Pago Tarjeta de Credito",
            "type": "expense",
            "is_personal": True,
            "allows_credit": False,
        }
    ).json()

    response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-30",
            "amount": 33.80,
            "category_id": payment_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash",
            "description": "Pago cuota 1 - Ramen bulldog"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.get("/transactions/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    response = client.get("/transactions/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_transactions"] == 0
    assert data["total_amount"] == 0


def test_filter_transactions_by_payment_method(client, sample_category, sample_participant):
    """Test filtering transactions by payment method"""
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-16",
            "amount": 200.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "debit"
        }
    )

    response = client.get("/transactions/?payment_method=cash")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["payment_method"] == "cash"


def test_filter_transactions_by_date_range(client, sample_category, sample_participant):
    """Test filtering transactions by date range"""
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-10",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-20",
            "amount": 200.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )

    response = client.get("/transactions/?start_date=2026-01-15&end_date=2026-01-25")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2026-01-20"


def test_get_transaction_by_id(client, sample_category, sample_participant):
    """Test getting a specific transaction"""
    create_response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    transaction_id = create_response.json()["id"]

    response = client.get(f"/transactions/{transaction_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["date"] == "2026-01-15"


def test_update_transaction(client, sample_category, sample_participant):
    """Test updating a transaction"""
    create_response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    transaction_id = create_response.json()["id"]

    response = client.put(
        f"/transactions/{transaction_id}",
        json={"amount": 150.00, "description": "Updated"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert float(data["amount"]) == 150.00
    assert data["description"] == "Updated"


def test_delete_transaction(client, sample_category, sample_participant):
    """Test deleting a transaction"""
    create_response = client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    transaction_id = create_response.json()["id"]

    response = client.delete(f"/transactions/{transaction_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/transactions/{transaction_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_transaction_summary(client, sample_category, sample_participant):
    """Test getting transaction summary"""
    # Create another category
    category2 = client.post(
        "/categories/",
        json={"name": "Another Category", "type": "expense"}
    ).json()

    # Create transactions
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-15",
            "amount": 100.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-16",
            "amount": 200.00,
            "category_id": sample_category["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )
    client.post(
        "/transactions/",
        json={
            "date": "2026-01-17",
            "amount": 300.00,
            "category_id": category2["id"],
            "participant_id": sample_participant["id"],
            "payment_method": "cash"
        }
    )

    response = client.get("/transactions/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_transactions"] == 3
    assert data["total_amount"] == 600.00
    assert len(data["summary"]) == 2
