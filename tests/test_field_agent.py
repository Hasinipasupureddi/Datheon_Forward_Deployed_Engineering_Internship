import pytest
from fastapi.testclient import TestClient

from src.api import app, get_current_user
from src import field_agent as agent


@pytest.fixture
def client():
    original_leads = {k: v.copy() for k, v in agent.LEADS.items()}
    original_tickets = list(agent.TICKETS)
    original_pending = dict(agent.PENDING)
    original_audit = list(agent.AUDIT_LOG)

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user",
        "username": "test-user",
        "role": "admin",
        "tenant_id": "college_a",
    }

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_current_user, None)
    agent.LEADS.clear()
    agent.LEADS.update(original_leads)
    agent.TICKETS.clear()
    agent.TICKETS.extend(original_tickets)
    agent.PENDING.clear()
    agent.PENDING.update(original_pending)
    agent.AUDIT_LOG.clear()
    agent.AUDIT_LOG.extend(original_audit)


def test_inventory_lookup_executes(client):
    response = client.post("/agent/run", json={
        "instruction": "Check inventory stock for LAPTOP-001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["quantity"] == 24
    assert any(c["stage"] == "observation" for c in data["cycles"])


def test_lead_update_requires_approval(client):
    response = client.post("/agent/run", json={
        "instruction": "Update lead LEAD-1001 to qualified"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_approval"
    assert agent.LEADS["LEAD-1001"]["status"] == "new"

    approval = client.post(
        f"/agent/approve/{data['approval_id']}",
        json={"approved": True},
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "completed"
    assert agent.LEADS["LEAD-1001"]["status"] == "qualified"


def test_ticket_creation_requires_approval(client):
    response = client.post("/agent/run", json={
        "instruction": "Create a high priority support ticket for printer issue"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_approval"
    assert len(agent.TICKETS) == 0

    approval = client.post(
        f"/agent/approve/{data['approval_id']}",
        json={"approved": True},
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "completed"
    assert len(agent.TICKETS) == 1
    assert agent.TICKETS[0]["priority"] == "high"


def test_rejected_ticket_is_not_created(client):
    response = client.post("/agent/run", json={
        "instruction": "Create a support ticket for network issue"
    })
    approval_id = response.json()["approval_id"]

    rejected = client.post(
        f"/agent/approve/{approval_id}",
        json={"approved": False},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert len(agent.TICKETS) == 0


def test_approval_id_cannot_be_reused(client):
    response = client.post("/agent/run", json={
        "instruction": "Update lead LEAD-1001 to contacted"
    })
    approval_id = response.json()["approval_id"]

    first = client.post(
        f"/agent/approve/{approval_id}",
        json={"approved": True},
    )
    second = client.post(
        f"/agent/approve/{approval_id}",
        json={"approved": True},
    )

    assert first.status_code == 200
    assert second.status_code == 404
