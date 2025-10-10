import pytest
from fastapi.testclient import TestClient


def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_weak_password(client):
    """Test registration with weak password"""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak"
        }
    )
    assert response.status_code == 400
    assert "Password does not meet requirements" in response.json()["detail"]


def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "NewPassword123!"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_refresh_token(client, test_user):
    """Test token refresh"""
    # First login to get tokens
    login_response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(client, auth_headers):
    """Test user logout"""
    response = client.post("/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


def test_forgot_password(client, test_user):
    """Test password reset request"""
    response = client.post(
        "/auth/forgot-password",
        data={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert "password reset link has been sent" in response.json()["message"]


def test_forgot_password_nonexistent_email(client):
    """Test password reset with non-existent email"""
    response = client.post(
        "/auth/forgot-password",
        data={"email": "nonexistent@example.com"}
    )
    # Should still return success to prevent email enumeration
    assert response.status_code == 200
