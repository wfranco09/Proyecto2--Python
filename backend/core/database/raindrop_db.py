"""
Database service para gestionar datos climáticos de Meteosource.

Implementa:
- Schema relacional con deduplicación por hora
- Solo se mantiene el último registro de cada hora por estación
- Agrupación por día y hora
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Path a la base de datos
DATABASE_PATH = Path(__file__).parent.parent / "database" / "raindrop.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_database():
    """Inicializa el schema de la base de datos."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Tabla principal de datos climáticos con índice único por estación+fecha+hora
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER NOT NULL,
            station_name TEXT NOT NULL,
            region TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation INTEGER NOT NULL,
            
            -- Campos de agrupación temporal
            date TEXT NOT NULL,           -- Fecha: YYYY-MM-DD
            hour INTEGER NOT NULL,        -- Hora: 0-23
            timestamp TEXT NOT NULL,      -- Timestamp completo ISO
            
            -- Datos climáticos
            temperature REAL,
            feels_like REAL,
            humidity REAL,
            wind_speed REAL,
            wind_direction TEXT,
            wind_angle INTEGER,
            precipitation_total REAL,
            precipitation_type TEXT,
            pressure REAL,
            cloud_cover INTEGER,
            summary TEXT,
            icon TEXT,
            
            -- Metadata
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            
            -- Constraint único: una sola lectura por estación por hora
            UNIQUE(station_id, date, hour)
        )
    """)
    
    # Índices para optimizar consultas
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_station_date_hour 
        ON weather_hourly(station_id, date, hour)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date_hour 
        ON weather_hourly(date, hour)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_station_id 
        ON weather_hourly(station_id)
    """)
    
    # Tabla de estaciones (si no existe)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de reportes de incidencias/anomalías
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_type TEXT NOT NULL,  -- 'flood' o 'drought'
            description TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            severity TEXT DEFAULT 'medium',  -- 'low', 'medium', 'high'
            status TEXT DEFAULT 'active',  -- 'active', 'resolved', 'dismissed'
            reported_by TEXT,  -- Usuario/fuente del reporte
            reported_at TEXT NOT NULL,
            resolved_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Índices para reportes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_status 
        ON incident_reports(status)
    """)
    
    # Tabla de pronósticos (forecast de 7 días)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER NOT NULL,
            station_name TEXT NOT NULL,
            region TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation INTEGER NOT NULL,
            
            -- Fecha del pronóstico
            forecast_date TEXT NOT NULL,  -- YYYY-MM-DD
            
            -- Datos climáticos
            temp_max REAL,
            temp_min REAL,
            temp_avg REAL,
            humidity REAL,
            wind_speed_max REAL,
            wind_direction TEXT,
            wind_angle INTEGER,
            precipitation_total REAL,
            precipitation_probability REAL,
            pressure REAL,
            cloud_cover INTEGER,
            summary TEXT,
            icon TEXT,
            
            -- Riesgos pre-calculados (para carga rápida)
            flood_probability REAL DEFAULT 0.0,
            flood_level TEXT DEFAULT 'GREEN',
            flood_alert INTEGER DEFAULT 0,
            drought_probability REAL DEFAULT 0.0,
            drought_level TEXT DEFAULT 'GREEN',
            drought_alert INTEGER DEFAULT 0,
            
            -- Metadata
            retrieved_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraint único: un pronóstico por estación por día
            UNIQUE(station_id, forecast_date)
        )
    """)
    
    # Índices para forecasts
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecast_station_date 
        ON weather_forecast(station_id, forecast_date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecast_date 
        ON weather_forecast(forecast_date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_type 
        ON incident_reports(incident_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_reported_at 
        ON incident_reports(reported_at DESC)
    """)
    
    # Tabla de alertas activas (generadas automáticamente)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER NOT NULL,
            station_name TEXT NOT NULL,
            alert_type TEXT NOT NULL,  -- 'flood' o 'drought'
            risk_level TEXT NOT NULL,  -- 'YELLOW', 'RED'
            probability REAL NOT NULL,  -- 0.0 - 1.0
            triggered_at TEXT NOT NULL,  -- Timestamp cuando se generó la alerta
            updated_at TEXT NOT NULL,  -- Última actualización
            
            -- Constraint único: una alerta por estación por tipo
            UNIQUE(station_id, alert_type)
        )
    """)
    
    # Índices para alertas
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_station 
        ON active_alerts(station_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_type 
        ON active_alerts(alert_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_triggered 
        ON active_alerts(triggered_at DESC)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f" Base de datos inicializada: {DATABASE_PATH}")


def insert_or_update_weather_data(weather_data: List[Dict]) -> int:
    """
    Inserta o actualiza datos climáticos.
    
    Si ya existe un registro para la misma estación, fecha y hora,
    lo reemplaza con los datos más recientes.
    
    Args:
        weather_data: Lista de diccionarios con datos climáticos
        
    Returns:
        Número de registros insertados/actualizados
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for data in weather_data:
        try:
            # Parsear timestamp y extraer fecha y hora
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            date_str = timestamp.strftime('%Y-%m-%d')
            hour = timestamp.hour
            
            now = datetime.now(timezone.utc).isoformat()
            
            # Usar INSERT OR REPLACE para deduplicación automática
            cursor.execute("""
                INSERT INTO weather_hourly (
                    station_id, station_name, region, latitude, longitude, elevation,
                    date, hour, timestamp,
                    temperature, feels_like, humidity,
                    wind_speed, wind_direction, wind_angle,
                    precipitation_total, precipitation_type,
                    pressure, cloud_cover, summary, icon,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(station_id, date, hour) 
                DO UPDATE SET
                    timestamp = excluded.timestamp,
                    temperature = excluded.temperature,
                    feels_like = excluded.feels_like,
                    humidity = excluded.humidity,
                    wind_speed = excluded.wind_speed,
                    wind_direction = excluded.wind_direction,
                    wind_angle = excluded.wind_angle,
                    precipitation_total = excluded.precipitation_total,
                    precipitation_type = excluded.precipitation_type,
                    pressure = excluded.pressure,
                    cloud_cover = excluded.cloud_cover,
                    summary = excluded.summary,
                    icon = excluded.icon,
                    updated_at = excluded.updated_at
            """, (
                data['station_id'], 
                data.get('station_name', f"Estación {data['station_id']}"), 
                data.get('region', 'Panama'),
                data.get('latitude'), 
                data.get('longitude'), 
                data.get('elevation'),
                date_str, hour, data['timestamp'],
                data.get('temperature'), data.get('feels_like'), data.get('humidity'),
                data.get('wind_speed'), data.get('wind_direction'), data.get('wind_angle'),
                data.get('precipitation_total'), data.get('precipitation_type'),
                data.get('pressure'), data.get('cloud_cover'),
                data.get('summary'), data.get('icon'),
                now, now
            ))
            
            if cursor.rowcount > 0:
                # Si rowcount es 1, fue INSERT, si es 2 fue UPDATE (SQLite behavior)
                if cursor.lastrowid > 0:
                    inserted += 1
                else:
                    updated += 1
                    
        except Exception as e:
            logger.error(f"Error insertando datos de estación {data.get('station_id')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    logger.info(f" Datos guardados: {inserted} nuevos, {updated} actualizados")
    return inserted + updated


def get_latest_data_by_station(station_id: int, limit: int = 24) -> List[Dict]:
    """
    Obtiene los últimos registros de una estación.
    
    Args:
        station_id: ID de la estación
        limit: Número máximo de registros (default: últimas 24 horas)
        
    Returns:
        Lista de registros ordenados por fecha y hora descendente
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM weather_hourly
        WHERE station_id = ?
        ORDER BY date DESC, hour DESC
        LIMIT ?
    """, (station_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_data_by_date_range(start_date: str, end_date: str, station_id: Optional[int] = None) -> List[Dict]:
    """
    Obtiene datos en un rango de fechas.
    
    Args:
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        station_id: ID de estación (opcional, si no se proporciona obtiene todas)
        
    Returns:
        Lista de registros en el rango
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if station_id:
        cursor.execute("""
            SELECT * FROM weather_hourly
            WHERE date BETWEEN ? AND ?
            AND station_id = ?
            ORDER BY date, hour
        """, (start_date, end_date, station_id))
    else:
        cursor.execute("""
            SELECT * FROM weather_hourly
            WHERE date BETWEEN ? AND ?
            ORDER BY station_id, date, hour
        """, (start_date, end_date))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_stations() -> List[Dict]:
    """
    Obtiene todas las estaciones desde la tabla stations.
    
    Returns:
        Lista de diccionarios con información de todas las estaciones
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            name,
            region,
            latitude as lat,
            longitude as lon,
            elevation
        FROM stations
        ORDER BY id
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    stations = []
    for row in rows:
        stations.append({
            "id": row["id"],
            "name": row["name"],
            "region": row["region"],
            "lat": row["lat"],
            "lon": row["lon"],
            "elevation": row["elevation"]
        })
    
    return stations


def get_all_stations_latest() -> List[Dict]:
    """
    Obtiene el último registro de cada estación con datos válidos de humedad.
    Prioriza datos con humedad > 0 para usar datos generados en lugar de Meteosource incompletos.
    
    Returns:
        Lista con el último dato válido de cada estación
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Primero intentar obtener datos con humedad válida (datos dummy generados)
    cursor.execute("""
        SELECT w1.* FROM weather_hourly w1
        INNER JOIN (
            SELECT station_id, MAX(date || ' ' || printf('%02d', hour)) as max_datetime
            FROM weather_hourly
            WHERE humidity IS NOT NULL AND humidity > 0
            GROUP BY station_id
        ) w2 ON w1.station_id = w2.station_id 
        AND (w1.date || ' ' || printf('%02d', w1.hour)) = w2.max_datetime
        ORDER BY w1.station_id
    """)
    
    rows = cursor.fetchall()
    
    # Si no hay datos con humedad, caer al último registro sin filtro
    if not rows:
        cursor.execute("""
            SELECT w1.* FROM weather_hourly w1
            INNER JOIN (
                SELECT station_id, MAX(date || ' ' || printf('%02d', hour)) as max_datetime
                FROM weather_hourly
                GROUP BY station_id
            ) w2 ON w1.station_id = w2.station_id 
            AND (w1.date || ' ' || printf('%02d', w1.hour)) = w2.max_datetime
            ORDER BY w1.station_id
        """)
        rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def cleanup_old_data(days_to_keep: int = 30):
    """
    Limpia datos antiguos para mantener solo los últimos N días.
    
    Args:
        days_to_keep: Número de días a mantener (default: 30)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        DELETE FROM weather_hourly
        WHERE date < ?
    """, (cutoff_date,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f" Limpieza completada: {deleted} registros antiguos eliminados")
    return deleted


def insert_incident_report(incident_data: Dict) -> int:
    """
    Inserta un nuevo reporte de incidencia.
    
    Args:
        incident_data: Diccionario con datos del reporte
            - incident_type: 'flood' o 'drought'
            - description: Descripción del incidente
            - latitude: Latitud
            - longitude: Longitud
            - severity: 'low', 'medium', 'high' (opcional)
            - reported_by: Usuario que reporta (opcional)
            
    Returns:
        ID del reporte insertado
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO incident_reports (
            incident_type, description, latitude, longitude,
            severity, reported_by, reported_at, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
    """, (
        incident_data['incident_type'],
        incident_data['description'],
        incident_data['latitude'],
        incident_data['longitude'],
        incident_data.get('severity', 'medium'),
        incident_data.get('reported_by', 'anonymous'),
        now,
        now,
        now
    ))
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f" Reporte de incidencia creado: ID={report_id}, Tipo={incident_data['incident_type']}")
    return report_id


def get_active_incident_reports(limit: int = 50) -> List[Dict]:
    """
    Obtiene reportes de incidencias activas.
    
    Args:
        limit: Número máximo de reportes
        
    Returns:
        Lista de reportes activos ordenados por fecha
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM incident_reports
        WHERE status = 'active'
        ORDER BY reported_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_incident_reports(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Obtiene todos los reportes de incidencias.
    
    Args:
        status: Filtrar por estado ('active', 'resolved', 'dismissed')
        limit: Número máximo de reportes
        
    Returns:
        Lista de reportes
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status:
        cursor.execute("""
            SELECT * FROM incident_reports
            WHERE status = ?
            ORDER BY reported_at DESC
            LIMIT ?
        """, (status, limit))
    else:
        cursor.execute("""
            SELECT * FROM incident_reports
            ORDER BY reported_at DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def update_incident_status(incident_id: int, status: str, notes: Optional[str] = None) -> bool:
    """
    Actualiza el estado de un reporte de incidencia.
    
    Args:
        incident_id: ID del reporte
        status: Nuevo estado ('active', 'resolved', 'dismissed')
        notes: Notas adicionales (opcional)
        
    Returns:
        True si se actualizó correctamente
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    
    if status == 'resolved':
        cursor.execute("""
            UPDATE incident_reports
            SET status = ?, resolved_at = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (status, now, notes, now, incident_id))
    else:
        cursor.execute("""
            UPDATE incident_reports
            SET status = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (status, notes, now, incident_id))
    
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if updated:
        logger.info(f" Reporte {incident_id} actualizado a estado: {status}")
    
    return updated


def insert_or_update_forecast_data(forecast_data: List[Dict]) -> int:
    """
    Inserta o actualiza datos de pronóstico en la base de datos.
    
    Args:
        forecast_data: Lista de diccionarios con datos de pronóstico
        
    Returns:
        Número de registros procesados
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for record in forecast_data:
        try:
            # Insertar o actualizar
            cursor.execute("""
                INSERT INTO weather_forecast (
                    station_id, station_name, region, latitude, longitude, elevation,
                    forecast_date, temp_max, temp_min, temp_avg, humidity,
                    wind_speed_max, wind_direction, wind_angle,
                    precipitation_total, precipitation_probability,
                    pressure, cloud_cover, summary, icon,
                    flood_probability, flood_level, flood_alert,
                    drought_probability, drought_level, drought_alert,
                    retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(station_id, forecast_date) DO UPDATE SET
                    temp_max = excluded.temp_max,
                    temp_min = excluded.temp_min,
                    temp_avg = excluded.temp_avg,
                    humidity = excluded.humidity,
                    wind_speed_max = excluded.wind_speed_max,
                    wind_direction = excluded.wind_direction,
                    wind_angle = excluded.wind_angle,
                    precipitation_total = excluded.precipitation_total,
                    precipitation_probability = excluded.precipitation_probability,
                    pressure = excluded.pressure,
                    cloud_cover = excluded.cloud_cover,
                    summary = excluded.summary,
                    icon = excluded.icon,
                    flood_probability = excluded.flood_probability,
                    flood_level = excluded.flood_level,
                    flood_alert = excluded.flood_alert,
                    drought_probability = excluded.drought_probability,
                    drought_level = excluded.drought_level,
                    drought_alert = excluded.drought_alert,
                    retrieved_at = excluded.retrieved_at,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                record.get("station_id"),
                record.get("station_name"),
                record.get("region"),
                record.get("latitude"),
                record.get("longitude"),
                record.get("elevation"),
                record.get("forecast_date"),
                record.get("temp_max"),
                record.get("temp_min"),
                record.get("temp_avg"),
                record.get("humidity"),
                record.get("wind_speed_max"),
                record.get("wind_direction"),
                record.get("wind_angle"),
                record.get("precipitation_total"),
                record.get("precipitation_probability"),
                record.get("pressure"),
                record.get("cloud_cover"),
                record.get("summary"),
                record.get("icon"),
                record.get("flood_probability", 0.0),
                record.get("flood_level", "GREEN"),
                1 if record.get("flood_alert", False) else 0,
                record.get("drought_probability", 0.0),
                record.get("drought_level", "GREEN"),
                1 if record.get("drought_alert", False) else 0,
                record.get("retrieved_at"),
            ))
            
            if cursor.rowcount == 1:
                inserted += 1
            else:
                updated += 1
                
        except Exception as e:
            logger.error(f" Error insertando forecast: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    logger.info(f" Pronósticos guardados: {inserted} nuevos, {updated} actualizados")
    return inserted + updated


def get_forecast_by_station(station_id: int, days: int = 7) -> List[Dict]:
    """
    Obtiene pronóstico de los próximos N días para una estación.
    Si no hay datos válidos para hoy/mañana (probabilidades = 0.0), usa los datos 
    más recientes disponibles con riesgos calculados (fallback).
    
    Args:
        station_id: ID de la estación
        days: Número de días a obtener (default: 7)
        
    Returns:
        Lista de pronósticos ordenados por fecha
    """
    from datetime import date as date_module
    today = date_module.today().isoformat()
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Primero intentar obtener datos de hoy en adelante
    cursor.execute("""
        SELECT * FROM weather_forecast
        WHERE station_id = ?
        AND forecast_date >= ?
        ORDER BY forecast_date ASC
        LIMIT ?
    """, (station_id, today, days))
    
    rows = cursor.fetchall()
    
    # Verificar si los datos tienen riesgos calculados
    has_valid_risks = False
    if rows:
        for row in rows:
            if row['flood_probability'] > 0.0 or row['drought_probability'] > 0.0:
                has_valid_risks = True
                break
    
    # Si no hay datos o no tienen riesgos calculados, usar los datos más recientes con riesgos
    if not rows or not has_valid_risks:
        logger.warning(f"⚠️ No hay datos de forecast válidos para estación {station_id}, usando datos más recientes con riesgos calculados")
        cursor.execute("""
            SELECT * FROM weather_forecast
            WHERE station_id = ?
            AND (flood_probability > 0.0 OR drought_probability > 0.0)
            ORDER BY forecast_date DESC
            LIMIT ?
        """, (station_id, days))
        rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_forecasts(days: int = 7) -> Dict[int, List[Dict]]:
    """
    Obtiene pronósticos de todas las estaciones agrupados por station_id.
    Si no hay datos válidos para hoy/mañana (probabilidades = 0.0), usa los datos 
    más recientes disponibles con riesgos calculados (fallback).
    
    Args:
        days: Número de días a obtener (default: 7)
        
    Returns:
        Diccionario {station_id: [forecasts]}
    """
    from datetime import date as date_module
    today = date_module.today().isoformat()
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Primero intentar obtener datos de hoy en adelante
    cursor.execute("""
        SELECT * FROM weather_forecast
        WHERE forecast_date >= ?
        ORDER BY station_id, forecast_date ASC
    """, (today,))
    
    rows = cursor.fetchall()
    
    # Verificar si los datos tienen riesgos calculados (probabilidades > 0)
    has_valid_risks = False
    if rows:
        for row in rows:
            if row['flood_probability'] > 0.0 or row['drought_probability'] > 0.0:
                has_valid_risks = True
                break
    
    # Si no hay datos o no tienen riesgos calculados, usar los datos más recientes con riesgos
    if not rows or not has_valid_risks:
        logger.warning("⚠️ No hay datos de forecast válidos para hoy, usando datos más recientes con riesgos calculados")
        cursor.execute("""
            SELECT * FROM weather_forecast
            WHERE flood_probability > 0.0 OR drought_probability > 0.0
            ORDER BY forecast_date DESC, station_id
        """)
        rows = cursor.fetchall()
    
    conn.close()
    
    # Agrupar por estación
    forecasts_by_station = {}
    for row in rows:
        station_id = row["station_id"]
        if station_id not in forecasts_by_station:
            forecasts_by_station[station_id] = []
        forecasts_by_station[station_id].append(dict(row))
    
    # Limitar a N días por estación
    for station_id in forecasts_by_station:
        forecasts_by_station[station_id] = forecasts_by_station[station_id][:days]
    
    return forecasts_by_station


def upsert_alert(station_id: int, station_name: str, alert_type: str, 
                 risk_level: str, probability: float) -> None:
    """
    Crea o actualiza una alerta activa.
    
    Args:
        station_id: ID de la estación
        station_name: Nombre de la estación
        alert_type: Tipo de alerta ('flood' o 'drought')
        risk_level: Nivel de riesgo ('YELLOW' o 'RED')
        probability: Probabilidad del riesgo (0.0 - 1.0)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    # Verificar si ya existe una alerta para esta estación y tipo
    cursor.execute("""
        SELECT id, triggered_at FROM active_alerts
        WHERE station_id = ? AND alert_type = ?
    """, (station_id, alert_type))
    
    existing = cursor.fetchone()
    
    if existing:
        # Actualizar alerta existente (mantener triggered_at original)
        cursor.execute("""
            UPDATE active_alerts
            SET risk_level = ?, probability = ?, updated_at = ?, station_name = ?
            WHERE station_id = ? AND alert_type = ?
        """, (risk_level, probability, now, station_name, station_id, alert_type))
    else:
        # Crear nueva alerta
        cursor.execute("""
            INSERT INTO active_alerts 
            (station_id, station_name, alert_type, risk_level, probability, triggered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (station_id, station_name, alert_type, risk_level, probability, now, now))
    
    conn.commit()
    conn.close()


def remove_alert(station_id: int, alert_type: str) -> None:
    """
    Elimina una alerta activa.
    
    Args:
        station_id: ID de la estación
        alert_type: Tipo de alerta ('flood' o 'drought')
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM active_alerts
        WHERE station_id = ? AND alert_type = ?
    """, (station_id, alert_type))
    
    conn.commit()
    conn.close()


def get_active_alerts(alert_type: Optional[str] = None) -> List[Dict]:
    """
    Obtiene todas las alertas activas.
    
    Args:
        alert_type: Filtrar por tipo ('flood' o 'drought'), None para todas
        
    Returns:
        Lista de alertas activas
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if alert_type:
        cursor.execute("""
            SELECT * FROM active_alerts
            WHERE alert_type = ?
            ORDER BY probability DESC, triggered_at DESC
        """, (alert_type,))
    else:
        cursor.execute("""
            SELECT * FROM active_alerts
            ORDER BY probability DESC, triggered_at DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_station_alert(station_id: int, alert_type: str) -> Optional[Dict]:
    """
    Obtiene la alerta de una estación específica.
    
    Args:
        station_id: ID de la estación
        alert_type: Tipo de alerta ('flood' o 'drought')
        
    Returns:
        Alerta si existe, None si no
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM active_alerts
        WHERE station_id = ? AND alert_type = ?
    """, (station_id, alert_type))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_all_alerts_by_station() -> Dict[int, Dict[str, Dict]]:
    """
    Obtiene TODAS las alertas agrupadas por estación para evitar consultas individuales.
    
    Returns:
        Dict con estructura: {station_id: {'flood': {...}, 'drought': {...}}}
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM active_alerts
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Agrupar por estación
    alerts_map = {}
    for row in rows:
        station_id = row['station_id']
        alert_type = row['alert_type']
        
        if station_id not in alerts_map:
            alerts_map[station_id] = {}
        
        alerts_map[station_id][alert_type] = dict(row)
    
    return alerts_map


if __name__ == "__main__":
    # Testing
    logging.basicConfig(level=logging.INFO)
    init_database()
    print("Database initialized successfully!")
