"""
API router para pronósticos y predicciones de riesgo a 7 días.
"""

import logging
import subprocess
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from core.database.raindrop_db import get_forecast_by_station, get_all_forecasts
from services import Predictor
from config import STATIONS
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# Instancia global del modelo ML (se carga una sola vez)
_risk_predictor_instance = None

# Caché simple para almacenar forecasts procesados (5 minutos de TTL)
_forecast_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 300  # 5 minutos
}

def get_risk_predictor():
    """Obtiene una instancia singleton del RiskPredictor."""
    global _risk_predictor_instance
    if _risk_predictor_instance is None:
        from core.ml.risk_predictor import RiskPredictor
        from pathlib import Path
        model_path = Path(__file__).parent.parent / "ml_models" / "risk_model.joblib"
        if model_path.exists():
            _risk_predictor_instance = RiskPredictor(model_path=model_path)
            logger.info(f"✅ Modelo ML cargado una vez (singleton): {model_path}")
        else:
            _risk_predictor_instance = RiskPredictor()
            logger.warning("⚠️ Modelo ML no encontrado, usando predictor sin modelo")
    return _risk_predictor_instance

def get_cached_forecasts():
    """Obtiene forecasts del caché si aún es válido."""
    current_time = time.time()
    if _forecast_cache["data"] and (current_time - _forecast_cache["timestamp"]) < _forecast_cache["ttl"]:
        logger.info("⚡ Usando forecasts desde caché")
        return _forecast_cache["data"]
    return None

def set_cached_forecasts(data):
    """Almacena forecasts en el caché."""
    _forecast_cache["data"] = data
    _forecast_cache["timestamp"] = time.time()
    logger.info("💾 Forecasts almacenados en caché (válido por 5 min)")


def run_forecast_pipeline_background():
    """
    Ejecuta el pipeline de forecast en segundo plano si es necesario.
    """
    try:
        logger.info("Ejecutando pipeline de forecast en segundo plano...")
        result = subprocess.run(
            ["python", "-m", "core.pipelines.etl.meteosource.forecast_pipeline"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        if result.returncode == 0:
            logger.info("Pipeline de forecast completado exitosamente")
        else:
            logger.error(f"Pipeline de forecast falló: {result.stderr}")
    except Exception as e:
        logger.error(f"Error ejecutando pipeline de forecast: {e}")


def get_risk_from_forecast_data(forecast_data: dict) -> dict:
    """
    Obtiene los riesgos PRE-CALCULADOS desde los datos del forecast.
    Ya no calcula en tiempo real, solo lee los valores de la BD.
    
    Args:
        forecast_data: Datos del pronóstico (ya incluye risk fields de la BD)
        
    Returns:
        Diccionario con probabilidades y niveles de riesgo
    """
    return {
        "flood_risk": {
            "probability": round(float(forecast_data.get("flood_probability", 0.0)), 3),
            "level": forecast_data.get("flood_level", "GREEN"),
            "alert": bool(forecast_data.get("flood_alert", 0)),
        },
        "drought_risk": {
            "probability": round(float(forecast_data.get("drought_probability", 0.0)), 3),
            "level": forecast_data.get("drought_level", "GREEN"),
            "alert": bool(forecast_data.get("drought_alert", 0)),
        },
        "conditions": {
            "temperature": forecast_data.get("temperature"),
            "humidity": forecast_data.get("humidity"),
            "precipitation": forecast_data.get("precipitation_total"),
            "wind_speed": forecast_data.get("wind_speed_max"),
        }
    }


def calculate_risk_from_forecast(forecast_data: dict) -> dict:
    """
    DEPRECATED: Usa get_risk_from_forecast_data() en su lugar.
    Esta función se mantiene solo como fallback si los datos pre-calculados no existen.
    
    Calcula riesgos de inundación y sequía basado en datos de pronóstico.
    Usa el modelo ML entrenado para predicciones precisas.
    
    Args:
        forecast_data: Datos del pronóstico
        
    Returns:
        Diccionario con probabilidades y niveles de riesgo
    """
    try:
        # Usar instancia singleton del modelo ML
        predictor = get_risk_predictor()
        return predictor.predict_from_forecast(forecast_data)
    except Exception as e:
        logger.warning(f"No se pudo usar modelo ML, usando cálculo simple: {e}")
        
        # Fallback: cálculo simple si el modelo no está disponible
        predictor = Predictor()
        
        rainfall = float(forecast_data.get("precipitation_total") or 0.0)
        humidity = float(forecast_data.get("humidity") or 0.0)
        temp_avg = float(forecast_data.get("temp_avg") or 25.0)
        wind_speed = float(forecast_data.get("wind_speed_max") or 0.0)
        
        flood_prob = min(0.95, (rainfall / 50.0) * 0.6 + (humidity / 100.0) * 0.4)
        flood_level = predictor._get_risk_level(flood_prob)
        
        drought_prob = min(0.95, (1 - rainfall / 50.0) * 0.6 + (1 - humidity / 100.0) * 0.4)
        drought_level = predictor._get_risk_level(drought_prob)
        
        return {
            "flood_risk": {
                "probability": round(flood_prob, 3),
                "level": flood_level,
                "alert": flood_prob >= 0.5,
            },
            "drought_risk": {
                "probability": round(drought_prob, 3),
                "level": drought_level,
                "alert": drought_prob >= 0.5,
            },
            "conditions": {
                "temperature": temp_avg,
                "humidity": humidity,
                "rainfall": rainfall,
                "wind_speed": wind_speed,
            }
        }


@router.get("/forecast/summary")
async def get_forecast_summary(
    background_tasks: BackgroundTasks,
    days: int = Query(default=7, ge=1, le=7)
):
    """
    Obtiene un resumen de alertas de riesgo para los próximos días.
    Si no hay datos disponibles, ejecuta el pipeline automáticamente.
    
    Returns:
        Resumen con conteo de estaciones en riesgo por día
    """
    try:
        all_forecasts = get_all_forecasts(days)
        
        if not all_forecasts:
            # Ejecutar pipeline en segundo plano
            background_tasks.add_task(run_forecast_pipeline_background)
            return {
                "forecast_days": 0,
                "total_stations": 0,
                "daily_summary": [],
                "message": "Generando pronósticos en segundo plano..."
            }
        
        # Crear resumen por día
        daily_summary = {}
        
        for station_id, forecasts in all_forecasts.items():
            for day_forecast in forecasts:
                date = day_forecast.get("forecast_date")
                
                if date not in daily_summary:
                    daily_summary[date] = {
                        "date": date,
                        "flood_alerts": 0,
                        "drought_alerts": 0,
                        "high_flood_risk": 0,
                        "high_drought_risk": 0,
                    }
                
                # Leer riesgos pre-calculados (ya no calcular)
                risk_data = get_risk_from_forecast_data(day_forecast)
                
                if risk_data["flood_risk"]["alert"]:
                    daily_summary[date]["flood_alerts"] += 1
                if risk_data["drought_risk"]["alert"]:
                    daily_summary[date]["drought_alerts"] += 1
                
                if risk_data["flood_risk"]["level"] == "RED":
                    daily_summary[date]["high_flood_risk"] += 1
                if risk_data["drought_risk"]["level"] == "RED":
                    daily_summary[date]["high_drought_risk"] += 1
        
        # Convertir a lista ordenada
        summary_list = sorted(daily_summary.values(), key=lambda x: x["date"])
        
        return {
            "forecast_days": len(summary_list),
            "total_stations": len(all_forecasts),
            "daily_summary": summary_list,
        }
        
    except Exception as e:
        logger.error(f"Error generando resumen de forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{station_id}")
async def get_station_forecast(
    station_id: int,
    background_tasks: BackgroundTasks,
    days: int = Query(default=7, ge=1, le=7, description="Número de días (1-7)")
):
    """
    Obtiene pronóstico de riesgo para una estación específica.
    Si no hay datos disponibles, ejecuta el pipeline automáticamente.
    
    Args:
        station_id: ID de la estación
        days: Número de días de pronóstico (1-7)
        
    Returns:
        Pronóstico con predicciones de riesgo para cada día
    """
    try:
        # Verificar que la estación existe
        station = next((s for s in STATIONS if s["id"] == station_id), None)
        if not station:
            raise HTTPException(status_code=404, detail=f"Estación {station_id} no encontrada")
        
        # Obtener datos de forecast
        forecast_data = get_forecast_by_station(station_id, days)
        
        if not forecast_data:
            # Ejecutar pipeline en segundo plano y devolver mensaje
            background_tasks.add_task(run_forecast_pipeline_background)
            raise HTTPException(
                status_code=202,
                detail="No hay pronósticos disponibles. Generando pronósticos en segundo plano. Intenta de nuevo en unos momentos."
            )
        
        # Leer riesgos pre-calculados (ya no usar modelo ML en tiempo real)
        forecast_with_risks = []
        for day_forecast in forecast_data:
            risk_data = get_risk_from_forecast_data(day_forecast)
            
            forecast_with_risks.append({
                "date": day_forecast.get("forecast_date"),
                "day_of_week": day_forecast.get("forecast_date"),  # Puedes agregar lógica para nombre del día
                "flood_risk": risk_data["flood_risk"],
                "drought_risk": risk_data["drought_risk"],
                "conditions": risk_data["conditions"],
                "summary": day_forecast.get("summary"),
                "icon": day_forecast.get("icon"),
                "precipitation_probability": day_forecast.get("precipitation_probability"),
            })
        
        return {
            "station_id": station_id,
            "station_name": station.get("name"),
            "location": {
                "lat": station.get("lat"),
                "lon": station.get("lon"),
                "elevation": station.get("elevation"),
            },
            "forecast_days": len(forecast_with_risks),
            "forecast": forecast_with_risks,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo forecast para estación {station_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
async def get_all_stations_forecast(
    background_tasks: BackgroundTasks,
    days: int = Query(default=7, ge=1, le=7, description="Número de días (1-7)")
):
    """
    Obtiene pronóstico de riesgo para todas las estaciones.
    Si no hay datos disponibles, ejecuta el pipeline automáticamente.
    
    Args:
        days: Número de días de pronóstico (1-7)
        
    Returns:
        Pronósticos con predicciones de riesgo para todas las estaciones
    """
    try:
        import time
        start_time = time.time()
        
        # Intentar obtener del caché primero
        cached_data = get_cached_forecasts()
        if cached_data:
            elapsed = time.time() - start_time
            logger.info(f"⚡ Forecast servido desde caché en {elapsed:.2f}s")
            return cached_data
        
        logger.info("🔄 Procesando forecasts (no en caché)...")
        
        # Obtener todos los forecasts
        all_forecasts = get_all_forecasts(days)
        
        if not all_forecasts:
            # Ejecutar pipeline en segundo plano y devolver mensaje
            background_tasks.add_task(run_forecast_pipeline_background)
            raise HTTPException(
                status_code=202,
                detail="No hay pronósticos disponibles. Generando pronósticos en segundo plano. Intenta de nuevo en unos momentos."
            )
        
        # Procesar estaciones en paralelo con ThreadPoolExecutor
        def process_station(station):
            """Procesa una estación individual."""
            station_id = station["id"]
            forecast_data = all_forecasts.get(station_id, [])
            
            if not forecast_data:
                return None
            
            # Leer riesgos pre-calculados (ya no calcular en tiempo real)
            forecast_with_risks = []
            for day_forecast in forecast_data:
                risk_data = get_risk_from_forecast_data(day_forecast)
                
                forecast_with_risks.append({
                    "date": day_forecast.get("forecast_date"),
                    "day_of_week": day_forecast.get("forecast_date"),
                    "flood_risk": risk_data["flood_risk"],
                    "drought_risk": risk_data["drought_risk"],
                    "conditions": risk_data["conditions"],
                    "summary": day_forecast.get("summary"),
                    "icon": day_forecast.get("icon"),
                    "precipitation_probability": day_forecast.get("precipitation_probability"),
                })
            
            return (station_id, {
                "station_id": station_id,
                "station_name": station.get("name"),
                "location": {
                    "lat": station.get("lat"),
                    "lon": station.get("lon"),
                    "elevation": station.get("elevation", 0),
                },
                "forecast_days": len(forecast_with_risks),
                "forecast": forecast_with_risks,
            })
        
        stations_forecast = {}
        
        # Usar ThreadPoolExecutor para procesamiento paralelo (hasta 20 threads para más rapidez)
        with ThreadPoolExecutor(max_workers=20) as executor:
            # Enviar todas las estaciones al pool
            future_to_station = {executor.submit(process_station, station): station for station in STATIONS}
            
            # Recoger resultados a medida que se completan
            for future in as_completed(future_to_station):
                try:
                    result = future.result()
                    if result:
                        station_id, station_data = result
                        stations_forecast[station_id] = station_data
                except Exception as e:
                    station = future_to_station[future]
                    logger.error(f"Error procesando estación {station.get('name')}: {e}")
        
        # Guardar en caché antes de devolver
        set_cached_forecasts(stations_forecast)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Forecast procesado y cacheado en {elapsed:.2f}s ({len(stations_forecast)} estaciones)")
        
        return stations_forecast
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo forecasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
