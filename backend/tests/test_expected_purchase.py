"""
Tests for ExpectedPurchase API endpoints.
"""
import pytest
from uuid import uuid4


def test_create_expected_purchase_cash(client, test_db):
    """Test creating an expected purchase with cash payment."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    response = client.post("/expected-purchases/", json={
        "description": "Future laptop purchase",
        "amount": 1500.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Future laptop purchase"
    assert float(data["amount"]) == 1500.00
    assert data["expected_date"] == "2024-03-15"
    assert data["converted_to_transaction"] is False
    assert "id" in data


def test_create_expected_purchase_credit(client, test_db):
    """Test creating an expected purchase with credit payment."""
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

    response = client.post("/expected-purchases/", json={
        "description": "Laptop in installments",
        "amount": 1800.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "installments": 6
    })

    assert response.status_code == 201
    data = response.json()
    assert data["payment_method"] == "CREDIT"
    assert data["installments"] == 6


def test_create_expected_purchase_credit_without_card(client, test_db):
    """Test that credit purchases require card_id."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()

    response = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1800.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT"
        # Missing card_id and installments
    })

    assert response.status_code == 422


def test_create_expected_purchase_category_not_allows_credit(client, test_db):
    """Test that credit purchases require category that allows credit."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE",
        "allows_credit": False
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    response = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1800.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "installments": 6
    })

    assert response.status_code == 400
    assert "does not allow credit" in response.json()["detail"].lower()


def test_get_all_expected_purchases(client, test_db):
    """Test retrieving all expected purchases."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Create two purchases
    client.post("/expected-purchases/", json={
        "description": "Purchase 1",
        "amount": 100.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    client.post("/expected-purchases/", json={
        "description": "Purchase 2",
        "amount": 200.00,
        "expected_date": "2024-04-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "DEBIT"
    })

    response = client.get("/expected-purchases/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_expected_purchases_by_converted(client, test_db):
    """Test filtering expected purchases by conversion status."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Create two purchases
    purchase1 = client.post("/expected-purchases/", json={
        "description": "To Convert",
        "amount": 100.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    client.post("/expected-purchases/", json={
        "description": "Not Converted",
        "amount": 200.00,
        "expected_date": "2024-04-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    })

    # Convert one
    client.post(f"/expected-purchases/{purchase1['id']}/convert")

    # Get converted
    response = client.get("/expected-purchases/?converted=true")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Get not converted
    response = client.get("/expected-purchases/?converted=false")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_simulate_expected_purchase_cash(client, test_db):
    """Test simulating a cash purchase."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Electronics",
        "type": "EXPENSE"
    }).json()

    # Create budget for March
    client.post("/budgets/", json={
        "month": "2024-03",
        "category_id": category["id"],
        "limit": 1000.00
    })

    # Create expected purchase
    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 800.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Simulate
    response = client.get(f"/expected-purchases/{purchase['id']}/simulate")
    assert response.status_code == 200
    data = response.json()

    assert data["description"] == "Laptop"
    assert data["impact_summary"]["total_amount"] == 800.00
    assert data["impact_summary"]["number_of_installments"] == 1
    assert len(data["monthly_impact"]) == 1

    # Check budget impact
    month_impact = data["monthly_impact"][0]
    assert month_impact["month"] == "2024-03"
    assert month_impact["amount"] == 800.00
    assert month_impact["budget_limit"] == 1000.00
    assert month_impact["remaining_budget"] == 200.00
    assert month_impact["over_budget"] is False


def test_simulate_expected_purchase_credit_installments(client, test_db):
    """Test simulating a credit purchase with installments."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Electronics",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create budgets for multiple months
    for month in ["2024-04", "2024-05", "2024-06"]:
        client.post("/budgets/", json={
            "month": month,
            "category_id": category["id"],
            "limit": 500.00
        })

    # Create expected purchase (1200 in 3 installments = 400 each)
    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop in installments",
        "amount": 1200.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "installments": 3
    }).json()

    # Simulate
    response = client.get(f"/expected-purchases/{purchase['id']}/simulate")
    assert response.status_code == 200
    data = response.json()

    assert data["impact_summary"]["total_amount"] == 1200.00
    assert data["impact_summary"]["number_of_installments"] == 3
    assert data["impact_summary"]["monthly_payment"] == 400.00
    assert data["impact_summary"]["affects_months"] == 3
    assert len(data["monthly_impact"]) == 3

    # Check each month's impact (installments start next month)
    assert data["monthly_impact"][0]["month"] == "2024-04"
    assert data["monthly_impact"][0]["installment_number"] == 1
    assert data["monthly_impact"][0]["amount"] == 400.00

    assert data["monthly_impact"][1]["month"] == "2024-05"
    assert data["monthly_impact"][1]["installment_number"] == 2

    assert data["monthly_impact"][2]["month"] == "2024-06"
    assert data["monthly_impact"][2]["installment_number"] == 3


def test_simulate_shows_budget_exceeded(client, test_db):
    """Test that simulation shows when budget would be exceeded."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Electronics",
        "type": "EXPENSE",
        "allows_credit": True
    }).json()
    card = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    }).json()

    # Create tight budget
    client.post("/budgets/", json={
        "month": "2024-04",
        "category_id": category["id"],
        "limit": 300.00
    })

    # Purchase that exceeds budget (600 in 1 installment)
    purchase = client.post("/expected-purchases/", json={
        "description": "Expensive laptop",
        "amount": 600.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CREDIT",
        "card_id": card["id"],
        "installments": 1
    }).json()

    response = client.get(f"/expected-purchases/{purchase['id']}/simulate")
    data = response.json()

    month_impact = data["monthly_impact"][0]
    assert month_impact["over_budget"] is True
    assert month_impact["remaining_budget"] == -300.00  # 300 - 600


def test_convert_expected_purchase_to_transaction(client, test_db):
    """Test converting an expected purchase to an actual transaction."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1500.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Convert to transaction
    response = client.post(f"/expected-purchases/{purchase['id']}/convert")
    assert response.status_code == 200
    transaction = response.json()

    # Verify transaction was created
    assert transaction["description"] == "Laptop"
    assert float(transaction["amount"]) == 1500.00
    assert transaction["category_id"] == category["id"]

    # Verify purchase is marked as converted
    purchase_response = client.get(f"/expected-purchases/{purchase['id']}")
    assert purchase_response.json()["converted_to_transaction"] is True
    assert purchase_response.json()["transaction_id"] == transaction["id"]


def test_cannot_convert_twice(client, test_db):
    """Test that a purchase cannot be converted twice."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1500.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Convert once
    client.post(f"/expected-purchases/{purchase['id']}/convert")

    # Try to convert again
    response = client.post(f"/expected-purchases/{purchase['id']}/convert")
    assert response.status_code == 400
    assert "already been converted" in response.json()["detail"].lower()


def test_update_expected_purchase(client, test_db):
    """Test updating an expected purchase."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "Original",
        "amount": 1000.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Update
    response = client.put(f"/expected-purchases/{purchase['id']}", json={
        "description": "Updated",
        "amount": 1200.00
    })

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated"
    assert float(data["amount"]) == 1200.00
    assert data["expected_date"] == "2024-03-15"  # unchanged


def test_cannot_update_converted_purchase(client, test_db):
    """Test that converted purchases cannot be updated."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1500.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Convert
    client.post(f"/expected-purchases/{purchase['id']}/convert")

    # Try to update
    response = client.put(f"/expected-purchases/{purchase['id']}", json={
        "description": "Updated"
    })

    assert response.status_code == 400
    assert "converted" in response.json()["detail"].lower()


def test_delete_expected_purchase(client, test_db):
    """Test deleting an expected purchase."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "To Delete",
        "amount": 1000.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    response = client.delete(f"/expected-purchases/{purchase['id']}")
    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(f"/expected-purchases/{purchase['id']}")
    assert get_response.status_code == 404


def test_cannot_delete_converted_purchase(client, test_db):
    """Test that converted purchases cannot be deleted."""
    participant = client.post("/participants/", json={"name": "Lu"}).json()
    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    purchase = client.post("/expected-purchases/", json={
        "description": "Laptop",
        "amount": 1500.00,
        "expected_date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": participant["id"],
        "payment_method": "CASH"
    }).json()

    # Convert
    client.post(f"/expected-purchases/{purchase['id']}/convert")

    # Try to delete
    response = client.delete(f"/expected-purchases/{purchase['id']}")
    assert response.status_code == 400
    assert "converted" in response.json()["detail"].lower()


def test_get_expected_purchase_not_found(client, test_db):
    """Test getting non-existent expected purchase."""
    fake_id = str(uuid4())
    response = client.get(f"/expected-purchases/{fake_id}")
    assert response.status_code == 404
