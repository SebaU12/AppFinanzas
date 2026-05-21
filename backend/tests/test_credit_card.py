"""
Tests for CreditCard API endpoints.
"""
import pytest
from uuid import uuid4


def test_create_credit_card(client, test_db):
    """Test creating a new credit card."""
    response = client.post("/credit-cards/", json={
        "name": "Visa Gold",
        "closing_day": 15,
        "payment_day": 10
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Visa Gold"
    assert data["closing_day"] == 15
    assert data["payment_day"] == 10
    assert "id" in data
    assert "created_at" in data


def test_create_credit_card_duplicate_name(client, test_db):
    """Test that duplicate credit card names are rejected."""
    client.post("/credit-cards/", json={
        "name": "Mastercard",
        "closing_day": 20,
        "payment_day": 5
    })

    response = client.post("/credit-cards/", json={
        "name": "Mastercard",
        "closing_day": 25,
        "payment_day": 15
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_create_credit_card_invalid_closing_day(client, test_db):
    """Test that invalid closing days are rejected."""
    response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 0,
        "payment_day": 10
    })
    assert response.status_code == 422

    response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 32,
        "payment_day": 10
    })
    assert response.status_code == 422


def test_create_credit_card_invalid_payment_day(client, test_db):
    """Test that invalid payment days are rejected."""
    response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 0
    })
    assert response.status_code == 422

    response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 33
    })
    assert response.status_code == 422


def test_get_all_credit_cards(client, test_db):
    """Test retrieving all credit cards."""
    # Create test cards
    client.post("/credit-cards/", json={"name": "Visa", "closing_day": 15, "payment_day": 10})
    client.post("/credit-cards/", json={"name": "Mastercard", "closing_day": 20, "payment_day": 5})

    response = client.get("/credit-cards/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Visa"
    assert data[1]["name"] == "Mastercard"


def test_get_all_credit_cards_with_pagination(client, test_db):
    """Test pagination for credit cards."""
    # Create 3 cards
    for i in range(3):
        client.post("/credit-cards/", json={
            "name": f"Card {i}",
            "closing_day": 15,
            "payment_day": 10
        })

    # Get first 2
    response = client.get("/credit-cards/?skip=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Get last 1
    response = client.get("/credit-cards/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_credit_card_by_id(client, test_db):
    """Test retrieving a specific credit card by ID."""
    create_response = client.post("/credit-cards/", json={
        "name": "Amex",
        "closing_day": 28,
        "payment_day": 15
    })
    card_id = create_response.json()["id"]

    response = client.get(f"/credit-cards/{card_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == card_id
    assert data["name"] == "Amex"
    assert data["closing_day"] == 28


def test_get_credit_card_not_found(client, test_db):
    """Test retrieving a non-existent credit card."""
    fake_id = str(uuid4())
    response = client.get(f"/credit-cards/{fake_id}")
    assert response.status_code == 404


def test_update_credit_card(client, test_db):
    """Test updating a credit card."""
    create_response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    })
    card_id = create_response.json()["id"]

    response = client.put(f"/credit-cards/{card_id}", json={
        "name": "Visa Platinum",
        "closing_day": 20
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Visa Platinum"
    assert data["closing_day"] == 20
    assert data["payment_day"] == 10  # unchanged


def test_update_credit_card_partial(client, test_db):
    """Test partial update of a credit card."""
    create_response = client.post("/credit-cards/", json={
        "name": "Mastercard",
        "closing_day": 15,
        "payment_day": 10
    })
    card_id = create_response.json()["id"]

    response = client.put(f"/credit-cards/{card_id}", json={
        "payment_day": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Mastercard"  # unchanged
    assert data["closing_day"] == 15  # unchanged
    assert data["payment_day"] == 5  # updated


def test_update_credit_card_not_found(client, test_db):
    """Test updating a non-existent credit card."""
    fake_id = str(uuid4())
    response = client.put(f"/credit-cards/{fake_id}", json={
        "name": "New Name"
    })
    assert response.status_code == 404


def test_delete_credit_card(client, test_db):
    """Test deleting a credit card."""
    create_response = client.post("/credit-cards/", json={
        "name": "Visa",
        "closing_day": 15,
        "payment_day": 10
    })
    card_id = create_response.json()["id"]

    response = client.delete(f"/credit-cards/{card_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/credit-cards/{card_id}")
    assert get_response.status_code == 404


def test_delete_credit_card_not_found(client, test_db):
    """Test deleting a non-existent credit card."""
    fake_id = str(uuid4())
    response = client.delete(f"/credit-cards/{fake_id}")
    assert response.status_code == 404
