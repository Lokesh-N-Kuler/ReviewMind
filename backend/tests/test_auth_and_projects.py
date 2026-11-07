def test_user_registration_and_login(client):
    # Register
    reg_payload = {
        "email": "alice@reviewmind.ai",
        "password": "securepassword123",
        "full_name": "Alice Engineer"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@reviewmind.ai"

    # Login
    login_payload = {
        "email": "alice@reviewmind.ai",
        "password": "securepassword123"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]

    # Get Me
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "alice@reviewmind.ai"

def test_project_crud(client):
    # Login as Alice
    login_payload = {
        "email": "alice@reviewmind.ai",
        "password": "securepassword123"
    }
    token = client.post("/api/auth/login", json=login_payload).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_payload = {
        "name": "Payment Service",
        "description": "Secure payment processing microservice",
        "languages": ["python", "sql"],
        "coding_standards": "All database queries MUST use parameterized inputs. No raw SQL concatenation."
    }
    create_res = client.post("/api/projects", json=proj_payload, headers=headers)
    assert create_res.status_code == 201
    proj_data = create_res.json()
    assert proj_data["name"] == "Payment Service"
    assert "reviewmind-project-" in proj_data["hindsight_bank_id"]
    project_id = proj_data["id"]

    # List projects
    list_res = client.get("/api/projects", headers=headers)
    assert list_res.status_code == 200
    projects = list_res.json()
    assert any(p["id"] == project_id for p in projects)

    # Get single project
    get_res = client.get(f"/api/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Payment Service"

    # Update project
    update_res = client.put(
        f"/api/projects/{project_id}",
        json={"description": "Updated description"},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated description"

def test_auth_validation_and_protected_routes(client):
    # 1. Unauthenticated requests to protected endpoints return 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/reviews").status_code == 401
    assert client.post("/api/projects", json={"name": "Hacked"}).status_code == 401

    # 2. Malformed or invalid Bearer tokens return 401
    bad_headers = {"Authorization": "Bearer invalid.jwt.signature"}
    assert client.get("/api/auth/me", headers=bad_headers).status_code == 401
    assert client.get("/api/projects", headers=bad_headers).status_code == 401

    # 3. Invalid login credentials return 401
    invalid_login = client.post("/api/auth/login", json={"email": "alice@reviewmind.ai", "password": "wrongpassword"})
    assert invalid_login.status_code == 401

    nonexistent_login = client.post("/api/auth/login", json={"email": "nobody@reviewmind.ai", "password": "anypassword"})
    assert nonexistent_login.status_code == 401

    # 4. Duplicate registration email returns 400
    dup_res = client.post(
        "/api/auth/register",
        json={"email": "alice@reviewmind.ai", "password": "anotherpassword", "full_name": "Alice Duplicate"}
    )
    assert dup_res.status_code == 400

def test_user_ownership_isolation(client):
    # Register and login Bob
    bob_reg = client.post(
        "/api/auth/register",
        json={"email": "bob@reviewmind.ai", "password": "bobpassword123", "full_name": "Bob Security"}
    )
    assert bob_reg.status_code == 201
    bob_token = bob_reg.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Login Alice
    alice_token = client.post(
        "/api/auth/login",
        json={"email": "alice@reviewmind.ai", "password": "securepassword123"}
    ).json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    # Alice creates a confidential project
    alice_proj = client.post(
        "/api/projects",
        json={"name": "Alice Secret Project", "description": "Confidential IP"},
        headers=alice_headers
    ).json()
    alice_proj_id = alice_proj["id"]

    # Bob attempts to access Alice's project -> 403 Forbidden
    assert client.get(f"/api/projects/{alice_proj_id}", headers=bob_headers).status_code == 403

    # Bob attempts to update Alice's project -> 403 Forbidden
    assert client.put(f"/api/projects/{alice_proj_id}", json={"name": "Hijacked"}, headers=bob_headers).status_code == 403

    # Bob attempts to delete Alice's project -> 403 Forbidden
    assert client.delete(f"/api/projects/{alice_proj_id}", headers=bob_headers).status_code == 403

    # Bob attempts to access Alice's project memory -> 403 Forbidden
    assert client.get(f"/api/memory/{alice_proj_id}", headers=bob_headers).status_code == 403
    assert client.get(f"/api/memory/{alice_proj_id}/status", headers=bob_headers).status_code == 403
    assert client.get(f"/api/memory/{alice_proj_id}/activity", headers=bob_headers).status_code == 403

    # Bob attempts to retain memory into Alice's project -> 403 Forbidden
    retain_res = client.post(
        f"/api/memory/{alice_proj_id}/retain",
        json={"content": "Malicious injected standard", "category": "coding_standards"},
        headers=bob_headers
    )
    assert retain_res.status_code == 403

    # Bob attempts to recall memory from Alice's project -> 403 Forbidden
    recall_res = client.post(
        f"/api/memory/{alice_proj_id}/recall",
        json={"query": "secret"},
        headers=bob_headers
    )
    assert recall_res.status_code == 403
