import pytest
from fastapi.testclient import TestClient

from src.api import app, get_current_user
from src import field_agent as agent
from src.agent_llm import plan_with_llm


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user",
        "username": "test-user",
        "role": "admin",
        "tenant_id": "college_a",
    }

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_current_user, None)


def test_inventory_lookup_executes(client):
    response = client.post("/agent/run", json={
        "instruction": "Check the available quantity of LAPTOP-001"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["tool"] == "inventory_lookup"
    assert data["result"]["sku"] == "LAPTOP-001"
    assert data["result"]["quantity"] == 24
    assert any(c["stage"] == "observation" for c in data["cycles"])


def test_lead_update_requires_approval(client):
    # Reset persistent mock CRM state so this test is repeatable.
    agent.erp_client.update_lead_status("LEAD-1001", "new")
    before = agent.erp_client.get_lead("LEAD-1001")
    assert before["status"] == "new"

    response = client.post("/agent/run", json={
        "instruction": "Update lead LEAD-1001 to qualified"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "pending_approval"
    assert data["tool"] == "update_lead_status"

    # The CRM must remain unchanged before approval.
    assert agent.erp_client.get_lead("LEAD-1001")["status"] == "new"

    approval = client.post(
        f"/agent/approve/{data['approval_id']}",
        json={"approved": True},
    )

    assert approval.status_code == 200
    assert approval.json()["status"] == "completed"
    assert agent.erp_client.get_lead("LEAD-1001")["status"] == "qualified"


def test_ticket_creation_requires_approval(client):
    before = len(agent.erp_client.list_tickets()["tickets"])

    response = client.post("/agent/run", json={
        "instruction": "Create a high priority support ticket for printer issue"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "pending_approval"
    assert data["tool"] == "create_support_ticket"
    assert len(agent.erp_client.list_tickets()["tickets"]) == before

    approval = client.post(
        f"/agent/approve/{data['approval_id']}",
        json={"approved": True},
    )

    assert approval.status_code == 200
    assert approval.json()["status"] == "completed"

    tickets = agent.erp_client.list_tickets()["tickets"]
    assert len(tickets) == before + 1
    assert tickets[-1]["priority"] == "high"


def test_rejected_ticket_is_not_created(client):
    before = len(agent.erp_client.list_tickets()["tickets"])

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
    assert len(agent.erp_client.list_tickets()["tickets"]) == before


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


def test_another_user_cannot_approve(client):
    response = client.post("/agent/run", json={
        "instruction": "Update lead LEAD-1001 to proposal"
    })

    approval_id = response.json()["approval_id"]

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "different-user",
        "username": "different-user",
        "role": "admin",
        "tenant_id": "college_a",
    }

    unauthorized = client.post(
        f"/agent/approve/{approval_id}",
        json={"approved": True},
    )

    assert unauthorized.status_code == 404

    # Original owner can still approve it.
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user",
        "username": "test-user",
        "role": "admin",
        "tenant_id": "college_a",
    }

    approved = client.post(
        f"/agent/approve/{approval_id}",
        json={"approved": True},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "completed"


def test_audit_log_is_persisted_and_scoped(client):
    response = client.post("/agent/run", json={
        "instruction": "Check the available quantity of LAPTOP-001"
    })

    assert response.status_code == 200

    audit = client.get("/agent/audit")

    assert audit.status_code == 200
    assert audit.json()["count"] >= 1
    assert any(
        event["event"] == "tool_executed"
        for event in audit.json()["events"]
    )


def test_agent_lists_available_tools(client):
    response = client.get("/agent/tools")

    assert response.status_code == 200

    tools = response.json()["tools"]
    assert len(tools) == 3

    write_tools = [
        tool for tool in tools
        if tool["type"] == "write"
    ]

    assert all(tool["requires_approval"] for tool in write_tools)
