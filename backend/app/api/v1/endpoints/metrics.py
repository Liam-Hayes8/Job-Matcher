from fastapi import APIRouter, Response
from app.services.metrics_service import get_metrics
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return Response(
            content="# Error retrieving metrics\n",
            media_type="text/plain"
        )