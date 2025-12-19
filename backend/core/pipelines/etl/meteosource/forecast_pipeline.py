"""
Pipeline para obtener pronósticos de 2 días de Meteosource (hoy y mañana).

Obtiene datos de forecast para cada estación y los guarda en la base de datos.
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone, date
from typing import List, Dict, Optional
from pathlib import Path

from config import STATIONS

logger = logging.getLogger(__name__)

# API Key de Meteosource
METEOSOURCE_API_KEY = os.getenv("METEOSOURCE_API_KEY", "")
METEOSOURCE_BASE_URL = "https://www.meteosource.com/api/v1/free"

# Archivo para rastrear estado de la API (5 niveles arriba: forecast_pipeline -> meteosource -> etl -> pipelines -> core -> backend)
API_STATE_FILE = Path(__file__).parent.parent.parent.parent.parent / "cache" / "api_state.json"


def get_api_state() -> Dict:
    """Lee el estado de la API desde el archivo cache."""
    if API_STATE_FILE.exists():
        try:
            with open(API_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"last_success": None, "consecutive_failures": 0, "last_attempt_date": None}


def save_api_state(state: Dict):
    """Guarda el estado de la API en el archivo cache."""
    try:
        API_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(API_STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logger.warning(f"No se pudo guardar estado de API: {e}")


def should_attempt_api() -> bool:
    """
    Determina si debemos intentar llamar a la API.
    Después de 10 fallos consecutivos en el mismo día, usa solo datos simulados.
    """
    state = get_api_state()
    today = str(date.today())
    
    # Si es un nuevo día, resetear el contador
    if state.get("last_attempt_date") != today:
        return True
    
    # Si ya fallamos 10 veces hoy, no intentar más
    if state.get("consecutive_failures", 0) >= 10:
        logger.warning(f" Límite de fallos alcanzado hoy ({state['consecutive_failures']}). Usando solo datos simulados.")
        return False
    
    return True


def record_api_result(success: bool):
    """Registra el resultado de un intento de API."""
    state = get_api_state()
    today = str(date.today())
    
    if success:
        state["last_success"] = today
        state["consecutive_failures"] = 0
        logger.info(f" ✅ API exitosa - reseteando contador de fallos")
    else:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        logger.debug(f" Fallo {state['consecutive_failures']} registrado en {API_STATE_FILE}")
    
    state["last_attempt_date"] = today
    save_api_state(state)


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


def generate_simulated_forecast(station: Dict, forecast_date: str) -> Dict:
    """
    Genera datos simulados de forecast para demostración cuando la API no está disponible.
    Usa variaciones realistas basadas en datos climáticos de Panamá.
    
    Args:
        station: Diccionario con datos de la estación
        forecast_date: Fecha del forecast (YYYY-MM-DD)
        
    Returns:
        Diccionario con datos de forecast simulados
    """
    import random
    from datetime import datetime
    
    # Semilla basada en station_id y fecha para consistencia
    random.seed(station['id'] * 1000 + int(forecast_date.replace('-', '')))
    
    # Valores base típicos de Panamá
    base_temp = 27.0 + random.uniform(-3, 3)  # 24-30°C
    base_humidity = 75.0 + random.uniform(-10, 10)  # 65-85%
    base_pressure = 1013.0 + random.uniform(-5, 5)  # 1008-1018 hPa
    
    # Precipitación: algunos días con lluvia, otros secos
    if random.random() > 0.4:  # 60% probabilidad de lluvia
        precipitation = random.uniform(5, 40)  # 5-40mm
    else:
        precipitation = random.uniform(0, 2)  # Poco o nada
    
    return {
        "station_id": station['id'],
        "station_name": station['name'],
        "region": station.get('region', 'Panamá'),
        "latitude": station['lat'],  # Agregar todos los campos requeridos por DB
        "longitude": station['lon'],
        "elevation": station.get('elevation', 0),
        "forecast_date": forecast_date,
        "temperature": base_temp,
        "temp_min": base_temp - random.uniform(2, 4),
        "temp_max": base_temp + random.uniform(2, 4),
        "temp_avg": base_temp,
        "precipitation_total": precipitation,
        "precipitation_probability": min(100, precipitation * 3),
        "wind_speed_max": random.uniform(5, 20),  # 5-20 km/h
        "wind_direction": None,
        "wind_angle": None,
        "humidity": base_humidity,
        "pressure": base_pressure,
        "cloud_cover": random.uniform(30, 90) if precipitation > 5 else random.uniform(10, 50),
        "summary": f"Precip: {precipitation:.1f}mm (SIMULADO)",
        "icon": "rain" if precipitation > 5 else "partly_cloudy",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_all_forecasts() -> List[Dict]:
    """
    Obtiene pronósticos para todas las estaciones configuradas.
    Si falla la API (5 errores consecutivos), genera datos simulados para demostración.
    Si ya fallamos 10 veces hoy, usa directamente datos simulados sin intentar la API.
    
    Returns:
        Lista con todos los pronósticos (reales o simulados)
    """
    all_forecasts = []
    
    # Verificar si debemos intentar la API o ir directo a simulados
    if not should_attempt_api():
        logger.warning(" 🎲 Usando solo datos simulados (límite de fallos alcanzado hoy)")
        from datetime import date, timedelta
        today = date.today()
        
        for sim_station in STATIONS:
            for days_ahead in [0, 1]:  # Hoy y mañana
                forecast_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                simulated = generate_simulated_forecast(sim_station, forecast_date)
                all_forecasts.append(simulated)
        
        logger.info(f" 🎲 Generados {len(all_forecasts)} pronósticos simulados")
        return all_forecasts
    
    # Intentar obtener datos reales de la API
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    logger.info(f" Iniciando obtención de forecasts para {len(STATIONS)} estaciones...")
    
    for station in STATIONS:
        forecast_data = fetch_forecast_for_station(station)
        
        if forecast_data:
            all_forecasts.extend(forecast_data)
            consecutive_errors = 0  # Resetear contador en caso de éxito
            record_api_result(success=True)  # Registrar éxito
        else:
            consecutive_errors += 1
            record_api_result(success=False)  # Registrar cada fallo
            logger.warning(f" No se obtuvo forecast para {station['name']} (error {consecutive_errors}/{max_consecutive_errors})")
            
            # Si alcanzamos el límite de errores consecutivos, usar datos simulados
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f" ✗ Límite de errores consecutivos alcanzado ({max_consecutive_errors}). Deteniendo obtención de API.")
                logger.warning(f" 🎲 Generando datos simulados para TODAS las estaciones (demostración)...")
                
                # Generar datos simulados para hoy y mañana para TODAS las estaciones
                from datetime import date, timedelta
                today = date.today()
                
                for sim_station in STATIONS:
                    for days_ahead in [0, 1]:  # Hoy y mañana
                        forecast_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                        simulated = generate_simulated_forecast(sim_station, forecast_date)
                        all_forecasts.append(simulated)
                
                logger.info(f" 🎲 Generados {len(all_forecasts)} pronósticos simulados")
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
        
        # Subir 5 niveles: forecast_pipeline.py -> meteosource -> etl -> pipelines -> core -> backend
        model_path = Path(__file__).parent.parent.parent.parent.parent / "ml_models" / "risk_model.joblib"
        
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
                # Preparar features del forecast (el modelo necesita precipitation_total, no precipitation)
                features = {
                    'temperature': forecast.get('temperature', forecast.get('temp_avg', 0)),
                    'humidity': forecast.get('humidity', 0),
                    'precipitation_total': forecast.get('precipitation_total', forecast.get('precipitation', 0)),
                    'wind_speed': forecast.get('wind_speed_max', forecast.get('wind_speed', 0)),
                    'pressure': forecast.get('pressure', 1013.25),
                    # Cambios (tendencias) - por ahora usar 0 ya que no tenemos histórico del forecast
                    'temp_change': 0,
                    'humidity_change': 0,
                    'precip_change': 0,
                    'wind_change': 0,
                    'pressure_change': 0,
                }
                
                # Predecir riesgos (devuelve dict con flood_risk y drought_risk)
                risk_prediction = predictor.predict(features)
                
                # Asignar riesgos de inundación
                flood_prob = risk_prediction['flood_risk']
                forecast["flood_probability"] = flood_prob
                forecast["flood_level"] = "RED" if flood_prob >= 0.7 else ("YELLOW" if flood_prob >= 0.3 else "GREEN")
                forecast["flood_alert"] = 1 if flood_prob >= 0.3 else 0
                
                # Asignar riesgos de sequía
                drought_prob = risk_prediction['drought_risk']
                forecast["drought_probability"] = drought_prob
                forecast["drought_level"] = "RED" if drought_prob >= 0.7 else ("YELLOW" if drought_prob >= 0.3 else "GREEN")
                forecast["drought_alert"] = 1 if drought_prob >= 0.3 else 0
                
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
