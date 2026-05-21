"""
Tests for Participant API endpoints.
"""
import pytest
from fastapi import status


def test_create_participant(client):
    """Test creating a new participant"""
    response = client.post(
        "/participants/",
        json={
            "name": "Lu",
            "active": True,
            "default_percentage": 60.0
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Lu"
    assert data["active"] is True
    assert data["default_percentage"] == 60.0
    assert "id" in data


def test_create_participant_duplicate_name(client):
    """Test creating a participant with duplicate name"""
    client.post(
        "/participants/",
        json={"name": "Lu", "active": True, "default_percentage": 60.0}
    )
    response = client.post(
        "/participants/",
        json={"name": "Lu", "active": True, "default_percentage": 40.0}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_all_participants(client):
    """Test getting all participants"""
    # Create test participants
    client.post("/participants/", json={"name": "Lu", "default_percentage": 60.0})
    client.post("/participants/", json={"name": "Chebos", "default_percentage": 40.0})

    response = client.get("/participants/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_get_participant_by_id(client):
    """Test getting a specific participant"""
    create_response = client.post(
        "/participants/",
        json={"name": "Lu", "default_percentage": 60.0}
    )
    participant_id = create_response.json()["id"]

    response = client.get(f"/participants/{participant_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Lu"


def test_get_nonexistent_participant(client):
    """Test getting a non-existent participant"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/participants/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_participant(client):
    """Test updating a participant"""
    create_response = client.post(
        "/participants/",
        json={"name": "Lu", "default_percentage": 60.0}
    )
    participant_id = create_response.json()["id"]

    response = client.put(
        f"/participants/{participant_id}",
        json={"default_percentage": 70.0}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["default_percentage"] == 70.0
    assert data["name"] == "Lu"


def test_delete_participant(client):
    """Test deleting a participant"""
    create_response = client.post(
        "/participants/",
        json={"name": "Lu", "default_percentage": 60.0}
    )
    participant_id = create_response.json()["id"]

    response = client.delete(f"/participants/{participant_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/participants/{participant_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_filter_active_participants(client):
    """Test filtering only active participants"""
    client.post("/participants/", json={"name": "Lu", "active": True, "default_percentage": 60.0})
    client.post("/participants/", json={"name": "Chebos", "active": False, "default_percentage": 40.0})

    response = client.get("/participants/?active_only=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Lu"


def test_invalid_percentage(client):
    """Test creating participant with invalid percentage"""
    response = client.post(
        "/participants/",
        json={"name": "Invalid", "default_percentage": 150.0}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
