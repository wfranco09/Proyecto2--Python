"""
Pipeline de Meteosource para obtener datos climáticos en tiempo real
de las +250 estaciones en Panamá.

API Documentation: https://www.meteosource.com/documentation
Free plan: 400 calls/day - Current weather + 7-day forecast
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import time
import warnings

import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Suprimir warnings de deprecación para logs más limpios
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Colores ANSI para terminal
class Colors:
    BLUE = '\033[94m'      # Azul claro para INFO
    GREEN = '\033[92m'     # Verde para SUCCESS
    RED = '\033[91m'       # Rojo para ERROR
    YELLOW = '\033[93m'    # Amarillo para WARNING
    RESET = '\033[0m'      # Reset color
    GRAY = '\033[90m'      # Gris para INFO alternativo

# Configurar logging con formato personalizado
class ColoredFormatter(logging.Formatter):
    """Formatter personalizado con colores."""
    
    FORMATS = {
        logging.INFO: Colors.GRAY + '%(asctime)s - INFO - %(message)s' + Colors.RESET,
        logging.WARNING: Colors.YELLOW + '%(asctime)s - WARNING - %(message)s' + Colors.RESET,
        logging.ERROR: Colors.RED + '%(asctime)s - ERROR - %(message)s' + Colors.RESET,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, '%(asctime)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Manejarr para consola con formato coloreado
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

# Prevenir propagación a logger root
logger.propagate = False

# Paths (ya no se usan archivos CSV/JSON, solo base de datos)
BACKEND_DIR = Path(__file__).parent.parent.parent.parent.parent

# API Configuration
METEOSOURCE_API_URL = "https://www.meteosource.com/api/v1/free/point"


def get_stations_from_db() -> List[Dict]:
    """
    Obtiene todas las estaciones desde la base de datos.
    
    Returns:
        Lista de diccionarios con información de estaciones
    """
    try:
        from core.database.raindrop_db import get_all_stations
        stations = get_all_stations()
        logger.info(f"📊 Cargadas {len(stations)} estaciones desde la base de datos")
        return stations
    except Exception as e:
        logger.error(f"❌ Error obteniendo estaciones de la base de datos: {e}")
        # Fallback a config si falla la DB
        from config import STATIONS as CONFIG_STATIONS
        logger.warning(f"⚠️ Usando {len(CONFIG_STATIONS)} estaciones desde config.py como fallback")
        return CONFIG_STATIONS


def get_api_key() -> str:
    """Obtiene la API key desde variable de entorno."""
    api_key = os.getenv("METEOSOURCE_API_KEY")
    if not api_key:
        raise ValueError(
            "METEOSOURCE_API_KEY no está configurada. "
            "Por favor, configúrala en tu archivo .env o como variable de entorno."
        )
    return api_key


def fetch_weather_data(station: Dict, api_key: str) -> Optional[Dict]:
    """
    Obtiene datos climáticos actuales para una estación específica.
    
    Args:
        station: Diccionario con información de la estación
        api_key: API key de Meteosource
        
    Returns:
        Diccionario con datos climáticos o None si falla
    """
    try:
        params = {
            "lat": station['lat'],  # Formato decimal: 9.0892 o -9.0892
            "lon": station['lon'],  # Formato decimal: -79.3680 o 79.3680
            "sections": "current",  # Solo datos actuales
            "units": "metric",
            "key": api_key
        }
        
        logger.info(f"Obteniendo datos para {station['name']} (ID: {station['id']})")
        
        response = requests.get(METEOSOURCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraer datos relevantes
        current = data.get("current", {})
        wind = current.get("wind", {})
        precipitation = current.get("precipitation", {})
        
        weather_data = {
            "station_id": station["id"],
            "station_name": station["name"],
            "region": station["region"],
            "latitude": station["lat"],
            "longitude": station["lon"],
            "elevation": station["elevation"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": current.get("temperature"),
            "feels_like": current.get("feels_like"),
            "humidity": current.get("humidity"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("dir"),
            "wind_angle": wind.get("angle"),
            "precipitation_total": precipitation.get("total", 0),
            "precipitation_type": precipitation.get("type", "none"),
            "pressure": current.get("pressure"),
            "cloud_cover": current.get("cloud_cover"),
            "summary": current.get("summary"),
            "icon": current.get("icon"),
        }
        
        logger.info(f" Datos obtenidos para {station['name']}")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f" Error al obtener datos para {station['name']}: {e}")
        return None
    except Exception as e:
        logger.error(f" Error inesperado para {station['name']}: {e}")
        return None


def fetch_all_stations(api_key: str, delay: float = 0.5) -> List[Dict]:
    """
    Obtiene datos de todas las estaciones con un delay entre requests.
    
    Args:
        api_key: API key de Meteosource
        delay: Segundos de espera entre requests (para respetar rate limits)
        
    Returns:
        Lista de diccionarios con datos de todas las estaciones
    """
    all_data = []
    
    # Obtener estaciones desde la base de datos
    stations = get_stations_from_db()
    
    logger.info(f"🚀 Iniciando extracción de datos para {len(stations)} estaciones...")
    
    for i, station in enumerate(stations):
        weather_data = fetch_weather_data(station, api_key)
        
        if weather_data:
            all_data.append(weather_data)
        
        # Delay entre requests (excepto en el último)
        if i < len(stations) - 1:
            time.sleep(delay)
    
    logger.info(f"✅ Extracción completada: {len(all_data)}/{len(stations)} estaciones exitosas")
    return all_data


def save_to_database(data: List[Dict]) -> int:
    """
    Guarda datos directamente en la base de datos SQLite.
    
    Args:
        data: Lista de diccionarios con datos climáticos
        
    Returns:
        Número de registros guardados/actualizados
    """
    try:
        from core.database.raindrop_db import insert_or_update_weather_data
        records_saved = insert_or_update_weather_data(data)
        logger.info(f" {records_saved} registros guardados en base de datos")
        return records_saved
    except Exception as e:
        logger.error(f" Error guardando en base de datos: {e}")
        raise


def train_ml_model() -> Dict:
    """
    Entrena el modelo ML con los datos históricos de la base de datos.
    
    Returns:
        Métricas del entrenamiento
    """
    try:
        from core.ml import train_model_from_history
        logger.info(" Iniciando entrenamiento de modelo ML...")
        metrics = train_model_from_history(days_back=7)
        logger.info(f" Modelo entrenado | Accuracy: {metrics['accuracy']:.2%} | Tiempo: {metrics['training_time']:.1f}s")
        return metrics
    except Exception as e:
        logger.warning(f"  Entrenamiento de modelo omitido: {e}")
        return {}


def run():
    """Ejecuta el pipeline completo de Meteosource."""
    try:
        logger.info("=" * 70)
        logger.info("INICIANDO PIPELINE DE METEOSOURCE")
        logger.info("=" * 70)
        
        # 1. Obtener API key
        api_key = get_api_key()
        logger.info(" API key configurada")
        
        # 2. Extraer datos de todas las estaciones
        weather_data = fetch_all_stations(api_key, delay=0.5)
        
        if not weather_data:
            logger.error("No se pudieron obtener datos de ninguna estación")
            return False
        
        # 3. Guardar directamente en base de datos
        records_saved = save_to_database(weather_data)
        
        # Obtener número total de estaciones para el resumen
        stations = get_stations_from_db()
        
        logger.info("=" * 70)
        print(f"{Colors.GREEN}✅ PIPELINE COMPLETADO EXITOSAMENTE{Colors.RESET}")
        print(f"{Colors.GREEN}📊 Estaciones procesadas: {len(weather_data)}/{len(stations)}{Colors.RESET}")
        print(f"{Colors.GREEN}💾
        print(f"{Colors.GREEN} PIPELINE COMPLETADO EXITOSAMENTE{Colors.RESET}")
        print(f"{Colors.GREEN} Estaciones procesadas: {len(weather_data)}/{len(STATIONS)}{Colors.RESET}")
        print(f"{Colors.GREEN} Registros en DB: {records_saved}{Colors.RESET}")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"Error en pipeline de Meteosource: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
