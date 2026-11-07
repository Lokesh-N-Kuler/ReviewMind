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

def test_quick_review_multiple_calls_no_unbound_local_error(client):
    """
    CRITICAL REGRESSION TEST for Phase 2:
    Calling quick_review repeatedly must not throw UnboundLocalError for demo_user,
    and must consistently return valid reviews for both unauthenticated and authenticated users.
    """
    code = "def add(a, b): return a + b"
    payload = {"language": "python", "source_code": code}

    # Call 1: creates/checks playground project
    res1 = client.post("/api/reviews/quick", json=payload)
    assert res1.status_code == 200
    assert "findings" in res1.json()

    # Call 2: Playground project already exists in database; must NOT raise UnboundLocalError
    res2 = client.post("/api/reviews/quick", json=payload)
    assert res2.status_code == 200
    assert "findings" in res2.json()

    # Call 3: Call with authenticated user
    login_payload = {"email": "alice@reviewmind.ai", "password": "securepassword123"}
    token = client.post("/api/auth/login", json=login_payload).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res3 = client.post("/api/reviews/quick", json=payload, headers=headers)
    assert res3.status_code == 200

def test_review_authorization_and_ownership(client):
    # Login Alice
    alice_token = client.post(
        "/api/auth/login",
        json={"email": "alice@reviewmind.ai", "password": "securepassword123"}
    ).json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    # Login Bob
    bob_token = client.post(
        "/api/auth/login",
        json={"email": "bob@reviewmind.ai", "password": "bobpassword123"}
    ).json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Get Alice's review
    alice_reviews = client.get("/api/reviews", headers=alice_headers).json()
    assert len(alice_reviews) > 0
    alice_review_id = alice_reviews[0]["id"]
    alice_project_id = alice_reviews[0]["project_id"]

    # Bob attempts to get Alice's review -> 403 Forbidden
    assert client.get(f"/api/reviews/{alice_review_id}", headers=bob_headers).status_code == 403

    # Bob attempts to get Alice's review findings -> 403 Forbidden
    assert client.get(f"/api/reviews/{alice_review_id}/findings", headers=bob_headers).status_code == 403

    # Bob attempts to filter reviews by Alice's project_id -> 403 Forbidden
    assert client.get(f"/api/reviews?project_id={alice_project_id}", headers=bob_headers).status_code == 403

    # Bob attempts to submit feedback on Alice's review -> 403 Forbidden
    feedback_payload = {
        "finding_id": "FIND-001",
        "feedback_type": "rejected",
        "comment": "Unauthorized tamper"
    }
    assert client.post(f"/api/reviews/{alice_review_id}/feedback", json=feedback_payload, headers=bob_headers).status_code == 403

def test_finding_schema_normalization():
    from app.schemas.review import FindingSchema
    # Test uppercase severity and synonym category normalization
    f = FindingSchema(
        finding_id="FIND-TEST",
        title="SQL Vulnerability",
        category="vulnerability",  # synonym for security
        severity="CRITICAL",        # uppercase
        explanation="Insecure query string",
        why_it_matters="Data leakage",
        suggested_fix="Use parameterized queries"
    )
    assert f.severity == "critical"
    assert f.category == "security"

def test_groq_fallback_generation():
    from app.services.ai_service import ai_service
    # Test fallback generation when Groq is unavailable or times out
    static_issues = [{
        "finding_id": "STATIC-PY-001",
        "title": "SQL Injection Detected",
        "category": "security",
        "severity": "critical",
        "line_start": 3,
        "line_end": 3,
        "explanation": "Concatenation detected in SQL statement",
        "why_it_matters": "Risk of SQL injection",
        "suggested_fix": "Use parameters"
    }]
    fallback = ai_service._generate_fallback_review(
        code="query = 'SELECT * FROM users WHERE id = ' + uid",
        language="python",
        file_path="db.py",
        static_findings=static_issues,
        error_note="Simulated timeout"
    )
    assert len(fallback.findings) == 1
    assert fallback.findings[0].severity == "critical"
    assert "Simulated timeout" in fallback.summary
    assert fallback.score < 100.0
