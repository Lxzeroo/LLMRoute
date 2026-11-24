import httpx
import numpy as np

from app.core.config import settings


class EmbeddingService:

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embed",
                json={
                    "model": settings.embedding_model,
                    "input": text,
                    "keep_alive": settings.model_keep_alive
                }
            )

            response.raise_for_status()
            return response.json()["embeddings"][0]

    @staticmethod
    def cosine_similarity(vector_a, vector_b) -> float:
        a = np.asarray(vector_a, dtype=np.float32)
        b = np.asarray(vector_b, dtype=np.float32)

        if a.shape != b.shape:
            raise ValueError("Embedding dimensions do not match")

        denominator = np.linalg.norm(a) * np.linalg.norm(b)

        if denominator == 0:
            return 0.0

        return float(np.clip(np.dot(a, b) / denominator, -1.0, 1.0))


embedding_service = EmbeddingService()
