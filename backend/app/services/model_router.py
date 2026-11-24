import re

import psutil

from app.core.config import settings
from app.services.cost_engine import cost_engine


class RoutingError(Exception):
    pass


class ModelRouter:

    COMPLEX_KEYWORDS = {
        "analyze", "compare", "evaluate", "architecture",
        "implement", "debug", "optimize", "design",
        "algorithm", "reasoning", "derive", "prove",
        "vulnerability", "tradeoffs", "refactor"
    }

    def route(self, query, mode="balanced", budget=None):

        words = re.findall(r"\b\w+\b", query.lower())
        matched = set(words) & self.COMPLEX_KEYWORDS

        score = min(len(words) / 100, 0.4)
        score += len(matched) * 0.25

        if "step by step" in query.lower():
            score += 0.2

        if "```" in query:
            score += 0.3

        score = min(score, 1.0)

        ram = psutil.virtual_memory().available / (1024 ** 3)

        models = [
            {
                "model": settings.small_model,
                "tier": "lightweight",
                "min_ram": 2.0
            },
            {
                "model": "qwen2.5:3b",
                "tier": "balanced",
                "min_ram": 3.5
            },
            {
                "model": settings.large_model,
                "tier": "advanced",
                "min_ram": 6.5
            }
        ]

        if mode == "economy":
            preferred = 0

        elif mode == "performance":
            preferred = 2

        elif score >= 0.65:
            preferred = 2

        elif score >= 0.25:
            preferred = 1

        else:
            preferred = 0

        candidates = []

        for index, model in enumerate(models):

            estimate = cost_engine.estimate_request(
                query, model["model"]
            )

            candidates.append({
                **model,
                "index": index,
                "estimated_cost_usd": estimate,
                "memory_eligible": ram >= model["min_ram"],
                "budget_eligible": (
                    budget is None or estimate <= budget
                )
            })

        selected = None

        for candidate in reversed(candidates[:preferred + 1]):

            if (
                candidate["memory_eligible"]
                and candidate["budget_eligible"]
            ):
                selected = candidate
                break

        if selected is None:
            raise RoutingError(
                "No suitable model within memory and budget limits"
            )

        return {
            "model": selected["model"],
            "tier": selected["tier"],
            "mode": mode,
            "complexity_score": round(score, 3),
            "available_ram_gb": round(ram, 2),
            "estimated_cost_usd": selected["estimated_cost_usd"],
            "budget_usd": budget,
            "fallback_used": selected["index"] != preferred,
            "reason": (
                "Memory or budget-aware fallback"
                if selected["index"] != preferred
                else "Preferred model selected"
            ),
            "matched_keywords": sorted(matched),
            "candidates": candidates
        }


model_router = ModelRouter()
