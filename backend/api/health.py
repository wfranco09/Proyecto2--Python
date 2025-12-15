"""
API router para health checks
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def health_status():
    """Status de salud de la API."""
    return {
        "status": "healthy",
        "service": "rAIndrop Backend",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness():
    """Verifica si el backend está listo para servir requests."""
    return {
        "ready": True,
        "message": "Backend operacional"
    }
