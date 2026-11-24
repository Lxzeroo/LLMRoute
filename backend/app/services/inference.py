import httpx

from app.core.config import settings


class InferenceService:

    async def generate(self, query: str, model: str) -> dict:

        async with httpx.AsyncClient(timeout=300.0) as client:

            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": query,
                    "system": (
                        "You are a helpful and accurate AI assistant. "
                        "Provide clear answers. "
                        "Do not invent facts."
                    ),
                    "stream": False,
                    "keep_alive": settings.model_keep_alive,
                    "options": {
                        "temperature": settings.temperature,
                        "num_ctx": settings.context_window,
                        "num_predict": settings.max_output_tokens
                    }
                }
            )

            response.raise_for_status()
            data = response.json()

            return {
                "answer": data["response"],
                "model": model,
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
                "inference_ms": round(
                    data.get("total_duration", 0) / 1_000_000, 2
                ),
                "load_ms": round(
                    data.get("load_duration", 0) / 1_000_000, 2
                )
            }


inference_service = InferenceService()
