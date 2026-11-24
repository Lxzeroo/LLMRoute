import math
from app.core.config import settings
MODEL_PRICING={settings.small_model:{'input':.05,'output':.1},settings.medium_model:{'input':.15,'output':.3},settings.large_model:{'input':.5,'output':1.0}}
class CostEngine:
    def estimate_tokens(self,text): return max(1,math.ceil(len(text.encode())/4))
    def calculate(self,model,input_tokens,output_tokens):
        p=MODEL_PRICING[model]; return round((input_tokens*p['input']+output_tokens*p['output'])/1e6,10)
    def estimate_request(self,query,model): return self.calculate(model,self.estimate_tokens(query)+64,settings.max_output_tokens)
    def evaluate(self,result):
        if result['cache_hit']:
            a=self.estimate_tokens(result['query'])+64; b=self.estimate_tokens(result['answer']); cost=0.
        else:
            a=result['input_tokens']; b=result['output_tokens']; cost=self.calculate(result['model'],a,b)
        baseline=self.calculate(settings.large_model,a,b); savings=baseline-cost
        return dict(estimated_cost_usd=cost,baseline_cost_usd=baseline,estimated_savings_usd=round(savings,10),savings_percent=round(100*savings/baseline,2) if baseline else 0,actual_api_cost_usd=0.,pricing_type='simulated')
cost_engine=CostEngine()
