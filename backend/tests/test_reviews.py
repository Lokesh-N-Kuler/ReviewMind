def test_quick_review_pipeline(client):
    code = """
def authenticate_user(username, password):
    # Vulnerable raw query
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    eval(password)
    return db.execute(query)
"""
    payload = {
        "language": "python",
        "source_code": code,
        "file_path": "auth.py"
    }

    res = client.post("/api/reviews/quick", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "findings" in data
    assert len(data["findings"]) >= 2
    assert "metrics" in data
    assert data["metrics"]["critical"] >= 1
    assert data["score"] < 100

    # Verify structured fields
    finding = data["findings"][0]
    assert "finding_id" in finding
    assert "title" in finding
    assert "category" in finding
    assert "severity" in finding
    assert "line_start" in finding
    assert "explanation" in finding
    assert "suggested_fix" in finding

def test_project_review_and_feedback(client):
    # Login
    login_payload = {"email": "alice@reviewmind.ai", "password": "securepassword123"}
    token = client.post("/api/auth/login", json=login_payload).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch Alice's project
    projects = client.get("/api/projects", headers=headers).json()
    project_id = projects[0]["id"]

    # Submit code review for project
    code = """
def fetch_records(record_id):
    query = "SELECT * FROM records WHERE id = " + record_id
    return db.execute(query)
"""
    review_res = client.post(
        "/api/reviews",
        json={
            "project_id": project_id,
            "language": "python",
            "source_code": code,
            "title": "Data Access Layer Review",
            "file_path": "records.py"
        },
        headers=headers
    )
    assert review_res.status_code == 201
    review_data = review_res.json()
    review_id = review_data["id"]
    finding_id = review_data["findings"][0]["finding_id"]

    # Submit developer feedback
    feedback_res = client.post(
        f"/api/reviews/{review_id}/feedback",
        json={
            "finding_id": finding_id,
            "feedback_type": "accepted",
            "comment": "Good catch, will switch to parameterized queries",
            "retain_in_hindsight": True
        },
        headers=headers
    )
    assert feedback_res.status_code == 200
    fb_data = feedback_res.json()
    assert fb_data["finding_id"] == finding_id
    assert fb_data["feedback_type"] == "accepted"
