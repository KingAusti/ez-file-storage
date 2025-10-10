import pytest
from fastapi.testclient import TestClient


def test_create_data_entry(client, auth_headers):
    """Test creating a data entry"""
    response = client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Entry"
    assert data["content"] == "This is a test data entry"
    assert "id" in data
    assert "created_at" in data


def test_create_data_entry_unauthorized(client):
    """Test creating data entry without authentication"""
    response = client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        }
    )
    assert response.status_code == 401


def test_get_data_entries(client, auth_headers):
    """Test getting all data entries"""
    # First create a data entry
    client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        },
        headers=auth_headers
    )
    
    # Then get all entries
    response = client.get("/data-entries/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Entry"


def test_get_data_entry(client, auth_headers):
    """Test getting a specific data entry"""
    # First create a data entry
    create_response = client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        },
        headers=auth_headers
    )
    entry_id = create_response.json()["id"]
    
    # Then get the specific entry
    response = client.get(f"/data-entries/{entry_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Entry"
    assert data["content"] == "This is a test data entry"


def test_get_nonexistent_data_entry(client, auth_headers):
    """Test getting a non-existent data entry"""
    response = client.get("/data-entries/999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_data_entry(client, auth_headers):
    """Test updating a data entry"""
    # First create a data entry
    create_response = client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        },
        headers=auth_headers
    )
    entry_id = create_response.json()["id"]
    
    # Then update it
    response = client.put(
        f"/data-entries/{entry_id}",
        json={
            "title": "Updated Entry",
            "content": "This is an updated data entry"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Entry"
    assert data["content"] == "This is an updated data entry"


def test_delete_data_entry(client, auth_headers):
    """Test deleting a data entry"""
    # First create a data entry
    create_response = client.post(
        "/data-entries/",
        json={
            "title": "Test Entry",
            "content": "This is a test data entry"
        },
        headers=auth_headers
    )
    entry_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/data-entries/{entry_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify it's deleted
    get_response = client.get(f"/data-entries/{entry_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_data_entry_isolation(client, test_user, db_session):
    """Test that users can only see their own data entries"""
    from app.models.user import User
    from app.models.data_entry import DataEntry
    from app.core.security import get_password_hash
    
    # Create another user
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    
    # Create data entry for other user
    other_entry = DataEntry(
        title="Other User's Entry",
        content="This belongs to another user",
        owner_id=other_user.id
    )
    db_session.add(other_entry)
    db_session.commit()
    
    # Login as test user
    login_response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    
    # Try to access other user's entry
    response = client.get(f"/data-entries/{other_entry.id}", headers=auth_headers)
    assert response.status_code == 404
