"""
Tests for MonthlyBudget API endpoints.
"""
import pytest
from fastapi import status


@pytest.fixture
def sample_category(client):
    """Create a sample category for testing"""
    response = client.post(
        "/categories/",
        json={"name": "Test Budget Category", "type": "expense"}
    )
    return response.json()


def test_create_monthly_budget(client, sample_category):
    """Test creating a new monthly budget"""
    response = client.post(
        "/budgets/",
        json={
            "month": "2026-01",
            "category_id": sample_category["id"],
            "budgeted_amount": 1000.50
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["month"] == "2026-01"
    assert data["category_id"] == sample_category["id"]
    assert float(data["budgeted_amount"]) == 1000.50
    assert "id" in data


def test_create_monthly_budget_duplicate(client, sample_category):
    """Test creating duplicate budget for same month and category"""
    # Create first budget
    client.post(
        "/budgets/",
        json={
            "month": "2026-01",
            "category_id": sample_category["id"],
            "budgeted_amount": 1000.00
        }
    )

    # Try to create duplicate
    response = client.post(
        "/budgets/",
        json={
            "month": "2026-01",
            "category_id": sample_category["id"],
            "budgeted_amount": 1500.00
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_budget_invalid_month_format(client, sample_category):
    """Test creating budget with invalid month format"""
    response = client.post(
        "/budgets/",
        json={
            "month": "2026/01",  # Wrong format
            "category_id": sample_category["id"],
            "budgeted_amount": 1000.00
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_budget_invalid_month_value(client, sample_category):
    """Test creating budget with invalid month value"""
    response = client.post(
        "/budgets/",
        json={
            "month": "2026-13",  # Invalid month
            "category_id": sample_category["id"],
            "budgeted_amount": 1000.00
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_budget_negative_amount(client, sample_category):
    """Test creating budget with negative amount"""
    response = client.post(
        "/budgets/",
        json={
            "month": "2026-01",
            "category_id": sample_category["id"],
            "budgeted_amount": -100.00
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_budget_nonexistent_category(client):
    """Test creating budget with non-existent category"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        "/budgets/",
        json={
            "month": "2026-01",
            "category_id": fake_id,
            "budgeted_amount": 1000.00
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_budgets(client, sample_category):
    """Test getting all budgets"""
    # Create test budgets
    client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    client.post(
        "/budgets/",
        json={"month": "2026-02", "category_id": sample_category["id"], "budgeted_amount": 1500.00}
    )

    response = client.get("/budgets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_filter_budgets_by_month(client, sample_category):
    """Test filtering budgets by month"""
    client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    client.post(
        "/budgets/",
        json={"month": "2026-02", "category_id": sample_category["id"], "budgeted_amount": 1500.00}
    )

    response = client.get("/budgets/?month=2026-01")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["month"] == "2026-01"


def test_filter_budgets_by_category(client, sample_category):
    """Test filtering budgets by category"""
    # Create another category
    category2 = client.post(
        "/categories/",
        json={"name": "Another Category", "type": "expense"}
    ).json()

    client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": category2["id"], "budgeted_amount": 2000.00}
    )

    response = client.get(f"/budgets/?category_id={sample_category['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["category_id"] == sample_category["id"]


def test_get_budget_by_id(client, sample_category):
    """Test getting a specific budget"""
    create_response = client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    budget_id = create_response.json()["id"]

    response = client.get(f"/budgets/{budget_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["month"] == "2026-01"


def test_get_nonexistent_budget(client):
    """Test getting a non-existent budget"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/budgets/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_budget(client, sample_category):
    """Test updating a budget"""
    create_response = client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    budget_id = create_response.json()["id"]

    response = client.put(
        f"/budgets/{budget_id}",
        json={"budgeted_amount": 1500.00}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert float(data["budgeted_amount"]) == 1500.00


def test_delete_budget(client, sample_category):
    """Test deleting a budget"""
    create_response = client.post(
        "/budgets/",
        json={"month": "2026-01", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    budget_id = create_response.json()["id"]

    response = client.delete(f"/budgets/{budget_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/budgets/{budget_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_monthly_summary(client, sample_category):
    """Test getting monthly summary"""
    # Create another category
    category2 = client.post(
        "/categories/",
        json={"name": "Summary Category", "type": "expense"}
    ).json()

    # Create budgets for the same month
    client.post(
        "/budgets/",
        json={"month": "2026-03", "category_id": sample_category["id"], "budgeted_amount": 1000.00}
    )
    client.post(
        "/budgets/",
        json={"month": "2026-03", "category_id": category2["id"], "budgeted_amount": 2000.00}
    )

    response = client.get("/budgets/summary/2026-03")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["month"] == "2026-03"
    assert data["total_budgeted"] == 3000.00
    assert data["category_count"] == 2
    assert len(data["budgets"]) == 2
