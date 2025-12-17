"""
Pipeline para obtener pronósticos de 2 días de Meteosource (hoy y mañana).

Obtiene datos de forecast para cada estación y los guarda en la base de datos.
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path

from config import STATIONS

logger = logging.getLogger(__name__)

# API Key de Meteosource
METEOSOURCE_API_KEY = os.getenv("METEOSOURCE_API_KEY", "")
METEOSOURCE_BASE_URL = "https://www.meteosource.com/api/v1/free"


def fetch_forecast_for_station(station: Dict) -> Optional[List[Dict]]:
    """
    Obtiene pronóstico de 2 días para una estación específica (hoy y mañana).
    
    Args:
        station: Diccionario con datos de la estación (lat, lon, id, name)
        
    Returns:
        Lista de pronósticos diarios o None si falla
    """
    if not METEOSOURCE_API_KEY:
        logger.error(" METEOSOURCE_API_KEY no configurada")
        return None
    
    try:
        # Plan gratuito: usar lat/lon directamente, language='en'
        url = f"{METEOSOURCE_BASE_URL}/point"
        params = {
            "lat": station["lat"],
            "lon": station["lon"],
            "timezone": "UTC",
            "language": "en",  # Plan gratuito solo soporta inglés
            "units": "metric",
            "key": METEOSOURCE_API_KEY
        }
        
        logger.info(f" Obteniendo forecast para {station['name']} ({station['lat']}, {station['lon']})")
        
        response = requests.get(url, params=params, timeout=30)
        
        # Loggear respuesta de error para debugging
        if response.status_code != 200:
            logger.error(f" Error response: {response.text}")
        
        response.raise_for_status()
        
        data = response.json()
        
        # El plan gratuito solo devuelve datos "hourly", no "daily"
        # Necesitamos agrupar los datos horarios por día
        hourly_data = None
        if isinstance(data, dict) and "hourly" in data and data["hourly"] is not None:
            hourly_data = data["hourly"].get("data", [])
        
        if not hourly_data:
            logger.warning(f" No hay datos horarios para {station['name']}")
            return None
        
        # Agrupar datos horarios por día (agregando por fecha)
        from collections import defaultdict
        from datetime import date as date_module
        
        # Calcular hoy y mañana
        today = date_module.today().strftime('%Y-%m-%d')
        
        daily_aggregated = defaultdict(lambda: {
            'temps': [],
            'humidity': [],
            'wind_speed': [],
            'precipitation': [],
            'pressure': [],
            'cloud_cover': []
        })
        
        for hour_data in hourly_data[:48]:  # Solo 2 días * 24 horas = 48 horas
            date_str = hour_data.get('date', '')
            if not date_str:
                continue
            
            # Extraer solo la fecha (YYYY-MM-DD)
            forecast_date = date_str.split('T')[0]
            
            # Solo procesar desde hoy en adelante (excluir datos pasados)
            if forecast_date < today:
                continue
            
            # Agregar datos con validación estricta de tipos
            if 'temperature' in hour_data and isinstance(hour_data['temperature'], (int, float)):
                daily_aggregated[forecast_date]['temps'].append(hour_data['temperature'])
            
            if 'humidity' in hour_data and isinstance(hour_data['humidity'], (int, float)):
                daily_aggregated[forecast_date]['humidity'].append(hour_data['humidity'])
            
            if 'wind' in hour_data and isinstance(hour_data['wind'], dict) and 'speed' in hour_data['wind']:
                wind_speed = hour_data['wind']['speed']
                if isinstance(wind_speed, (int, float)):
                    daily_aggregated[forecast_date]['wind_speed'].append(wind_speed)
            
            if 'precipitation' in hour_data and isinstance(hour_data['precipitation'], dict) and 'total' in hour_data['precipitation']:
                precip_val = hour_data['precipitation']['total']
                if isinstance(precip_val, (int, float)):
                    daily_aggregated[forecast_date]['precipitation'].append(precip_val)
            
            if 'pressure' in hour_data and isinstance(hour_data['pressure'], (int, float)):
                daily_aggregated[forecast_date]['pressure'].append(hour_data['pressure'])
            
            if 'cloud_cover' in hour_data and isinstance(hour_data['cloud_cover'], (int, float)):
                daily_aggregated[forecast_date]['cloud_cover'].append(hour_data['cloud_cover'])
        
        # Formatear datos agregados - solo hoy y mañana (2 días)
        forecast_list = []
        for forecast_date in sorted(daily_aggregated.keys())[:2]:  # Solo 2 días: hoy y mañana
            day_data = daily_aggregated[forecast_date]
            
            # Calcular promedios y extremos
            temps = day_data['temps']
            humidity_vals = day_data['humidity']
            wind_vals = day_data['wind_speed']
            precip_vals = day_data['precipitation']
            pressure_vals = day_data['pressure']
            cloud_vals = day_data['cloud_cover']
            
            forecast_record = {
                "station_id": station["id"],
                "station_name": station["name"],
                "region": station.get("region", "Panama"),
                "latitude": station["lat"],
                "longitude": station["lon"],
                "elevation": station.get("elevation", 0),
                
                # Fecha del pronóstico
                "forecast_date": forecast_date,
                
                # Temperatura (max, min, promedio)
                "temp_max": max(temps) if temps else None,
                "temp_min": min(temps) if temps else None,
                "temp_avg": sum(temps) / len(temps) if temps else None,
                
                # Precipitación (suma del día)
                "precipitation_total": sum(precip_vals) if precip_vals else 0,
                "precipitation_probability": 100 if sum(precip_vals) > 0 else 0,  # Simplificado
                
                # Viento (máximo del día)
                "wind_speed_max": max(wind_vals) if wind_vals else None,
                "wind_direction": None,  # No disponible en agregación
                "wind_angle": None,
                
                # Humedad y presión (promedios)
                "humidity": sum(humidity_vals) / len(humidity_vals) if humidity_vals else 70.0,
                "pressure": sum(pressure_vals) / len(pressure_vals) if pressure_vals else None,
                
                # Nubosidad (promedio)
                "cloud_cover": sum(cloud_vals) / len(cloud_vals) if cloud_vals else None,
                
                # Descripción (simplificada)
                "summary": f"Precip: {sum(precip_vals):.1f}mm" if precip_vals else "Seco",
                "icon": "rain" if sum(precip_vals) > 5 else "partly_cloudy",
                
                # Metadata
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
            
            forecast_list.append(forecast_record)
        
        logger.info(f" ✓ {len(forecast_list)} días de forecast obtenidos para {station['name']}")
        return forecast_list
        
    except requests.exceptions.RequestException as e:
        logger.error(f" Error en request para {station['name']}: {e}")
        return None
    except Exception as e:
        logger.error(f" Error procesando forecast para {station['name']}: {e}")
        return None


def fetch_all_forecasts() -> List[Dict]:
    """
    Obtiene pronósticos para todas las estaciones configuradas.
    Se detiene después de 5 errores consecutivos (por ejemplo, límite de API excedido).
    
    Returns:
        Lista con todos los pronósticos
    """
    all_forecasts = []
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    logger.info(f" Iniciando obtención de forecasts para {len(STATIONS)} estaciones...")
    
    for station in STATIONS:
        forecast_data = fetch_forecast_for_station(station)
        
        if forecast_data:
            all_forecasts.extend(forecast_data)
            consecutive_errors = 0  # Resetear contador en caso de éxito
        else:
            consecutive_errors += 1
            logger.warning(f" No se obtuvo forecast para {station['name']} (error {consecutive_errors}/{max_consecutive_errors})")
            
            # Si alcanzamos el límite de errores consecutivos, parar el pipeline
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f" ✗ Límite de errores consecutivos alcanzado ({max_consecutive_errors}). Deteniendo pipeline.")
                logger.error(f" Probable causa: Límite de API excedido. Se reintentará en la próxima ejecución programada.")
                break
    
    logger.info(f" Total de pronósticos obtenidos: {len(all_forecasts)}")
    return all_forecasts


def calculate_risks_for_forecasts(forecasts: List[Dict]) -> List[Dict]:
    """
    Calcula los riesgos (inundación y sequía) para cada pronóstico.
    
    Args:
        forecasts: Lista de diccionarios con datos de forecast
        
    Returns:
        Lista de forecasts con campos de riesgo agregados
    """
    try:
        # Importar el predictor singleton
        from pathlib import Path
        from core.ml.risk_predictor import RiskPredictor
        
        model_path = Path(__file__).parent.parent.parent.parent / "ml_models" / "risk_model.joblib"
        
        if not model_path.exists():
            logger.warning(f" Modelo de riesgo no encontrado en {model_path}, usando valores por defecto")
            # Agregar valores por defecto
            for forecast in forecasts:
                forecast["flood_probability"] = 0.0
                forecast["flood_level"] = "GREEN"
                forecast["flood_alert"] = 0
                forecast["drought_probability"] = 0.0
                forecast["drought_level"] = "GREEN"
                forecast["drought_alert"] = 0
            return forecasts
        
        # Cargar modelo
        predictor = RiskPredictor(model_path=model_path)
        logger.info(f" Calculando riesgos para {len(forecasts)} pronósticos...")
        
        # Calcular riesgos para cada forecast
        for forecast in forecasts:
            try:
                # Preparar features del forecast
                features = {
                    'temperature': forecast.get('temperature', 0),
                    'humidity': forecast.get('humidity', 0),
                    'precipitation': forecast.get('precipitation', 0),
                    'wind_speed': forecast.get('wind_speed', 0),
                    'pressure': forecast.get('pressure', 1013.25),
                    'cloud_cover': forecast.get('cloud_cover', 0),
                    'uv_index': forecast.get('uv_index', 0),
                }
                
                # Predecir riesgo de inundación
                flood_risk = predictor.predict(features)
                forecast["flood_probability"] = flood_risk[1]  # probabilidad
                forecast["flood_level"] = flood_risk[0]  # nivel (GREEN, YELLOW, RED)
                forecast["flood_alert"] = 1 if flood_risk[0] in ["YELLOW", "RED"] else 0
                
                # Predecir riesgo de sequía (usando mismas features por ahora)
                drought_risk = predictor.predict(features)
                forecast["drought_probability"] = drought_risk[1]
                forecast["drought_level"] = drought_risk[0]
                forecast["drought_alert"] = 1 if drought_risk[0] in ["YELLOW", "RED"] else 0
                
            except Exception as e:
                logger.error(f" Error calculando riesgo para forecast de estación {forecast.get('station_id')}: {e}")
                # Valores por defecto en caso de error
                forecast["flood_probability"] = 0.0
                forecast["flood_level"] = "GREEN"
                forecast["flood_alert"] = 0
                forecast["drought_probability"] = 0.0
                forecast["drought_level"] = "GREEN"
                forecast["drought_alert"] = 0
        
        logger.info(f" Riesgos calculados exitosamente para {len(forecasts)} pronósticos")
        return forecasts
        
    except Exception as e:
        logger.error(f" Error general calculando riesgos: {e}")
        # Agregar valores por defecto a todos
        for forecast in forecasts:
            forecast["flood_probability"] = 0.0
            forecast["flood_level"] = "GREEN"
            forecast["flood_alert"] = 0
            forecast["drought_probability"] = 0.0
            forecast["drought_level"] = "GREEN"
            forecast["drought_alert"] = 0
        return forecasts


def save_forecasts_to_db(forecasts: List[Dict]) -> int:
    """
    Guarda pronósticos en la base de datos.
    
    Args:
        forecasts: Lista de diccionarios con datos de forecast
        
    Returns:
        Número de registros guardados
    """
    from core.database.raindrop_db import insert_or_update_forecast_data
    
    try:
        count = insert_or_update_forecast_data(forecasts)
        logger.info(f" {count} pronósticos guardados en la base de datos")
        return count
    except Exception as e:
        logger.error(f" Error guardando forecasts: {e}")
        return 0


def run():
    """
    Ejecuta el pipeline completo de forecasts.
    """
    try:
        logger.info("=" * 60)
        logger.info(" PIPELINE: FORECAST METEOSOURCE (2 DÍAS - HOY Y MAÑANA)")
        logger.info("=" * 60)
        
        # Obtener forecasts
        forecasts = fetch_all_forecasts()
        
        if not forecasts:
            logger.warning(" No se obtuvieron forecasts")
            return False
        
        # Calcular riesgos ANTES de guardar en DB
        logger.info(" Calculando riesgos para todos los pronósticos...")
        forecasts = calculate_risks_for_forecasts(forecasts)
        
        # Guardar en DB (ahora con riesgos pre-calculados)
        saved = save_forecasts_to_db(forecasts)
        
        if saved > 0:
            logger.info(f" Pipeline completado exitosamente: {saved} pronósticos guardados con riesgos")
            return True
        else:
            logger.warning(" No se guardaron pronósticos")
            return False
            
    except Exception as e:
        logger.error(f" Error en pipeline de forecast: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run()
