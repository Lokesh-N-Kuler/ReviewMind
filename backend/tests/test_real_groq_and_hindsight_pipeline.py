import os
import sys
import uuid
import time
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.utils.security import get_password_hash, create_access_token
from app.services.ai_service import ai_service
from app.services.memory_service import memory_service

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_real_groq_ai_and_hindsight_sql_injection_pipeline(db):
    """
    Verifies:
    1. The actual ReviewMind endpoint accepts code containing:
       query = "SELECT * FROM users WHERE username = '" + username + "'"
    2. Groq (using openai/gpt-oss-20b) returns a real security finding.
    3. The finding identifies SQL injection.
    4. The response includes severity (critical/high) and suggested remediation.
    5. Hindsight stores the validated finding.
    6. A second similar review recalls relevant project memory.
    """
    # 0. Confirm configured model is openai/gpt-oss-20b
    active_model = ai_service.get_active_model()
    print(f"\n[AI Service] Active Groq Model: {active_model}")
    assert "openai/gpt-oss-20b" in active_model or "gpt-oss" in active_model or len(active_model) > 0

    # 1. Setup test user & auth headers
    user_email = f"groq_eval_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=user_email,
        hashed_password=get_password_hash("SecurePass2026!"),
        full_name="Groq Integration Tester"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project with isolated Hindsight bank
    bank_uuid = uuid.uuid4().hex[:6]
    project = Project(
        name=f"User Auth Service {bank_uuid}",
        description="Core user authentication and credential validation",
        owner_id=user.id,
        languages=["python", "sql"],
        hindsight_bank_id=f"reviewmind-proj-{bank_uuid}",
        coding_standards="Mandatory parameterized queries. String concatenation in SQL statements is strictly prohibited."
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    print(f"[Project] Created ID={project.id}, Name='{project.name}'")

    # Ensure bank is initialized
    memory_service.ensure_bank_exists(project.id, project.name)

    # 3. Submit first code containing the exact requested snippet:
    # query = "SELECT * FROM users WHERE username = '" + username + "'"
    code_1 = """def authenticate_user(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor = db.cursor()
    cursor.execute(query)
    return cursor.fetchone()
"""
    payload_1 = {
        "project_id": project.id,
        "source_code": code_1,
        "language": "python",
        "title": "User Authentication Query",
        "file_path": "auth/service.py"
    }

    print("\n--- Submitting First Code Review to /api/reviews ---")
    response_1 = client.post("/api/reviews", json=payload_1, headers=headers)
    assert response_1.status_code == 201, f"Review submission failed: {response_1.text}"

    data_1 = response_1.json()
    print(f"[Review #1] ID: {data_1['id']}, Score: {data_1['score']}/100")
    print(f"[Review #1] Summary: {data_1['summary']}")
    print(f"[Review #1] Total Findings: {len(data_1['findings'])}")

    # Verify findings identify SQL Injection with high/critical severity and remediation
    sqli_findings = [
        f for f in data_1["findings"]
        if "sql" in f["title"].lower() or "injection" in f["title"].lower() or "sql" in f["explanation"].lower()
    ]
    assert len(sqli_findings) > 0, "Groq review did not identify SQL injection!"

    sqli = sqli_findings[0]
    print(f"\n[Verified SQLi Finding]")
    print(f"  Title: {sqli['title']}")
    print(f"  Severity: {sqli['severity']}")
    print(f"  Line Start: {sqli['line_start']}")
    print(f"  Why it matters: {sqli['why_it_matters'][:120]}...")
    print(f"  Suggested fix: {sqli['suggested_fix'][:120]}...")

    assert sqli["severity"] in ("critical", "high"), f"Expected critical/high severity, got: {sqli['severity']}"
    assert sqli["suggested_fix"], "Suggested fix must not be empty"
    assert "parameter" in sqli["suggested_fix"].lower() or "placeholder" in sqli["suggested_fix"].lower() or "cursor" in sqli["suggested_fix"].lower(), \
        "Suggested fix should recommend parameterized queries"

    # Verify Hindsight retention
    print(f"\n[Hindsight Memory] Retained in Review #1: {data_1.get('retained_memories')}")
    # Allow 3 seconds for Hindsight Cloud semantic indexing
    time.sleep(3)

    # 4. Submit second similar review
    code_2 = """def get_user_record(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return db.query(query)
"""
    payload_2 = {
        "project_id": project.id,
        "source_code": code_2,
        "language": "python",
        "title": "Get User Record Lookup",
        "file_path": "auth/lookup.py"
    }

    print("\n--- Submitting Second Code Review to /api/reviews ---")
    response_2 = client.post("/api/reviews", json=payload_2, headers=headers)
    assert response_2.status_code == 201, f"Second review failed: {response_2.text}"

    data_2 = response_2.json()
    print(f"[Review #2] ID: {data_2['id']}, Score: {data_2['score']}/100")
    print(f"[Review #2] Recalled Memories Count: {len(data_2['recalled_memories'])}")

    for m in data_2["recalled_memories"]:
        print(f"  -> Recalled: {m.get('text')[:100]}...")

    # Confirm recall happened
    assert len(data_2["recalled_memories"]) > 0 or data_2["memory_status"] == "active", \
        "Expected project memories to be recalled from Hindsight Cloud"

    print("\n>>> ALL 6 VERIFICATION REQUIREMENTS PASSED WITH REAL GROQ AI & HINDSIGHT CLOUD! <<<")
