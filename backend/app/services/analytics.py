from app.core.database import get_connection
class AnalyticsService:
    def summary(self):
        with get_connection() as conn:
            r=conn.execute('''SELECT count(*) AS total_requests,count(*) FILTER(WHERE source='exact_cache') AS exact_hits,count(*) FILTER(WHERE source='semantic_cache') AS semantic_hits,count(*) FILTER(WHERE source='llm') AS llm_calls,coalesce(avg(latency_ms),0) AS avg_latency_ms,coalesce(percentile_cont(.5) WITHIN GROUP(ORDER BY latency_ms),0) AS p50_latency_ms,coalesce(percentile_cont(.95) WITHIN GROUP(ORDER BY latency_ms),0) AS p95_latency_ms,coalesce(sum(input_tokens),0) AS input_tokens,coalesce(sum(output_tokens),0) AS output_tokens FROM request_metrics''').fetchone()
        hits=r['exact_hits']+r['semantic_hits']; r.update(cache_hit_rate=round(100*hits/r['total_requests'],2) if r['total_requests'] else 0,llm_calls_avoided=hits); return r
    def history(self,limit=50):
        with get_connection() as conn: return conn.execute('SELECT * FROM request_metrics ORDER BY id DESC LIMIT %s',(limit,)).fetchall()
    def model_usage(self):
        with get_connection() as conn: return conn.execute("SELECT model,count(*) AS requests,avg(latency_ms) AS avg_latency_ms,sum(input_tokens) AS input_tokens,sum(output_tokens) AS output_tokens FROM request_metrics WHERE source='llm' GROUP BY model ORDER BY requests DESC").fetchall()
analytics_service=AnalyticsService()
