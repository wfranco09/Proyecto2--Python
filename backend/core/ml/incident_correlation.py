"""
Módulo para correlacionar incidentes reportados con datos meteorológicos.
Permite usar reportes reales de usuarios para entrenar el modelo ML.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd

from core.database.raindrop_db import get_all_incident_reports, get_data_by_date_range

logger = logging.getLogger(__name__)


def get_incident_training_data() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Obtiene datos de entrenamiento basados en incidentes reportados por usuarios.
    
    Correlaciona cada incidente con MÚLTIPLES estaciones cercanas (radio 50km).
    El impacto disminuye con la distancia (decaimiento gaussiano).
    
    Returns:
        Tuple con (features_df, flood_labels, drought_labels)
    """
    logger.info("📊 Obteniendo incidentes reportados para entrenamiento...")
    
    # Obtener TODOS los incidentes (activos, resueltos y dismisseados)
    incidents = get_all_incident_reports(status=None, limit=10000)
    
    if not incidents:
        logger.warning("⚠️ No hay incidentes reportados en la base de datos")
        return pd.DataFrame(), pd.Series(dtype=float), pd.Series(dtype=float)
    
    logger.info(f"📍 Encontrados {len(incidents)} incidentes reportados")
    
    # Importar función para encontrar estaciones cercanas
    from config import STATIONS
    
    training_samples = []
    total_correlations = 0
    
    for incident in incidents:
        try:
            # Encontrar TODAS las estaciones dentro del radio de influencia (50km)
            nearby_stations = find_nearby_stations(
                incident['latitude'],
                incident['longitude'],
                STATIONS,
                max_distance_km=50
            )
            
            if not nearby_stations:
                logger.debug(f"Incidente {incident['id']} muy lejos de todas las estaciones (>50km)")
                continue
            
            # Obtener datos meteorológicos del momento del reporte
            # Usamos ventana de +/- 1 hora para capturar condiciones
            reported_at = datetime.fromisoformat(incident['reported_at'].replace('Z', '+00:00'))
            start_time = reported_at - timedelta(hours=1)
            end_time = reported_at + timedelta(hours=1)
            
            # Convertir severidad base a valor numérico
            severity_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
            base_severity = severity_map.get(incident.get('severity', 'medium'), 0.6)
            
            # Crear una muestra para CADA estación cercana con impacto proporcional
            for station_id, distance in nearby_stations:
                # Calcular factor de decaimiento basado en distancia
                # Fórmula gaussiana: impact = base_severity * exp(-(distance/20)^2)
                # Esto da: 0km=100%, 10km=78%, 20km=37%, 30km=11%, 40km=2%, 50km=0.3%
                import math
                distance_factor = math.exp(-(distance / 20) ** 2)
                adjusted_severity = base_severity * distance_factor
                
                # Obtener datos meteorológicos de esta estación
                weather_data = get_data_by_date_range(
                    station_id=station_id,
                    start_date=start_time.isoformat(),
                    end_date=end_time.isoformat()
                )
                
                if not weather_data:
                    logger.debug(f"No hay datos para estación {station_id} en incidente {incident['id']}")
                    continue
                
                # Usar el dato más cercano al momento del reporte
                weather_record = weather_data[0]
                
                # Crear etiquetas: solo el tipo de incidente reportado tiene valor
                flood_label = adjusted_severity if incident['incident_type'] == 'flood' else 0.0
                drought_label = adjusted_severity if incident['incident_type'] == 'drought' else 0.0
                
                # Extraer features meteorológicas
                sample = {
                    'temperature': float(weather_record.get('temperature', 0)),
                    'humidity': float(weather_record.get('humidity', 0)),
                    'precipitation_total': float(weather_record.get('precipitation_total', 0)),
                    'wind_speed': float(weather_record.get('wind_speed', 0)),
                    'pressure': float(weather_record.get('pressure', 1013)),
                    'temp_change': 0.0,  # No tenemos histórico aquí
                    'humidity_change': 0.0,
                    'precip_change': 0.0,
                    'wind_change': 0.0,
                    'pressure_change': 0.0,
                    'flood_risk': flood_label,
                    'drought_risk': drought_label,
                    'incident_id': incident['id'],
                    'station_id': station_id,
                    'distance_km': distance,
                    'impact_factor': distance_factor
                }
                
                training_samples.append(sample)
                total_correlations += 1
            
        except Exception as e:
            logger.warning(f"Error procesando incidente {incident.get('id')}: {e}")
            continue
    
    if not training_samples:
        logger.warning("⚠️ No se pudieron correlacionar incidentes con datos meteorológicos")
        return pd.DataFrame(), pd.Series(dtype=float), pd.Series(dtype=float)
    
    # Convertir a DataFrame
    df = pd.DataFrame(training_samples)
    
    logger.info(f"✅ Generadas {len(df)} muestras de entrenamiento desde {len(incidents)} incidentes")
    logger.info(f"   - Total correlaciones: {total_correlations} (múltiples estaciones por incidente)")
    logger.info(f"   - Promedio estaciones/incidente: {total_correlations/len(incidents):.1f}")
    logger.info(f"   - Flood incidents: {(df['flood_risk'] > 0).sum()}")
    logger.info(f"   - Drought incidents: {(df['drought_risk'] > 0).sum()}")
    logger.info(f"   - Rango impacto: {df['impact_factor'].min():.3f} - {df['impact_factor'].max():.3f}")
    
    # Separar features y labels
    feature_names = [
        'temperature', 'humidity', 'precipitation_total', 
        'wind_speed', 'pressure', 'temp_change', 
        'humidity_change', 'precip_change', 'wind_change', 'pressure_change'
    ]
    
    X = df[feature_names]
    y_flood = df['flood_risk']
    y_drought = df['drought_risk']
    
    return X, y_flood, y_drought


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula distancia entre dos puntos geográficos usando fórmula de Haversine.
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
        
    Returns:
        Distancia en kilómetros
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def find_nearby_stations(
    lat: float, 
    lon: float, 
    stations: List[Dict],
    max_distance_km: float = 50
) -> List[Tuple[int, float]]:
    """
    Encuentra TODAS las estaciones dentro de un radio de distancia.
    
    Args:
        lat: Latitud del punto
        lon: Longitud del punto
        stations: Lista de estaciones
        max_distance_km: Radio máximo de búsqueda en km
        
    Returns:
        Lista de tuplas (station_id, distance_km) ordenadas por distancia
    """
    nearby = []
    
    for station in stations:
        distance = haversine_distance(lat, lon, station['lat'], station['lon'])
        if distance <= max_distance_km:
            nearby.append((station['id'], distance))
    
    # Ordenar por distancia (más cercana primero)
    nearby.sort(key=lambda x: x[1])
    
    return nearby


def find_closest_station(lat: float, lon: float, stations: List[Dict]) -> Tuple[int, float]:
    """
    Encuentra la estación más cercana a unas coordenadas.
    
    Args:
        lat: Latitud del punto
        lon: Longitud del punto
        stations: Lista de estaciones
        
    Returns:
        Tuple (station_id, distance_km)
    """
    closest_station_id = None
    min_distance = float('inf')
    
    for station in stations:
        distance = haversine_distance(lat, lon, station['lat'], station['lon'])
        if distance < min_distance:
            min_distance = distance
            closest_station_id = station['id']
    
    return closest_station_id, min_distance


def get_combined_training_data(use_incidents: bool = True) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Combina datos de incidentes reales con datos sintéticos históricos.
    
    Args:
        use_incidents: Si es True, incluye datos de incidentes reportados
        
    Returns:
        Tuple con (features_df, flood_labels, drought_labels)
    """
    from core.ml.risk_predictor import RiskPredictor
    
    # 1. Obtener datos de incidentes reales (prioridad)
    if use_incidents:
        X_incidents, y_flood_incidents, y_drought_incidents = get_incident_training_data()
        
        if len(X_incidents) > 0:
            logger.info(f"✅ Usando {len(X_incidents)} muestras de incidentes REALES")
            return X_incidents, y_flood_incidents, y_drought_incidents
        else:
            logger.warning("⚠️ No hay incidentes suficientes, usando datos sintéticos...")
    
    # 2. Fallback: usar método sintético original
    predictor = RiskPredictor()
    X_synthetic, y_flood_synthetic, y_drought_synthetic = predictor.prepare_training_data()
    
    logger.info(f"📊 Usando {len(X_synthetic):,} muestras sintéticas (fallback)")
    
    return X_synthetic, y_flood_synthetic, y_drought_synthetic
