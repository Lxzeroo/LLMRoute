import math

from app.core.config import settings


MODEL_PRICING = {
    settings.small_model: {
        "input": 0.05,
        "output": 0.10
    },
    "qwen2.5:3b": {
        "input": 0.15,
        "output": 0.30
    },
    settings.large_model: {
        "input": 0.50,
        "output": 1.00
    }
}


class CostEngine:

    @staticmethod
    def estimate_tokens(text):
        return max(1, math.ceil(len(text.encode("utf-8")) / 4))

    def calculate(self, model, input_tokens, output_tokens):
        pricing = MODEL_PRICING[model]

        return round(
            (
                input_tokens * pricing["input"]
                + output_tokens * pricing["output"]
            ) / 1_000_000,
            10
        )

    def estimate_request(self, query, model):
        input_tokens = self.estimate_tokens(query) + 64

        return self.calculate(
            model,
            input_tokens,
            settings.max_output_tokens
        )

    def evaluate(self, result):
        if result["cache_hit"]:
            input_tokens = self.estimate_tokens(
                result["query"]
            ) + 64

            output_tokens = self.estimate_tokens(
                result["answer"]
            )

            cost = 0.0

        else:
            input_tokens = result["input_tokens"]
            output_tokens = result["output_tokens"]

            cost = self.calculate(
                result["model"],
                input_tokens,
                output_tokens
            )

        baseline = self.calculate(
            settings.large_model,
            input_tokens,
            output_tokens
        )

        savings = max(0.0, baseline - cost)

        return {
            "estimated_cost_usd": cost,
            "baseline_cost_usd": baseline,
            "estimated_savings_usd": round(savings, 10),
            "savings_percent": round(
                savings / baseline * 100, 2
            ) if baseline else 0.0,
            "actual_api_cost_usd": 0.0,
            "pricing_type": "simulated"
        }


cost_engine = CostEngine()
