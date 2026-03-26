from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str, password: str) -> str:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    return login_response.json()["data"]["token"]["access_token"]


def _create_document(client: TestClient, token: str) -> int:
    response = client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": "test.txt",
            "content_type": "text/plain",
            "storage_path": "/uploads/test.txt",
            "extracted_text": "hello world",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_status_update_valid_transition(client: TestClient) -> None:
    token = _register_and_login(client, "owner@example.com", "strong-pass-123")
    document_id = _create_document(client, token)

    response = client.post(
        f"/api/v1/documents/{document_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "processing"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["processing_status"] == "processing"


def test_status_update_invalid_transition_returns_422(client: TestClient) -> None:
    token = _register_and_login(client, "owner2@example.com", "strong-pass-123")
    document_id = _create_document(client, token)

    response = client.post(
        f"/api/v1/documents/{document_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "completed"},
    )

    assert response.status_code == 422
    assert "Cannot transition" in response.json()["error"]["message"]


def test_status_update_forbidden_for_non_owner(client: TestClient) -> None:
    owner_token = _register_and_login(client, "owner3@example.com", "strong-pass-123")
    other_token = _register_and_login(client, "other3@example.com", "strong-pass-123")
    document_id = _create_document(client, owner_token)

    response = client.post(
        f"/api/v1/documents/{document_id}/status",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"status": "processing"},
    )

    assert response.status_code == 403


def test_status_update_requires_authentication(client: TestClient) -> None:
    token = _register_and_login(client, "owner4@example.com", "strong-pass-123")
    document_id = _create_document(client, token)

    response = client.post(
        f"/api/v1/documents/{document_id}/status",
        json={"status": "processing"},
    )

    assert response.status_code == 401
