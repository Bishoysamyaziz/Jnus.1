"""Tests for FastAPI endpoints"""
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
    assert "status" in data
    assert "version" in data
    assert "uptime" in data


@pytest.mark.asyncio
async def test_process_endpoint(client):
    """POST /process should process a task"""
    payload = {
        "description": "write a Python function",
        "intent_type": "CODE",
        "user_id": "test_user",
        "session_id": "test_session",
    }
    response = await client.post("/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "framework" in data
    assert "success" in data


@pytest.mark.asyncio
async def test_process_endpoint_empty(client):
    """POST /process with empty description should return 400"""
    payload = {
        "description": "",
        "intent_type": "CODE",
        "user_id": "test_user",
        "session_id": "test_session",
    }
    response = await client.post("/process", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_process_endpoint_invalid(client):
    """POST /process with missing fields should return 422"""
    payload = {"description": "test"}
    response = await client.post("/process", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agents_endpoint(client):
    """GET /agents should return list of available agents"""
    response = await client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("name" in a for a in data)


@pytest.mark.asyncio
async def test_agents_by_intent_endpoint(client):
    """GET /agents/{intent_type} should return agents for intent"""
    response = await client.get("/agents/CODE")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_agents_by_intent_invalid(client):
    """GET /agents/{invalid} should return 400"""
    response = await client.get("/agents/INVALID_INTENT")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_memory_endpoint(client):
    """GET /memory/{session_id} should return session memory"""
    response = await client.get("/memory/test_session")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data


@pytest.mark.asyncio
async def test_memory_clear_endpoint(client):
    """DELETE /memory/{session_id} should clear session memory"""
    response = await client.delete("/memory/test_session")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleared"


@pytest.mark.asyncio
async def test_stats_endpoint(client):
    """GET /stats should return system statistics"""
    response = await client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "agents_used" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """GET /metrics should return Prometheus metrics"""
    response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cors_headers(client):
    """Response should include CORS headers"""
    response = await client.options("/health")
    assert "access-control-allow-origin" in response.headers
