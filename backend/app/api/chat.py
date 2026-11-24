from typing import Literal
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.gateway import llm_gateway
from app.services.model_router import model_router,RoutingError
from app.services.semantic_cache import semantic_cache
from app.services.cost_engine import MODEL_PRICING
router=APIRouter(prefix='/api',tags=['Gateway'])
class ChatRequest(BaseModel):
    query:str=Field(min_length=1,max_length=4000)
    mode:Literal['economy','balanced','performance']='balanced'
    budget_usd:float|None=Field(default=None,ge=0,allow_inf_nan=False)
@router.post('/chat')
async def chat(r:ChatRequest):
    if not r.query.strip(): raise HTTPException(400,'Question cannot be empty')
    try: return await llm_gateway.process(r.query.strip(),r.mode,r.budget_usd)
    except RoutingError as e: raise HTTPException(422,str(e)) from e
    except httpx.TimeoutException as e: raise HTTPException(504,'Ollama timed out') from e
    except httpx.HTTPError as e: raise HTTPException(502,'Ollama request failed') from e
@router.post('/route')
def route(r:ChatRequest):
    if not r.query.strip(): raise HTTPException(400,'Question cannot be empty')
    try: return model_router.route(r.query,r.mode,r.budget_usd)
    except RoutingError as e: raise HTTPException(422,str(e)) from e
@router.get('/pricing')
def pricing(): return dict(currency='USD',unit='per million tokens',pricing_type='simulated',models=MODEL_PRICING)
@router.get('/stats')
def stats(): return semantic_cache.stats()
