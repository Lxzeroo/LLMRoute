from app.core.database import get_connection
class CostAnalytics:
    def record(self,result):
        c=result['cost']; r=result.get('routing',{})
        with get_connection() as conn:
            conn.execute('''INSERT INTO request_metrics(query,model,source,cache_hit,similarity,latency_ms,inference_ms,input_tokens,output_tokens,complexity_score,routing_mode,estimated_cost_usd,baseline_cost_usd,estimated_savings_usd,budget_usd) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(result['query'],result.get('model'),result['source'],result['cache_hit'],result.get('similarity'),result['latency_ms'],result.get('inference_ms',0),result.get('input_tokens',0),result.get('output_tokens',0),r.get('complexity_score'),result['mode'],c['estimated_cost_usd'],c['baseline_cost_usd'],c['estimated_savings_usd'],result.get('budget_usd')))
    def summary(self):
        with get_connection() as conn:
            r=conn.execute('''SELECT count(*) AS cost_tracked_requests,coalesce(sum(estimated_cost_usd),0) AS estimated_cost_usd,coalesce(sum(baseline_cost_usd),0) AS baseline_cost_usd,coalesce(sum(estimated_savings_usd),0) AS estimated_savings_usd FROM request_metrics WHERE estimated_cost_usd IS NOT NULL''').fetchone()
        r.update(savings_percent=round(100*r['estimated_savings_usd']/r['baseline_cost_usd'],2) if r['baseline_cost_usd'] else 0,actual_api_cost_usd=0.,pricing_type='simulated'); return r
cost_analytics=CostAnalytics()
