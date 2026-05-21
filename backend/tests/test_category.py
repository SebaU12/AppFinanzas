"""
Tests for Category API endpoints.
"""
import pytest
from fastapi import status


def test_seed_categories(client):
    """Test seeding categories"""
    response = client.post("/categories/seed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "created" in data
    assert "total" in data
    assert data["total"] == 47  # Total number of predefined categories


def test_seed_categories_idempotent(client):
    """Test that seeding multiple times doesn't create duplicates"""
    # First seed
    response1 = client.post("/categories/seed")
    assert response1.status_code == status.HTTP_200_OK

    # Second seed
    response2 = client.post("/categories/seed")
    assert response2.status_code == status.HTTP_200_OK
    data = response2.json()
    assert data["created"] == 0
    assert data["skipped"] == 47


def test_create_category(client):
    """Test creating a new category"""
    response = client.post(
        "/categories/",
        json={
            "name": "Test Category",
            "type": "expense",
            "is_personal": False,
            "allows_credit": True
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Category"
    assert data["type"] == "expense"
    assert data["is_personal"] is False
    assert data["allows_credit"] is True
    assert "id" in data


def test_create_category_duplicate_name(client):
    """Test creating a category with duplicate name"""
    client.post(
        "/categories/",
        json={"name": "Duplicate", "type": "expense"}
    )
    response = client.post(
        "/categories/",
        json={"name": "Duplicate", "type": "income"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_all_categories(client):
    """Test getting all categories"""
    # Seed first
    client.post("/categories/seed")

    response = client.get("/categories/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 47


def test_filter_categories_by_type(client):
    """Test filtering categories by type"""
    client.post("/categories/seed")

    # Filter income
    response = client.get("/categories/?type=income")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(cat["type"] == "income" for cat in data)
    assert len(data) == 6  # 6 income categories

    # Filter expense
    response = client.get("/categories/?type=expense")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(cat["type"] == "expense" for cat in data)


def test_filter_personal_categories(client):
    """Test filtering personal categories"""
    client.post("/categories/seed")

    response = client.get("/categories/?personal_only=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(cat["is_personal"] is True for cat in data)


def test_filter_credit_allowed_categories(client):
    """Test filtering categories that allow credit"""
    client.post("/categories/seed")

    response = client.get("/categories/?allows_credit_only=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(cat["allows_credit"] is True for cat in data)


def test_get_category_by_id(client):
    """Test getting a specific category"""
    # Create a category first
    create_response = client.post(
        "/categories/",
        json={"name": "Test Get", "type": "expense"}
    )
    category_id = create_response.json()["id"]

    response = client.get(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Get"


def test_get_nonexistent_category(client):
    """Test getting a non-existent category"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/categories/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_category(client):
    """Test updating a category"""
    create_response = client.post(
        "/categories/",
        json={"name": "Update Me", "type": "expense", "allows_credit": False}
    )
    category_id = create_response.json()["id"]

    response = client.put(
        f"/categories/{category_id}",
        json={"allows_credit": True}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["allows_credit"] is True
    assert data["name"] == "Update Me"


def test_delete_category(client):
    """Test deleting a category"""
    create_response = client.post(
        "/categories/",
        json={"name": "Delete Me", "type": "expense"}
    )
    category_id = create_response.json()["id"]

    response = client.delete(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/categories/{category_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_spanish_category_names(client):
    """Test that seeded categories have Spanish names"""
    client.post("/categories/seed")

    response = client.get("/categories/")
    data = response.json()

    # Check some Spanish category names
    spanish_names = [cat["name"] for cat in data]
    assert "Lu Sueldo" in spanish_names
    assert "Compras (supermercado)" in spanish_names
    assert "Gastos Lu" in spanish_names
    assert "Comida Goli" in spanish_names
