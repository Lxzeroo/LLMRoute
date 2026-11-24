import httpx
import psutil
from fastapi import FastAPI,HTTPException
from app.core.config import settings
from app.core.database import check_database
from app.api import chat,analytics,documents,rag_upgrade
app=FastAPI(title=settings.app_name,version=settings.app_version)
for module in (chat,analytics,documents,rag_upgrade): app.include_router(module.router)
@app.get('/')
def root(): return dict(name=settings.app_name,version=settings.app_version,status='running')
@app.get('/health')
def health():
    m=psutil.virtual_memory(); return dict(status='healthy',system=dict(cpu_percent=psutil.cpu_percent(),memory_percent=m.percent,available_ram_gb=round(m.available/2**30,2),total_ram_gb=round(m.total/2**30,2)))
@app.get('/health/db')
def db():
    try: return dict(status='connected',**check_database())
    except Exception as e: raise HTTPException(503,'Database connection failed') from e
@app.get('/health/ollama')
async def ollama():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r=await client.get(settings.ollama_base_url+'/api/tags'); r.raise_for_status()
        installed=[m['name'] for m in r.json()['models']]; missing=[m for m in (settings.small_model,settings.medium_model,settings.large_model,settings.embedding_model) if m not in installed]
        return dict(status='connected',installed_models=installed,missing_models=missing,ready=not missing)
    except httpx.HTTPError as e: raise HTTPException(503,'Ollama unavailable') from e
