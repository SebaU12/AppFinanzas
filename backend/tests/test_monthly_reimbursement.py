"""
Tests for MonthlyReimbursement API endpoints.
"""
import pytest
from uuid import uuid4


def test_calculate_reimbursement_basic(client, test_db):
    """Test basic reimbursement calculation with two participants."""
    # Create participants with 50/50 split
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    # Create shared category
    category = client.post("/categories/", json={
        "name": "Compras",
        "type": "EXPENSE"
    }).json()

    # Lu pays 300, Seba pays 100 (total 400, each should pay 200)
    client.post("/transactions/", json={
        "description": "Lu's purchase",
        "amount": 300.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Seba's purchase",
        "amount": 100.00,
        "date": "2024-02-20",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    # Calculate reimbursement
    response = client.post("/reimbursements/calculate/2024-02")
    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2024-02"
    assert float(data["total_shared_expenses"]) == 400.00
    assert len(data["details"]) == 2

    # Find each participant's detail
    lu_detail = next(d for d in data["details"] if d["participant_id"] == lu["id"])
    seba_detail = next(d for d in data["details"] if d["participant_id"] == seba["id"])

    # Lu paid 300, expected 200, balance +100 (owed to Lu)
    assert float(lu_detail["amount_paid"]) == 300.00
    assert float(lu_detail["expected_share"]) == 200.00
    assert float(lu_detail["balance"]) == 100.00

    # Seba paid 100, expected 200, balance -100 (Seba owes)
    assert float(seba_detail["amount_paid"]) == 100.00
    assert float(seba_detail["expected_share"]) == 200.00
    assert float(seba_detail["balance"]) == -100.00


def test_calculate_reimbursement_excludes_personal(client, test_db):
    """Test that personal categories are excluded from reimbursement."""
    # Create participants
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    # Create shared and personal categories
    shared_cat = client.post("/categories/", json={
        "name": "Shared Expense",
        "type": "EXPENSE",
        "is_personal": False
    }).json()

    personal_cat = client.post("/categories/", json={
        "name": "Personal Expense",
        "type": "EXPENSE",
        "is_personal": True
    }).json()

    # Shared transaction
    client.post("/transactions/", json={
        "description": "Shared",
        "amount": 200.00,
        "date": "2024-02-15",
        "category_id": shared_cat["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    # Personal transaction (should be excluded)
    client.post("/transactions/", json={
        "description": "Personal",
        "amount": 500.00,
        "date": "2024-02-20",
        "category_id": personal_cat["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    # Calculate reimbursement
    response = client.post("/reimbursements/calculate/2024-02")
    assert response.status_code == 200
    data = response.json()

    # Only shared expense (200) should be counted
    assert float(data["total_shared_expenses"]) == 200.00


def test_calculate_reimbursement_unequal_percentages(client, test_db):
    """Test reimbursement with unequal percentage splits."""
    # Lu pays 60%, Seba pays 40%
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 60.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 40.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Total 1000: Lu should pay 600, Seba should pay 400
    # But Lu pays 500, Seba pays 500
    client.post("/transactions/", json={
        "description": "Lu's",
        "amount": 500.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Seba's",
        "amount": 500.00,
        "date": "2024-02-20",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    response = client.post("/reimbursements/calculate/2024-02")
    assert response.status_code == 200
    data = response.json()

    lu_detail = next(d for d in data["details"] if d["participant_id"] == lu["id"])
    seba_detail = next(d for d in data["details"] if d["participant_id"] == seba["id"])

    # Lu paid 500, expected 600, balance -100 (Lu owes)
    assert float(lu_detail["expected_share"]) == 600.00
    assert float(lu_detail["balance"]) == -100.00

    # Seba paid 500, expected 400, balance +100 (owed to Seba)
    assert float(seba_detail["expected_share"]) == 400.00
    assert float(seba_detail["balance"]) == 100.00


def test_recalculate_reimbursement(client, test_db):
    """Test recalculating an existing reimbursement."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Initial transaction
    client.post("/transactions/", json={
        "description": "First",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    # Calculate
    response1 = client.post("/reimbursements/calculate/2024-02")
    assert float(response1.json()["total_shared_expenses"]) == 100.00

    # Add another transaction
    client.post("/transactions/", json={
        "description": "Second",
        "amount": 200.00,
        "date": "2024-02-20",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    # Recalculate
    response2 = client.post("/reimbursements/calculate/2024-02")
    assert response2.status_code == 200
    assert float(response2.json()["total_shared_expenses"]) == 300.00


def test_cannot_recalculate_finalized(client, test_db):
    """Test that finalized reimbursements cannot be recalculated."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    # Calculate and finalize
    client.post("/reimbursements/calculate/2024-02")
    client.post("/reimbursements/finalize/2024-02")

    # Try to recalculate
    response = client.post("/reimbursements/calculate/2024-02")
    assert response.status_code == 400
    assert "finalized" in response.json()["detail"].lower()


def test_get_all_reimbursements(client, test_db):
    """Test retrieving all reimbursements."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Create transactions in two months
    client.post("/transactions/", json={
        "description": "Feb",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Mar",
        "amount": 200.00,
        "date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    # Calculate both
    client.post("/reimbursements/calculate/2024-02")
    client.post("/reimbursements/calculate/2024-03")

    # Get all
    response = client.get("/reimbursements/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_filter_reimbursements_by_finalized(client, test_db):
    """Test filtering reimbursements by finalized status."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Create two months
    client.post("/transactions/", json={
        "description": "Feb",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Mar",
        "amount": 200.00,
        "date": "2024-03-15",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")
    client.post("/reimbursements/calculate/2024-03")

    # Finalize Feb
    client.post("/reimbursements/finalize/2024-02")

    # Get finalized
    response = client.get("/reimbursements/?finalized=true")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Get not finalized
    response = client.get("/reimbursements/?finalized=false")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_reimbursement_by_month(client, test_db):
    """Test getting reimbursement for specific month."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")

    response = client.get("/reimbursements/month/2024-02")
    assert response.status_code == 200
    assert response.json()["month"] == "2024-02"


def test_get_reimbursement_not_found(client, test_db):
    """Test getting non-existent reimbursement."""
    response = client.get("/reimbursements/month/2024-02")
    assert response.status_code == 404


def test_finalize_reimbursement(client, test_db):
    """Test finalizing a reimbursement."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")

    response = client.post("/reimbursements/finalize/2024-02")
    assert response.status_code == 200
    data = response.json()
    assert data["finalized"] is True
    assert data["finalized_date"] is not None


def test_get_balance_summary(client, test_db):
    """Test getting balance summary with settlements."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    # Lu pays 300, Seba pays 100 (total 400, each should pay 200)
    # Lu is owed 100, Seba owes 100
    client.post("/transactions/", json={
        "description": "Lu's",
        "amount": 300.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/transactions/", json={
        "description": "Seba's",
        "amount": 100.00,
        "date": "2024-02-20",
        "category_id": category["id"],
        "participant_id": seba["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")

    response = client.get("/reimbursements/balance/2024-02")
    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2024-02"
    assert data["total_shared_expenses"] == 400.00
    assert len(data["settlements"]) == 1

    settlement = data["settlements"][0]
    assert settlement["from"] == "Seba"
    assert settlement["to"] == "Lu"
    assert settlement["amount"] == 100.00


def test_delete_reimbursement(client, test_db):
    """Test deleting a reimbursement."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")

    response = client.delete("/reimbursements/month/2024-02")
    assert response.status_code == 204

    # Verify deleted
    get_response = client.get("/reimbursements/month/2024-02")
    assert get_response.status_code == 404


def test_cannot_delete_finalized(client, test_db):
    """Test that finalized reimbursements cannot be deleted."""
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 50.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 50.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    client.post("/reimbursements/calculate/2024-02")
    client.post("/reimbursements/finalize/2024-02")

    response = client.delete("/reimbursements/month/2024-02")
    assert response.status_code == 400
    assert "finalized" in response.json()["detail"].lower()


def test_invalid_percentages_sum(client, test_db):
    """Test that calculation fails if percentages don't sum to 100."""
    # Create participants with percentages that don't sum to 100
    lu = client.post("/participants/", json={
        "name": "Lu",
        "default_percentage": 60.0
    }).json()
    seba = client.post("/participants/", json={
        "name": "Seba",
        "default_percentage": 30.0
    }).json()

    category = client.post("/categories/", json={
        "name": "Test",
        "type": "EXPENSE"
    }).json()

    client.post("/transactions/", json={
        "description": "Test",
        "amount": 100.00,
        "date": "2024-02-15",
        "category_id": category["id"],
        "participant_id": lu["id"],
        "payment_method": "CASH"
    })

    response = client.post("/reimbursements/calculate/2024-02")
    assert response.status_code == 400
    assert "100" in response.json()["detail"]
