"""
rAIndrop Backend - FastAPI Server
Servidor para servir datos de predicción de riesgos climáticos
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from core.scheduler import start_scheduler, stop_scheduler
from core.database.raindrop_db import init_database
from api import health_router, stations_router, predictions_router, pipelines_router, risk_router, ml_router, incidents_router
from api.forecast import router as forecast_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables globales para el ciclo de vida de la app
scheduler_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación."""
    # Inicio
    logger.info(" Iniciando rAIndrop Backend...")
    
    # Inicializar base de datos
    logger.info(" Inicializando base de datos...")
    init_database()
    logger.info(" Base de datos inicializada")
    
    # Ejecutar pipeline de pronósticos inmediatamente al inicio (en thread separado)
    logger.info(" Iniciando generación de pronósticos en segundo plano...")
    try:
        from core.scheduler import execute_forecast_now
        execute_forecast_now()
        logger.info(" Pipeline de pronósticos iniciado (ejecutando en segundo plano)")
    except Exception as e:
        logger.error(f" Error iniciando pipeline de pronósticos: {e}")
    
    # Iniciar scheduler
    start_scheduler()
    logger.info(" Scheduler iniciado:")
    logger.info("   - Pipeline de datos: cada hora")
    logger.info("   - Pipeline de pronósticos: cada 6 horas (0, 6, 12, 18)")
    logger.info("   - Entrenamiento ML: diario a las 2:00 AM")
    
    yield
    
    # Shutdown
    logger.info(" Deteniendo rAIndrop Backend...")
    stop_scheduler()
    logger.info(" Scheduler detenido")


# Crear app FastAPI
app = FastAPI(
    title="rAIndrop API",
    description="Sistema de Predicción de Riesgos Climáticos en Panamá",
    version="1.0.0",
    lifespan=lifespan
)

# Agregar CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las orígenes (incluye localhost:3000 del frontend)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(stations_router, prefix="/api/stations", tags=["Stations"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(pipelines_router, tags=["Pipelines"])
app.include_router(risk_router, tags=["Risk Analysis"])
app.include_router(ml_router, tags=["Machine Learning"])
app.include_router(incidents_router, prefix="/api/incidents", tags=["Incident Reports"])
app.include_router(forecast_router, prefix="/api", tags=["Forecast"])


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "rAIndrop API v1.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Ejecutar servidor con hot-reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
