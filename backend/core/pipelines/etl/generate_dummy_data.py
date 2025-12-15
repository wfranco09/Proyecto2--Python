"""
Pipeline para generar datos climáticos dummy para entrenamiento del modelo ML.

Genera datos sintéticos basados en rangos realistas de variables climáticas
de Panamá y correlaciones típicas entre variables.
"""

import logging
import random
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from pathlib import Path

from config import STATIONS
from core.database.raindrop_db import insert_or_update_weather_data, DATABASE_PATH

logger = logging.getLogger(__name__)

# Estado global del progreso de generación
generation_progress = {
    "is_running": False,
    "current_station": 0,
    "total_stations": 0,
    "station_name": "",
    "records_generated": 0,
    "start_time": None,
    "error": None
}


# Rangos realistas de variables climáticas para Panamá
WEATHER_RANGES = {
    'temperature': (20.0, 35.0),  # °C - rango tropical
    'feels_like': (20.0, 40.0),   # °C - puede ser mayor por humedad
    'humidity': (50.0, 100.0),     # % - alta humedad en trópico
    'wind_speed': (0.0, 40.0),     # km/h
    'wind_angle': (0, 360),        # grados
    'precipitation_total': (0.0, 150.0),  # mm - puede ser muy alto en tormentas
    'pressure': (1005.0, 1020.0),  # hPa - rango tropical
    'cloud_cover': (0, 100),       # %
}

# Direcciones de viento
WIND_DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

# Tipos de precipitación
PRECIPITATION_TYPES = ['none', 'rain', 'drizzle', 'thunderstorm']

# Descripciones del clima
WEATHER_SUMMARIES = [
    'Despejado', 'Parcialmente nublado', 'Nublado', 'Lluvioso',
    'Tormenta', 'Llovizna', 'Sol con nubes', 'Cielo cubierto'
]

# Iconos de clima
WEATHER_ICONS = ['clear', 'pcloudy', 'cloudy', 'rain', 'tstorm', 'fog']


def generate_correlated_weather_data(base_temp: float, base_humidity: float) -> Dict:
    """
    Genera datos climáticos con correlaciones realistas.
    
    Correlaciones:
    - Temperatura alta → Sensación térmica más alta
    - Humedad alta + Temperatura alta → Mayor precipitación
    - Precipitación alta → Nubosidad alta
    - Presión baja → Mayor probabilidad de lluvia
    """
    # Temperatura base con variación
    temp = base_temp + random.uniform(-3, 3)
    temp = max(WEATHER_RANGES['temperature'][0], min(WEATHER_RANGES['temperature'][1], temp))
    
    # Sensación térmica (mayor con humedad alta)
    humidity = base_humidity + random.uniform(-10, 10)
    humidity = max(WEATHER_RANGES['humidity'][0], min(WEATHER_RANGES['humidity'][1], humidity))
    feels_like = temp + (humidity / 100.0) * 5.0
    
    # Precipitación (más probable con humedad alta y temperatura alta)
    precipitation_prob = (humidity / 100.0) * 0.4 + (temp / 35.0) * 0.3
    if random.random() < precipitation_prob:
        # Hay precipitación
        precip = random.uniform(0.5, WEATHER_RANGES['precipitation_total'][1])
        # Correlación: más precipitación → más nubosidad
        cloud_cover = int(min(100, 60 + (precip / 150.0) * 40 + random.uniform(-10, 10)))
        precip_type = random.choice(['rain', 'drizzle', 'thunderstorm'])
        summary = random.choice(['Lluvioso', 'Tormenta', 'Llovizna', 'Cielo cubierto'])
        icon = 'rain' if precip < 50 else 'tstorm'
        # Presión más baja con lluvia
        pressure = random.uniform(1005, 1012)
    else:
        # Sin precipitación
        precip = 0.0
        cloud_cover = int(random.uniform(0, 70))
        precip_type = 'none'
        if cloud_cover < 30:
            summary = 'Despejado'
            icon = 'clear'
        elif cloud_cover < 60:
            summary = 'Parcialmente nublado'
            icon = 'pcloudy'
        else:
            summary = 'Nublado'
            icon = 'cloudy'
        pressure = random.uniform(1010, 1020)
    
    # Viento
    wind_speed = random.uniform(WEATHER_RANGES['wind_speed'][0], WEATHER_RANGES['wind_speed'][1])
    wind_angle = random.randint(WEATHER_RANGES['wind_angle'][0], WEATHER_RANGES['wind_angle'][1] - 1)  # 0-359
    wind_direction = WIND_DIRECTIONS[min(wind_angle // 45, 7)]  # Asegurar índice válido 0-7
    
    return {
        'temperature': round(temp, 1),
        'feels_like': round(feels_like, 1),
        'humidity': round(humidity, 1),
        'wind_speed': round(wind_speed, 1),
        'wind_direction': wind_direction,
        'wind_angle': wind_angle,
        'precipitation_total': round(precip, 2),
        'precipitation_type': precip_type,
        'pressure': round(pressure, 1),
        'cloud_cover': cloud_cover,
        'summary': summary,
        'icon': icon
    }


def generate_seasonal_pattern(month: int, hour: int) -> tuple:
    """
    Genera patrones estacionales realistas para Panamá.
    
    - Estación seca (Enero-Abril): menos lluvia, más calor
    - Estación lluviosa (Mayo-Diciembre): más lluvia, más humedad
    - Patrón diario: más calor al mediodía, más fresco en la madrugada
    """
    # Estación del año
    if 1 <= month <= 4:
        # Estación seca
        base_temp = 28.0
        base_humidity = 65.0
    else:
        # Estación lluviosa
        base_temp = 26.0
        base_humidity = 85.0
    
    # Variación diurna
    if 6 <= hour <= 18:
        # Día
        temp_adjustment = 3.0 + np.sin((hour - 6) / 12 * np.pi) * 4.0
    else:
        # Noche
        temp_adjustment = -2.0
    
    return base_temp + temp_adjustment, base_humidity


def generate_dummy_weather_data(
    days_back: int = 365,
    stations_to_use: List[Dict] = None,
    use_random: bool = False,
    records_per_day: int = 24
) -> int:
    """
    Genera datos climáticos dummy para entrenamiento del modelo.
    
    Args:
        days_back: Cuántos días hacia atrás generar datos (default: 365 = 1 año)
        stations_to_use: Lista de estaciones a usar (default: todas de STATIONS)
        use_random: Si True, genera datos completamente aleatorios.
                   Si False, genera datos basados en patrones estacionales (default).
        records_per_day: Número de registros por día (default: 24 = cada hora)
        
    Returns:
        Número de registros insertados
    """
    mode_text = "aleatorios" if use_random else "con patrones estacionales"
    logger.info(f" Iniciando generación de datos para {days_back} días ({mode_text})...")
    
    # Usar estaciones configuradas o las proporcionadas
    stations = stations_to_use or STATIONS
    num_stations = len(stations)
    
    if num_stations == 0:
        logger.error(" No hay estaciones configuradas")
        return 0
    
    
    # Fecha de inicio
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    # Generar e insertar datos por estación (no acumular todo en memoria)
    total_inserted = 0
    hours_between_records = 24 // records_per_day
    
    logger.info(f" Rango de fechas: {start_date.date()} a {end_date.date()}")
    logger.info(" Iniciando generación e inserción...\n")
    
    # Actualizar progreso: inicio
    generation_progress["is_running"] = True
    generation_progress["total_stations"] = num_stations
    generation_progress["current_station"] = 0
    generation_progress["records_generated"] = 0
    generation_progress["start_time"] = datetime.now(timezone.utc).isoformat()
    generation_progress["error"] = None
    
    for idx, station in enumerate(stations, 1):
        # Actualizar progreso: estación actual
        generation_progress["current_station"] = idx
        generation_progress["station_name"] = station['name']
        
        logger.info(f" [{idx}/{num_stations}] Generando datos para {station['name']} (ID: {station['id']})")
        
        station_weather_data = []
        station_records = 0
        current_date = start_date
        
        while current_date <= end_date:
            if use_random:
                # Modo aleatorio: generar temperaturas y humedad completamente random
                # para incluir escenarios de alto riesgo
                base_temp = random.uniform(WEATHER_RANGES['temperature'][0], WEATHER_RANGES['temperature'][1])
                base_humidity = random.uniform(WEATHER_RANGES['humidity'][0], WEATHER_RANGES['humidity'][1])
            else:
                # Modo conocimiento: usar patrones estacionales
                base_temp, base_humidity = generate_seasonal_pattern(
                    current_date.month,
                    current_date.hour
                )
            
            # Generar datos correlacionados
            weather_data = generate_correlated_weather_data(base_temp, base_humidity)
            
            # Agregar metadata de la estación
            weather_record = {
                'station_id': station['id'],
                'station_name': station['name'],
                'region': station.get('region', 'Panama'),
                'latitude': station['lat'],
                'longitude': station['lon'],
                'elevation': station.get('elevation', 0),
                'timestamp': current_date.isoformat(),
                **weather_data
            }
            
            station_weather_data.append(weather_record)
            station_records += 1
            
            # Avanzar tiempo según records_per_day
            current_date += timedelta(hours=hours_between_records)
        
        # Insertar datos de esta estación inmediatamente (en lotes pequeños)
        logger.info(f"     Insertando {station_records} registros...")
        batch_size = 100
        station_inserted = 0
        
        for i in range(0, len(station_weather_data), batch_size):
            batch = station_weather_data[i:i + batch_size]
            try:
                count = insert_or_update_weather_data(batch)
                station_inserted += count
            except Exception as e:
                logger.error(f" Error insertando lote: {e}")
        
        total_inserted += station_inserted
        
        # Actualizar progreso después de completar cada estación
        generation_progress["records_generated"] = total_inserted
        generation_progress["percentage"] = (idx / num_stations) * 100
        
        logger.info(f"     ✓ {station_inserted} registros insertados para {station['name']}")
    
    logger.info(f" Generación completada: {total_inserted} registros insertados/actualizados")
    
    # Estadísticas
    avg_records = total_inserted // num_stations if num_stations > 0 else 0
    logger.info(f" Rango de fechas: {start_date.date()} a {end_date.date()}")
    logger.info(f" Estaciones: {num_stations}")
    logger.info(f" Registros por estación (aprox): {avg_records}")
    
    # Marcar como completado
    generation_progress["is_running"] = False
    generation_progress["percentage"] = 100
    
    return total_inserted


def run(days: int = 365, use_random: bool = False, records_per_day: int = 24):
    """
    Ejecuta el pipeline de generación de datos dummy.
    
    Args:
        days: Número de días de historia a generar (default: 365 = 1 año)
        use_random: Genera datos aleatorios (True) o basados en patrones estacionales (False, recomendado)
        records_per_day: Registros por día (default: 24 = cada hora)
    """
    try:
        # Resetear progreso
        generation_progress["is_running"] = True
        generation_progress["current_station"] = 0
        generation_progress["total_stations"] = 0
        generation_progress["station_name"] = ""
        generation_progress["records_generated"] = 0
        generation_progress["start_time"] = datetime.now(timezone.utc).isoformat()
        generation_progress["error"] = None
        
        logger.info("=" * 60)
        logger.info(" PIPELINE: GENERACIÓN DE DATOS DUMMY - 1 AÑO")
        logger.info("=" * 60)
        
        inserted = generate_dummy_weather_data(days_back=days, use_random=use_random, records_per_day=records_per_day)
        
        if inserted > 0:
            logger.info(f" Pipeline completado exitosamente: {inserted} registros")
            return True
        else:
            logger.warning(" No se insertaron registros")
            return False
            
    except Exception as e:
        logger.error(f" Error en pipeline de generación de datos dummy: {e}", exc_info=True)
        generation_progress["is_running"] = False
        generation_progress["error"] = str(e)
        return False


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parsear argumentos
    days = 365  # Default: 1 año
    use_random = False  # Default: usar patrones estacionales
    records_per_day = 24  # Default: cada hora
    
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])
    
    if '--use-random' in sys.argv:
        idx = sys.argv.index('--use-random')
        if idx + 1 < len(sys.argv):
            use_random = sys.argv[idx + 1].lower() == 'true'
    
    if '--records-per-day' in sys.argv:
        idx = sys.argv.index('--records-per-day')
        if idx + 1 < len(sys.argv):
            records_per_day = int(sys.argv[idx + 1])
    
    run(days=days, use_random=use_random, records_per_day=records_per_day)
