"""
Tests for tags functionality
"""
import pytest
from fastapi.testclient import TestClient


def test_create_tag(client, auth_headers):
    """Test creating a new tag"""
    tag_data = {
        "name": "Important",
        "color": "#ff0000",
        "description": "Important items"
    }
    
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 200
    
    tag = response.json()
    assert tag["name"] == "Important"
    assert tag["color"] == "#ff0000"
    assert tag["description"] == "Important items"
    assert "id" in tag


def test_get_tags(client, auth_headers):
    """Test getting all tags"""
    # Create a tag first
    tag_data = {"name": "Test Tag", "color": "#00ff00"}
    client.post("/tags/", json=tag_data, headers=auth_headers)
    
    response = client.get("/tags/", headers=auth_headers)
    assert response.status_code == 200
    
    tags = response.json()
    assert len(tags) >= 1
    assert any(tag["name"] == "Test Tag" for tag in tags)


def test_create_data_entry_with_tags(client, auth_headers):
    """Test creating a data entry with tags"""
    # Create a tag first
    tag_data = {"name": "Work", "color": "#0000ff"}
    tag_response = client.post("/tags/", json=tag_data, headers=auth_headers)
    tag_id = tag_response.json()["id"]
    
    # Create data entry with tag
    entry_data = {
        "title": "Test Entry",
        "content": "This is a test entry",
        "tag_ids": [tag_id]
    }
    
    response = client.post("/data-entries/", json=entry_data, headers=auth_headers)
    assert response.status_code == 200
    
    entry = response.json()
    assert entry["title"] == "Test Entry"
    assert len(entry["tags"]) == 1
    assert entry["tags"][0]["name"] == "Work"


def test_search_data_entries(client, auth_headers):
    """Test searching data entries"""
    # Create a data entry first
    entry_data = {
        "title": "Important Meeting",
        "content": "Discuss project timeline"
    }
    client.post("/data-entries/", json=entry_data, headers=auth_headers)
    
    # Search for entries
    response = client.get("/data-entries/?search=meeting", headers=auth_headers)
    assert response.status_code == 200
    
    entries = response.json()
    assert len(entries) >= 1
    assert any("meeting" in entry["title"].lower() for entry in entries)


def test_version_endpoint(client):
    """Test version endpoint"""
    response = client.get("/version")
    assert response.status_code == 200
    
    version_info = response.json()
    assert "version" in version_info
    assert "api_version" in version_info
    assert "features" in version_info
    assert version_info["version"] == "1.1.0"
