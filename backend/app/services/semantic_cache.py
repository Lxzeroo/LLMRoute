import asyncio
import hashlib

import numpy as np

from app.core.config import settings
from app.core.database import get_connection
from app.services.embeddings import embedding_service


class SemanticCache:

    @staticmethod
    def hash_query(query):
        return hashlib.sha256(
            query.strip().encode("utf-8")
        ).hexdigest()

    def exact_lookup(self, query, scope):

        with get_connection() as conn:

            return conn.execute(
                """
                UPDATE semantic_cache
                SET hit_count = hit_count + 1
                WHERE query_hash = %s
                AND scope = %s
                AND embedding_model = %s
                AND expires_at > NOW()
                RETURNING query, answer, model
                """,
                (
                    self.hash_query(query),
                    scope,
                    settings.embedding_model
                )
            ).fetchone()

    def vector_lookup(self, vector, scope):

        vector = np.asarray(vector, dtype=np.float32)

        with get_connection() as conn:

            result = conn.execute(
                """
                SELECT id, query, answer, model,
                    1 - (embedding <=> %s) AS similarity
                FROM semantic_cache
                WHERE scope = %s
                AND embedding_model = %s
                AND expires_at > NOW()
                ORDER BY embedding <=> %s
                LIMIT 1
                """,
                (
                    vector,
                    scope,
                    settings.embedding_model,
                    vector
                )
            ).fetchone()

            if (
                result
                and result["similarity"]
                >= settings.cache_similarity_threshold
            ):

                conn.execute(
                    """
                    UPDATE semantic_cache
                    SET hit_count = hit_count + 1
                    WHERE id = %s
                    """,
                    (result["id"],)
                )

                return result

        return None

    async def lookup(self, query, scope="default"):

        exact = await asyncio.to_thread(
            self.exact_lookup, query, scope
        )

        if exact:
            return {
                "cache_hit": True,
                "cache_type": "exact",
                "answer": exact["answer"],
                "matched_query": exact["query"],
                "cached_model": exact["model"],
                "similarity": 1.0
            }

        vector = await embedding_service.embed(query)

        similar = await asyncio.to_thread(
            self.vector_lookup, vector, scope
        )

        if similar:
            return {
                "cache_hit": True,
                "cache_type": "semantic",
                "answer": similar["answer"],
                "matched_query": similar["query"],
                "cached_model": similar["model"],
                "similarity": round(
                    float(similar["similarity"]), 4
                )
            }

        return {
            "cache_hit": False,
            "cache_type": None,
            "embedding": vector
        }

    def store(
        self, query, answer, embedding,
        scope="default", model=None
    ):

        vector = np.asarray(
            embedding, dtype=np.float32
        )

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO semantic_cache (
                    query_hash, query, answer,
                    embedding, scope, embedding_model,
                    model, expires_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    NOW() + (%s * INTERVAL '1 second')
                )
                ON CONFLICT (
                    scope, query_hash, embedding_model
                )
                DO UPDATE SET
                    answer = EXCLUDED.answer,
                    embedding = EXCLUDED.embedding,
                    model = EXCLUDED.model,
                    created_at = NOW(),
                    expires_at = EXCLUDED.expires_at
                """,
                (
                    self.hash_query(query),
                    query,
                    answer,
                    vector,
                    scope,
                    settings.embedding_model,
                    model,
                    settings.cache_ttl_seconds
                )
            )

    def stats(self):

        with get_connection() as conn:

            cache = conn.execute(
                """
                SELECT COUNT(*) AS entries
                FROM semantic_cache
                WHERE expires_at > NOW()
                """
            ).fetchone()

            metrics = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_requests,
                    COUNT(*) FILTER (
                        WHERE cache_hit
                    ) AS hits,
                    COUNT(*) FILTER (
                        WHERE NOT cache_hit
                    ) AS misses
                FROM request_metrics
                """
            ).fetchone()

        total = metrics["total_requests"]

        return {
            **cache,
            **metrics,
            "hit_rate": round(
                metrics["hits"] / total * 100, 2
            ) if total else 0.0
        }

    def clear(self):

        with get_connection() as conn:
            conn.execute("DELETE FROM semantic_cache")


semantic_cache = SemanticCache()
