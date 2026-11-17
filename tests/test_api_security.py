import pytest
import jwt
from fastapi.testclient import TestClient
from src import api


@pytest.fixture
def client():
    test_client = TestClient(api.app)
    yield test_client
    api.app.dependency_overrides.clear()


def set_test_user(client, user):
    api.app.dependency_overrides[api.get_current_user] = lambda: user


def make_user(
    role="employee",
    tenant_id="college_a",
    department="CSE",
    clearance_level="public"
):
    return {
        "user_id": "test-user",
        "username": "test_user",
        "role": role,
        "tenant_id": tenant_id,
        "department": department,
        "clearance_level": clearance_level,
        "is_active": True
    }


def mock_retrieval(monkeypatch):
    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return {"mock": "retrieval"}

    def fake_rerank(query, results, top_k):
        return [{
            "content": "A computer network connects devices.",
            "metadata": {
                "source": "sample.pdf",
                "page_number": 3,
                "department": "CSE",
                "access_tier": "public"
            },
            "distance": 0.2,
            "rerank_score": 5.5
        }]

    monkeypatch.setattr(api, "search_rag_documents", fake_search)
    monkeypatch.setattr(api, "rerank_results", fake_rerank)

    return captured


def test_missing_authentication_is_rejected(client):
    response = client.post(
        "/query",
        json={"query": "What is a computer network?"}
    )
    assert response.status_code == 401


def test_invalid_token_is_rejected(client, monkeypatch):
    def reject_token(token):
        raise jwt.InvalidTokenError("Invalid token")

    monkeypatch.setattr(api, "decode_access_token", reject_token)

    response = client.post(
        "/query",
        json={"query": "What is a computer network?"},
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401


def test_public_employee_access_filter(client, monkeypatch):
    user = make_user(clearance_level="public")
    set_test_user(client, user)
    captured = mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "What is a computer network?"}
    )

    assert response.status_code == 200
    assert captured["allowed_access_tiers"] == ["public"]
    assert captured["tenant_id"] == "college_a"
    assert captured["department"] == "CSE"


def test_internal_employee_access_filter(client, monkeypatch):
    user = make_user(clearance_level="internal")
    set_test_user(client, user)
    captured = mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "Explain computer networks"}
    )

    assert response.status_code == 200
    assert captured["allowed_access_tiers"] == [
        "public", "internal"
    ]


def test_confidential_admin_access_filter(client, monkeypatch):
    user = make_user(
        role="admin",
        department=None,
        clearance_level="confidential"
    )
    set_test_user(client, user)
    captured = mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "Explain computer networks"}
    )

    assert response.status_code == 200
    assert captured["allowed_access_tiers"] == [
        "public", "internal", "confidential"
    ]
    assert captured["department"] is None


def test_tenant_id_is_passed_to_retrieval(client, monkeypatch):
    user = make_user(
        tenant_id="college_b",
        clearance_level="confidential"
    )
    set_test_user(client, user)
    captured = mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "What is DBMS?"}
    )

    assert response.status_code == 200
    assert captured["tenant_id"] == "college_b"


def test_employee_department_is_enforced(client, monkeypatch):
    user = make_user(department="CSE")
    set_test_user(client, user)
    captured = mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "Explain machine learning"}
    )

    assert response.status_code == 200
    assert captured["department"] == "CSE"


def test_citations_contain_source_and_page(client, monkeypatch):
    user = make_user()
    set_test_user(client, user)
    mock_retrieval(monkeypatch)

    response = client.post(
        "/query",
        json={"query": "What is a computer network?"}
    )

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert result["source"] == "sample.pdf"
    assert result["page_number"] == 3
    assert result["content"]
    assert "rerank_score" in result
