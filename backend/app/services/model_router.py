import re
import psutil

from app.core.config import settings


class ModelRouter:

    COMPLEX_KEYWORDS = {
        "analyze", "compare", "evaluate", "architecture",
        "implement", "debug", "optimize", "design",
        "algorithm", "reasoning", "derive", "prove",
        "vulnerability", "tradeoffs", "refactor"
    }

    def route(self, query: str) -> dict:

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

        if score >= 0.65 and ram >= 6.5:
            model = settings.large_model
            tier = "advanced"
            reason = "High complexity with sufficient memory"

        elif score >= 0.25 and ram >= 3.5:
            model = "qwen2.5:3b"
            tier = "balanced"
            reason = "Balanced reasoning and memory efficiency"

        else:
            model = settings.small_model
            tier = "lightweight"
            reason = (
                "Low complexity query"
                if score < 0.25
                else "Memory-aware lightweight fallback"
            )

        return {
            "model": model,
            "tier": tier,
            "complexity_score": round(score, 3),
            "reason": reason,
            "available_ram_gb": round(ram, 2),
            "memory_warning": ram < 2.0,
            "matched_keywords": sorted(matched)
        }


model_router = ModelRouter()
