def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "ReviewMind"

def test_diagnostics_endpoint(client):
    response = client.get("/api/health/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert data["database"]["connected"] is True
    assert "ai_service" in data
    assert "memory_service" in data
