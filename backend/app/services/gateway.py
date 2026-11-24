import asyncio
import time

from app.core.config import settings
from app.services.semantic_cache import semantic_cache
from app.services.model_router import model_router
from app.services.inference import inference_service
from app.services.cost_engine import cost_engine
from app.services.cost_analytics import cost_analytics


class LLMGateway:

    def __init__(self):
        self.semaphore = asyncio.Semaphore(
            settings.max_concurrent_requests
        )

    async def process(
        self, query, mode="balanced", budget=None
    ):

        start = time.perf_counter()

        scope = f"v2:{mode}:{budget}"

        async with self.semaphore:

            cached = await semantic_cache.lookup(
                query, scope=scope
            )

            if cached["cache_hit"]:

                cache_type = cached["cache_type"]

                result = {
                    "query": query,
                    "answer": cached["answer"],
                    "source": f"{cache_type}_cache",
                    "cache_type": cache_type,
                    "cache_hit": True,
                    "similarity": cached["similarity"],
                    "matched_query": cached["matched_query"],
                    "cached_model": cached["cached_model"],
                    "model": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "inference_ms": 0
                }

            else:

                routing = model_router.route(
                    query, mode, budget
                )

                inference = await inference_service.generate(
                    query, routing["model"]
                )

                if inference["answer"].strip():

                    await asyncio.to_thread(
                        semantic_cache.store,
                        query,
                        inference["answer"],
                        cached["embedding"],
                        scope=scope,
                        model=routing["model"]
                    )

                result = {
                    "query": query,
                    **inference,
                    "source": "llm",
                    "cache_type": None,
                    "cache_hit": False,
                    "routing": routing
                }

            result["mode"] = mode
            result["budget_usd"] = budget

            result["cost"] = cost_engine.evaluate(result)

            result["budget_exceeded"] = (
                budget is not None
                and result["cost"]["estimated_cost_usd"] > budget
            )

            result["latency_ms"] = round(
                (time.perf_counter() - start) * 1000,
                2
            )

            await asyncio.to_thread(
                cost_analytics.record, result
            )

            result["total_processing_ms"] = round(
                (time.perf_counter() - start) * 1000,
                2
            )

            return result


llm_gateway = LLMGateway()
