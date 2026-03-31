# tests/test_health_check.py


def test_health_check(client):
    """
    Testet den Health-Check Endpoint unter /api/v1/utils/health-check
    """
    # GET Request an Health-Check Endpoint
    response = client.get("/api/v1/utils/health-check")

    # Status-Code prüfen
    assert response.status_code == 200

    # Rückgabe prüfen
    assert response.json() == {"status": "ok"}


def test_global_health_endpoint(client):
    """
    Testet den globalen Health-Endpoint unter /health

    Dieser Endpoint folgt der Standard-Konvention für Health Checks
    und ist ideal für Load Balancer und Kubernetes Probes.
    """
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "model_loaded" in data
    assert "database" in data
