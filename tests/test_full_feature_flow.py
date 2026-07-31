def _analyze_email(client):
    response = client.post(
        "/api/v1/analyses/email",
        json={
            "text": "Please send the contract by Friday.",
            "target_country": "JP",
            "language": "en",
            "source": "gmail",
            "mode": "manual",
            "client_request_id": "email-flow-test",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_meeting_analysis(client):
    response = client.post(
        "/api/v1/meetings/transcript",
        json={
            "title": "Partner meeting",
            "transcript": (
                "Alice: You are wrong about the delivery schedule. "
                "Bob: We should review the timeline and agree on next steps."
            ),
            "target_country": "JP",
            "language": "en",
            "client_request_id": "meeting-flow-test",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meeting_temperature"] <= 88
    assert body["issues"][0]["category"] == "tone"
    assert body["key_points"]
    assert body["action_items"]


def test_dashboard_aggregates_email_and_meeting(client):
    _analyze_email(client)
    meeting_response = client.post(
        "/api/v1/meetings/transcript",
        json={
            "title": "Weekly meeting",
            "transcript": (
                "We discussed the product schedule and agreed to send "
                "a written update after the meeting."
            ),
            "target_country": "US",
        },
    )
    assert meeting_response.status_code == 200

    response = client.get("/api/v1/dashboard/summary?period_days=7")

    assert response.status_code == 200
    body = response.json()
    assert body["total_analyses"] == 2
    assert body["email_analyses"] == 1
    assert body["meeting_analyses"] == 1
    assert body["country_usage"]


def test_quiz_is_generated_from_analysis_issue(client):
    _analyze_email(client)

    quiz_response = client.get("/api/v1/quizzes?limit=3")
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()
    assert quiz["generated_from_analyses"] == 1
    assert quiz["questions"]

    question = quiz["questions"][0]
    correct_option = next(
        option
        for option in question["options"]
        if option["text"].startswith("Would it be possible")
    )
    answer_response = client.post(
        f"/api/v1/quizzes/{question['id']}/answer",
        json={"option_id": correct_option["id"]},
    )
    assert answer_response.status_code == 200
    assert answer_response.json()["correct"] is True


def test_suggestion_action_and_feedback(client):
    analysis = _analyze_email(client)
    issue_id = analysis["issues"][0]["issue_id"]

    action_response = client.post(
        f"/api/v1/analyses/{analysis['analysis_id']}/actions",
        json={
            "issue_id": issue_id,
            "action": "accepted",
        },
    )
    assert action_response.status_code == 200
    assert action_response.json()["saved"] is True

    feedback_response = client.post(
        "/api/v1/feedback",
        json={
            "analysis_id": analysis["analysis_id"],
            "rating": 5,
            "is_helpful": True,
            "comment": "문화적 이유가 명확했습니다.",
        },
    )
    assert feedback_response.status_code == 201

    dashboard = client.get("/api/v1/dashboard/summary").json()
    assert dashboard["accepted_suggestions"] == 1


def test_analysis_history(client):
    _analyze_email(client)

    response = client.get("/api/v1/analyses?kind=email")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["kind"] == "email"

