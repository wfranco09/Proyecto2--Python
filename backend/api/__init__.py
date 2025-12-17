"""
API routers para rAIndrop backend
"""

from .health import router as health_router
from .stations import router as stations_router
from .predictions import router as predictions_router
from .pipelines import router as pipelines_router
from .risk import router as risk_router
from .ml import router as ml_router
from .incidents import router as incidents_router

__all__ = ["health_router", "stations_router", "predictions_router", "pipelines_router", "risk_router", "ml_router", "incidents_router"]
