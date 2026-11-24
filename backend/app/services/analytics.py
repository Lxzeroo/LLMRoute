from app.core.database import get_connection


class AnalyticsService:

    def record(self, result):
        routing = result.get("routing", {})

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO request_metrics (
                    query, model, source, cache_hit,
                    similarity, latency_ms,
                    inference_ms, input_tokens,
                    output_tokens, complexity_score
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    result["query"],
                    result.get("model"),
                    result["source"],
                    result["cache_hit"],
                    result.get("similarity"),
                    result["latency_ms"],
                    result.get("inference_ms", 0),
                    result.get("input_tokens", 0),
                    result.get("output_tokens", 0),
                    routing.get("complexity_score")
                )
            )

    def summary(self):
        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_requests,
                    COUNT(*) FILTER (
                        WHERE source = 'exact_cache'
                    ) AS exact_hits,
                    COUNT(*) FILTER (
                        WHERE source = 'semantic_cache'
                    ) AS semantic_hits,
                    COUNT(*) FILTER (
                        WHERE source = 'llm'
                    ) AS llm_calls,
                    COALESCE(AVG(latency_ms), 0)
                        AS avg_latency_ms,
                    COALESCE(
                        percentile_cont(0.5)
                        WITHIN GROUP (ORDER BY latency_ms),
                        0
                    ) AS p50_latency_ms,
                    COALESCE(
                        percentile_cont(0.95)
                        WITHIN GROUP (ORDER BY latency_ms),
                        0
                    ) AS p95_latency_ms,
                    COALESCE(SUM(input_tokens), 0)
                        AS input_tokens,
                    COALESCE(SUM(output_tokens), 0)
                        AS output_tokens
                FROM request_metrics
                """
            ).fetchone()

        total = result["total_requests"]
        hits = result["exact_hits"] + result["semantic_hits"]

        result["cache_hit_rate"] = (
            round(hits / total * 100, 2)
            if total else 0.0
        )

        result["llm_calls_avoided"] = hits

        return result

    def history(self, limit=50):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT *
                FROM request_metrics
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,)
            ).fetchall()

    def model_usage(self):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT model,
                    COUNT(*) AS requests,
                    AVG(latency_ms) AS avg_latency_ms,
                    SUM(input_tokens) AS input_tokens,
                    SUM(output_tokens) AS output_tokens
                FROM request_metrics
                WHERE source = 'llm'
                GROUP BY model
                ORDER BY requests DESC
                """
            ).fetchall()


analytics_service = AnalyticsService()
