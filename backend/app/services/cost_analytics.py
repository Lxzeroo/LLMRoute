from app.core.database import get_connection


class CostAnalytics:

    def record(self, result):

        routing = result.get("routing", {})
        cost = result["cost"]

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO request_metrics (
                    query, model, source, cache_hit,
                    similarity, latency_ms, inference_ms,
                    input_tokens, output_tokens,
                    complexity_score, routing_mode,
                    estimated_cost_usd, baseline_cost_usd,
                    estimated_savings_usd, budget_usd
                )
                VALUES (
                    %s, %s, %s, %s, %s,
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
                    routing.get("complexity_score"),
                    result["mode"],
                    cost["estimated_cost_usd"],
                    cost["baseline_cost_usd"],
                    cost["estimated_savings_usd"],
                    result.get("budget_usd")
                )
            )

    def summary(self):

        with get_connection() as conn:
            result = conn.execute(
                """
                SELECT
                    COUNT(*) AS cost_tracked_requests,
                    COALESCE(SUM(estimated_cost_usd), 0)
                        AS estimated_cost_usd,
                    COALESCE(SUM(baseline_cost_usd), 0)
                        AS baseline_cost_usd,
                    COALESCE(SUM(estimated_savings_usd), 0)
                        AS estimated_savings_usd
                FROM request_metrics
                WHERE estimated_cost_usd IS NOT NULL
                """
            ).fetchone()

        baseline = result["baseline_cost_usd"]

        result["savings_percent"] = round(
            result["estimated_savings_usd"] / baseline * 100,
            2
        ) if baseline else 0.0

        result["actual_api_cost_usd"] = 0.0
        result["pricing_type"] = "simulated"

        return result


cost_analytics = CostAnalytics()
