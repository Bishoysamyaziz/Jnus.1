"""OneAgent OS — Skill Memory (Qdrant Vector DB)
Learned strategies for optimal agent selection per intent type.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, Optional


class SkillMemory:
    """Qdrant Vector DB — learned strategies"""

    def __init__(self, qdrant_url: Optional[str] = None):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self._client = None
        self.collection_name = "skills"

    async def _get_client(self):
        if self._client is None:
            from qdrant_client import AsyncQdrantClient
            self._client = AsyncQdrantClient(self.qdrant_url)
            await self._ensure_collection()
        return self._client

    async def _ensure_collection(self):
        try:
            client = self._client
            collections = await client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={"size": 384, "distance": "Cosine"},
                )
        except Exception:
            pass  # Qdrant might not be available

    async def save(self, intent_type: str, strategy: dict, score: float):
        """Save a learned strategy"""
        try:
            client = await self._get_client()
            # Simple embedding: use the strategy as text
            import hashlib
            text = json.dumps(strategy, sort_keys=True)
            vector = self._simple_embed(text)

            await client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {
                        "intent_type": intent_type,
                        "strategy": json.dumps(strategy),
                        "performance_score": score,
                        "used_count": 1,
                    },
                }],
            )
        except Exception:
            pass  # Graceful degradation

    async def get_best(self, intent_type: str) -> dict | None:
        """Get the best strategy for an intent type"""
        try:
            client = await self._get_client()
            results = await client.search(
                collection_name=self.collection_name,
                query_vector=self._simple_embed(intent_type),
                query_filter={"must": [{"key": "intent_type", "match": {"value": intent_type}}]},
                limit=1,
                with_payload=True,
            )
            if results:
                payload = results[0].payload
                return {
                    "intent_type": payload.get("intent_type"),
                    "strategy": json.loads(payload.get("strategy", "{}")),
                    "performance_score": payload.get("performance_score", 0),
                }
        except Exception:
            pass
        return None

    def _simple_embed(self, text: str) -> list[float]:
        """Real embedding using FastEmbed (BGE-small) — replaces SHA256 hash hack"""
        try:
            from fastembed import TextEmbedding
            # Lazy-init model (singleton pattern)
            if not hasattr(self, '_embed_model'):
                self._embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
            return list(self._embed_model.embed([text]))[0].tolist()
        except ImportError:
            # Fallback: deterministic hash-based embedding (last resort)
            import hashlib
            vector = []
            for i in range(384):
                h = hashlib.sha256(f"{text}:{i}".encode()).digest()
                val = int.from_bytes(h[:4], "big") / (2**32 - 1)
                vector.append(val * 2 - 1)
            return vector

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            await client.get_collections()
            return True
        except Exception:
            return False
