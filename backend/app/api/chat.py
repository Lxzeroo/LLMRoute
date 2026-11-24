import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gateway import llm_gateway
from app.services.model_router import model_router
from app.services.semantic_cache import semantic_cache


router = APIRouter(prefix="/api", tags=["LLM Gateway"])


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


@router.post("/chat")
async def chat(request: ChatRequest):

    if not request.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    try:
        return await llm_gateway.process(request.query.strip())

    except httpx.TimeoutException:
        raise HTTPException(504, "Model inference timed out")

    except httpx.HTTPError:
        raise HTTPException(502, "Ollama request failed")


@router.post("/route")
async def route_query(request: ChatRequest):
    return model_router.route(request.query)


@router.get("/stats")
async def stats():
    return semantic_cache.stats()
