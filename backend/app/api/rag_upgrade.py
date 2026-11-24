from typing import Literal
from uuid import UUID
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.rag_upgrade import ask
from app.services.model_router import RoutingError
router=APIRouter(prefix='/api/rag-v2',tags=['Optimized RAG'])
class Request(BaseModel):
    query:str=Field(min_length=1,max_length=1000)
    document_ids:list[UUID]=Field(min_length=1,max_length=10)
    mode:Literal['economy','balanced','performance']='balanced'
    budget_usd:float|None=Field(default=None,ge=0,allow_inf_nan=False)
    top_k:int=Field(default=3,ge=1,le=3)
    bypass_cache:bool=False
@router.post('/ask')
async def question(request:Request):
    try:
        return await ask(request.query,[str(x) for x in request.document_ids],request.mode,request.budget_usd,request.top_k,request.bypass_cache)
    except ValueError as e: raise HTTPException(400,str(e)) from e
    except RoutingError as e: raise HTTPException(422,str(e)) from e
    except httpx.TimeoutException as e: raise HTTPException(504,'Ollama timed out') from e
    except httpx.HTTPError as e: raise HTTPException(502,'Ollama request failed') from e
