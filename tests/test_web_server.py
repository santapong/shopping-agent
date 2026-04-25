"""Smoke tests for the web demo server (frontend + /api routes)."""

from fastapi.testclient import TestClient

from shopping_agent.web_server import app


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["ucp"] == "online"
    assert body["products"] > 0


def test_index_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "UCP Shopping Agent" in resp.text


def test_static_assets_served():
    css = client.get("/static/styles.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]

    js = client.get("/static/app.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]


def test_chat_requires_api_key(monkeypatch):
    """Without ANTHROPIC_API_KEY the /api/chat route should return 503."""
    # Make sure no key is present and no agent has been built yet.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import shopping_agent.web_server as ws

    monkeypatch.setattr(ws, "_agent", None)
    monkeypatch.setattr(ws, "_agent_error", None)

    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]
