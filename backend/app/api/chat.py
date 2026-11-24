from typing import Literal

import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gateway import llm_gateway
from app.services.model_router import model_router, RoutingError
from app.services.semantic_cache import semantic_cache
from app.services.cost_engine import MODEL_PRICING
from app.services.cost_analytics import cost_analytics


router = APIRouter(prefix="/api", tags=["LLM Gateway"])


class ChatRequest(BaseModel):

    query: str = Field(
        min_length=1, max_length=4000
    )

    mode: Literal[
        "economy", "balanced", "performance"
    ] = "balanced"

    budget_usd: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False
    )


@router.post("/chat")
async def chat(request: ChatRequest):

    if not request.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    try:
        return await llm_gateway.process(
            request.query.strip(),
            request.mode,
            request.budget_usd
        )

    except RoutingError as error:
        raise HTTPException(422, str(error))

    except httpx.TimeoutException:
        raise HTTPException(504, "Model inference timed out")

    except httpx.HTTPError:
        raise HTTPException(502, "Ollama request failed")


@router.post("/route")
def route_query(request: ChatRequest):

    try:
        return model_router.route(
            request.query,
            request.mode,
            request.budget_usd
        )

    except RoutingError as error:
        raise HTTPException(422, str(error))


@router.get("/stats")
def stats():
    return semantic_cache.stats()


@router.get("/pricing")
def pricing():
    return {
        "currency": "USD",
        "unit": "per million tokens",
        "pricing_type": "simulated",
        "models": MODEL_PRICING
    }


@router.get("/analytics/costs")
def costs():
    return cost_analytics.summary()
