import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer demo_token"}

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI SDR API is running"}

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_create_campaign(client, auth_headers):
    campaign_data = {
        "name": "Test Campaign",
        "description": "Test Description",
        "target_audience": "Test Audience",
        "value_proposition": "Test Value Prop",
        "call_to_action": "Test CTA"
    }
    
    response = client.post("/campaigns", json=campaign_data, headers=auth_headers)
    assert response.status_code == 200
    
    campaign = response.json()
    assert campaign["name"] == campaign_data["name"]
    assert campaign["description"] == campaign_data["description"]
    assert "id" in campaign

def test_get_campaigns(client, auth_headers):
    response = client.get("/campaigns", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_lead(client, auth_headers):
    # First create a campaign
    campaign_data = {
        "name": "Test Campaign for Lead",
        "description": "Test Description",
        "target_audience": "Test Audience",
        "value_proposition": "Test Value Prop",
        "call_to_action": "Test CTA"
    }
    
    campaign_response = client.post("/campaigns", json=campaign_data, headers=auth_headers)
    campaign_id = campaign_response.json()["id"]
    
    # Create a lead
    lead_data = {
        "name": "John Doe",
        "company": "Test Company",
        "title": "Test Title",
        "email": "john@test.com"
    }
    
    response = client.post(f"/campaigns/{campaign_id}/leads", json=lead_data, headers=auth_headers)
    assert response.status_code == 200
    
    lead = response.json()
    assert lead["name"] == lead_data["name"]
    assert lead["company"] == lead_data["company"]
    assert lead["campaign_id"] == campaign_id

def test_get_campaign_leads(client, auth_headers):
    # Create campaign and lead first
    campaign_data = {
        "name": "Test Campaign for Leads",
        "description": "Test Description",
        "target_audience": "Test Audience",
        "value_proposition": "Test Value Prop",
        "call_to_action": "Test CTA"
    }
    
    campaign_response = client.post("/campaigns", json=campaign_data, headers=auth_headers)
    campaign_id = campaign_response.json()["id"]
    
    lead_data = {
        "name": "Jane Doe",
        "company": "Test Company",
        "title": "Test Title"
    }
    
    client.post(f"/campaigns/{campaign_id}/leads", json=lead_data, headers=auth_headers)
    
    # Get leads
    response = client.get(f"/campaigns/{campaign_id}/leads", headers=auth_headers)
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) >= 1
    assert leads[0]["name"] == lead_data["name"]

def test_campaign_execution(client, auth_headers):
    # Create campaign with leads
    campaign_data = {
        "name": "Test Execution Campaign",
        "description": "Test Description",
        "target_audience": "Test Audience",
        "value_proposition": "Test Value Prop",
        "call_to_action": "Test CTA"
    }
    
    campaign_response = client.post("/campaigns", json=campaign_data, headers=auth_headers)
    campaign_id = campaign_response.json()["id"]
    
    # Add a lead
    lead_data = {
        "name": "Test Lead",
        "company": "Test Company",
        "title": "Test Title"
    }
    
    client.post(f"/campaigns/{campaign_id}/leads", json=lead_data, headers=auth_headers)
    
    # Execute campaign
    response = client.post(f"/campaigns/{campaign_id}/execute", headers=auth_headers)
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "task_id" in result

def test_campaign_stats(client, auth_headers):
    # Create campaign
    campaign_data = {
        "name": "Test Stats Campaign",
        "description": "Test Description",
        "target_audience": "Test Audience",
        "value_proposition": "Test Value Prop",
        "call_to_action": "Test CTA"
    }
    
    campaign_response = client.post("/campaigns", json=campaign_data, headers=auth_headers)
    campaign_id = campaign_response.json()["id"]
    
    # Get stats
    response = client.get(f"/campaigns/{campaign_id}/stats", headers=auth_headers)
    assert response.status_code == 200
    
    stats = response.json()
    assert "campaign_id" in stats
    assert "total_leads" in stats
    assert "successful_outreach" in stats
    assert "response_rate" in stats

def test_unauthorized_access(client):
    response = client.get("/campaigns")
    assert response.status_code == 401

def test_invalid_campaign_id(client, auth_headers):
    response = client.get("/campaigns/invalid-id", headers=auth_headers)
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__])
