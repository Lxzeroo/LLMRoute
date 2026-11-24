import httpx
from app.core.config import settings

class EmbeddingService:
    async def embed(self, text):
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(settings.ollama_base_url+'/api/embed', json={'model':settings.embedding_model,'input':text,'keep_alive':settings.model_keep_alive})
            r.raise_for_status()
            vector = r.json()['embeddings'][0]
            if len(vector)!=384: raise ValueError('Expected 384-dimensional embedding')
            return vector
embedding_service=EmbeddingService()
