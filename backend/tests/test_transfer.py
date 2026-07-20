"""
Tests for Transfer API endpoints.
"""
import pytest
from fastapi import status


@pytest.fixture
def sample_participant(client):
    response = client.post(
        "/participants/",
        json={"name": "Test Person", "default_percentage": 50.0}
    )
    return response.json()


@pytest.fixture
def sample_debit_card(client, sample_participant):
    response = client.post(
        "/debit-cards/",
        json={
            "name": "Cuenta debito",
            "participant_id": sample_participant["id"],
            "initial_balance": 1000.00,
            "currency": "PEN"
        }
    )
    return response.json()


@pytest.fixture
def second_debit_card(client, sample_participant):
    response = client.post(
        "/debit-cards/",
        json={
            "name": "Cuenta destino",
            "participant_id": sample_participant["id"],
            "initial_balance": 500.00,
            "currency": "PEN"
        }
    )
    return response.json()


@pytest.fixture
def sample_savings_card(client, sample_participant):
    response = client.post(
        "/savings-cards/",
        json={
            "name": "Ahorros BCP",
            "participant_id": sample_participant["id"],
            "currency": "PEN"
        }
    )
    return response.json()


def test_create_cash_to_savings_transfer(client, sample_savings_card):
    response = client.post(
        "/transfers/",
        json={
            "date": "2026-07-20",
            "amount": 150.00,
            "currency": "PEN",
            "from_type": "cash",
            "to_type": "savings",
            "to_savings_card_id": sample_savings_card["id"],
            "description": "Guardar efectivo"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["from_type"] == "cash"
    assert data["to_type"] == "savings"
    assert data["to_savings_card_id"] == sample_savings_card["id"]
    assert data["to_account_name"].startswith("Ahorros BCP")


def test_create_savings_to_debit_transfer(client, sample_debit_card, sample_savings_card):
    response = client.post(
        "/transfers/",
        json={
            "date": "2026-07-20",
            "amount": 80.00,
            "currency": "PEN",
            "from_type": "savings",
            "from_savings_card_id": sample_savings_card["id"],
            "to_type": "debit",
            "to_debit_card_id": sample_debit_card["id"],
            "description": "Mover a debito"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["from_type"] == "savings"
    assert data["from_savings_card_id"] == sample_savings_card["id"]
    assert data["to_debit_card_id"] == sample_debit_card["id"]
    assert data["from_account_name"].startswith("Ahorros BCP")


def test_reject_transfer_same_savings_account(client, sample_savings_card):
    response = client.post(
        "/transfers/",
        json={
            "date": "2026-07-20",
            "amount": 20.00,
            "currency": "PEN",
            "from_type": "savings",
            "from_savings_card_id": sample_savings_card["id"],
            "to_type": "savings",
            "to_savings_card_id": sample_savings_card["id"]
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be the same" in response.json()["detail"].lower()


def test_delete_savings_card_with_transfer_fails(client, sample_debit_card, sample_savings_card):
    transfer_response = client.post(
        "/transfers/",
        json={
            "date": "2026-07-20",
            "amount": 40.00,
            "currency": "PEN",
            "from_type": "savings",
            "from_savings_card_id": sample_savings_card["id"],
            "to_type": "debit",
            "to_debit_card_id": sample_debit_card["id"]
        }
    )
    assert transfer_response.status_code == status.HTTP_201_CREATED

    delete_response = client.delete(f"/savings-cards/{sample_savings_card['id']}")

    assert delete_response.status_code == status.HTTP_409_CONFLICT
    assert "associated transfer" in delete_response.json()["detail"]


def test_debit_balance_includes_savings_transfers(client, sample_debit_card, second_debit_card, sample_savings_card):
    inbound = client.post(
        "/transfers/",
        json={
            "date": "2026-07-20",
            "amount": 120.00,
            "currency": "PEN",
            "from_type": "savings",
            "from_savings_card_id": sample_savings_card["id"],
            "to_type": "debit",
            "to_debit_card_id": sample_debit_card["id"]
        }
    )
    outbound = client.post(
        "/transfers/",
        json={
            "date": "2026-07-21",
            "amount": 70.00,
            "currency": "PEN",
            "from_type": "debit",
            "from_debit_card_id": sample_debit_card["id"],
            "to_type": "debit",
            "to_debit_card_id": second_debit_card["id"]
        }
    )

    assert inbound.status_code == status.HTTP_201_CREATED
    assert outbound.status_code == status.HTTP_201_CREATED

    balance_response = client.get(f"/debit-cards/{sample_debit_card['id']}/balance")

    assert balance_response.status_code == status.HTTP_200_OK
    assert balance_response.json()["current_balance"] == 1050.0
