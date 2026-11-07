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
