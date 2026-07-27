def test_analyze_email_with_mock_ai(client):
    response = client.post(
        "/api/v1/analyses/email",
        headers={
            "X-Request-ID": "test-request-id",
            "X-Extension-Version": "0.1.0",
        },
        json={
            "text": "Please send the contract by Friday.",
            "target_country": "JP",
            "language": "en",
            "source": "gmail",
            "mode": "manual",
            "client_request_id": "test-client-request",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["request_id"] == "test-request-id"
    assert body["overall_score"] == 72
    assert body["issues"][0]["category"] == "tone"
    assert body["issues"][0]["suggestion"]


def test_rejects_short_email(client):
    response = client.post(
        "/api/v1/analyses/email",
        json={
            "text": "short",
            "target_country": "JP",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_rejects_unsupported_country(client):
    response = client.post(
        "/api/v1/analyses/email",
        json={
            "text": "This is a sufficiently long email.",
            "target_country": "FR",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"
