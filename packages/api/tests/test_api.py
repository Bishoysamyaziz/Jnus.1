"""Tests for FastAPI endpoints — matches actual API routes"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from packages.api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /health should return system status"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    """POST /v1/chat should return SSE stream"""
    payload = {
        "message": "write a Python function",
        "session_id": "test_session",
        "user_id": "test_user",
    }
    response = await client.post("/v1/chat", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    # Read first few events
    content = response.text
    assert "data: " in content


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message(client):
    """POST /v1/chat with empty message should still work"""
    payload = {
        "message": "",
        "session_id": "test_session",
        "user_id": "test_user",
    }
    response = await client.post("/v1/chat", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"


@pytest.mark.asyncio
async def test_chat_endpoint_no_session(client):
    """POST /v1/chat without session_id should work (auto-generates)"""
    payload = {
        "message": "hello",
        "user_id": "test_user",
    }
    response = await client.post("/v1/chat", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_agents_endpoint(client):
    """GET /v1/agents should return list of available agents"""
    response = await client.get("/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "total" in data
    assert isinstance(data["agents"], list)


@pytest.mark.asyncio
async def test_history_endpoint(client):
    """GET /v1/history should return sessions"""
    response = await client.get("/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data


@pytest.mark.asyncio
async def test_history_with_session_id(client):
    """GET /v1/history?session_id=... should return session messages"""
    response = await client.get("/v1/history", params={"session_id": "test_session"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "messages" in data


@pytest.mark.asyncio
async def test_delete_history(client):
    """DELETE /v1/history/{session_id} should work"""
    response = await client.delete("/v1/history/test_session")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """GET /metrics should return system metrics"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data
    assert "uptime_seconds" in data
    assert "agents_registered" in data


@pytest.mark.asyncio
async def test_cors_headers(client):
    """Response should include CORS headers"""
    response = await client.options("/health")
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_chat_sse_format(client):
    """Chat endpoint should return valid SSE format"""
    payload = {
        "message": "test",
        "session_id": "sse_test",
        "user_id": "test_user",
    }
    response = await client.post("/v1/chat", json=payload)
    assert response.status_code == 200
    # Check SSE headers
    assert response.headers.get("cache-control") == "no-cache"
    assert response.headers.get("x-accel-buffering") == "no"
