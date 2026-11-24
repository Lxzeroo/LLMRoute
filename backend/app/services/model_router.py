import re
import psutil
from app.core.config import settings
from app.services.cost_engine import cost_engine
class RoutingError(Exception): pass
class ModelRouter:
    def route(self,query,mode='balanced',budget=None):
        words=re.findall(r'\b\w+\b',query.lower()); matched=set(words)&set('analyze compare evaluate architecture implement debug optimize design algorithm reasoning derive prove vulnerability tradeoffs refactor'.split())
        score=min(1,min(len(words)/100,.4)+len(matched)*.25+(.2 if 'step by step' in query.lower() else 0)+(.3 if '```' in query else 0))
        ram=psutil.virtual_memory().available/2**30
        preferred=0 if mode=='economy' else 2 if mode=='performance' or score>=.65 else 1 if score>=.25 else 0
        candidates=[]
        for i,(model,tier,minimum) in enumerate(zip([settings.small_model,settings.medium_model,settings.large_model],['lightweight','balanced','advanced'],[2,3.5,6.5])):
            estimate=cost_engine.estimate_request(query,model)
            candidates.append(dict(model=model,tier=tier,min_ram=minimum,index=i,estimated_cost_usd=estimate,memory_eligible=ram>=minimum,budget_eligible=budget is None or estimate<=budget))
        chosen=next((c for c in reversed(candidates[:preferred+1]) if c['memory_eligible'] and c['budget_eligible']),None)
        if chosen is None: raise RoutingError('No suitable model within memory and budget limits')
        return dict(model=chosen['model'],tier=chosen['tier'],mode=mode,complexity_score=round(score,3),available_ram_gb=round(ram,2),estimated_cost_usd=chosen['estimated_cost_usd'],budget_usd=budget,fallback_used=chosen['index']!=preferred,reason='Memory or budget-aware fallback' if chosen['index']!=preferred else 'Preferred model selected',matched_keywords=sorted(matched),candidates=candidates)
model_router=ModelRouter()
