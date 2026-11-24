import os

import httpx
import psutil
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

app = FastAPI(
    title="LLMRoute",
    description="Intelligent LLM routing and semantic caching gateway",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {
        "name": "LLMRoute",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    memory = psutil.virtual_memory()

    return {
        "status": "healthy",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": memory.percent,
            "available_ram_gb": round(
                memory.available / (1024 ** 3), 2
            ),
            "total_ram_gb": round(
                memory.total / (1024 ** 3), 2
            )
        }
    }


@app.get("/health/ollama")
async def ollama_health():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OLLAMA_URL}/api/tags"
            )
            response.raise_for_status()

            models = response.json().get("models", [])
            installed = [model["name"] for model in models]

            required = [
                os.getenv("SMALL_MODEL"),
                os.getenv("LARGE_MODEL"),
                os.getenv("EMBEDDING_MODEL")
            ]

            missing = [
                model for model in required
                if model and model not in installed
            ]

            return {
                "status": "connected",
                "installed_models": installed,
                "missing_models": missing,
                "ready": not missing
            }

    except httpx.HTTPError as error:
        return {
            "status": "disconnected",
            "ready": False,
            "error": str(error)
        }

from app.api.chat import router as chat_router

app.include_router(chat_router)

from fastapi import HTTPException
from app.core.database import check_database


@app.get("/health/db")
def database_health():
    try:
        result = check_database()

        return {
            "status": "connected",
            **result
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

from app.api.analytics import router as analytics_router

app.include_router(analytics_router)
