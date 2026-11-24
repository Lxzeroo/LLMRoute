from fastapi import APIRouter, Query

from app.services.analytics import analytics_service


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


@router.get("/summary")
def summary():
    return analytics_service.summary()


@router.get("/history")
def history(limit: int = Query(50, ge=1, le=500)):
    return analytics_service.history(limit)


@router.get("/models")
def models():
    return analytics_service.model_usage()
