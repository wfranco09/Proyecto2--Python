"""
API router para endpoints de estaciones respaldados por los servicios
"""

from datetime import datetime
import logging
from typing import Optional, List

import pandas as pd
from fastapi import APIRouter, HTTPException

from services import Predictor, RiskCalculator
from config import STATIONS, DATA_CLEAN_PATH
from core.database.raindrop_db import (
    get_all_stations_latest, 
    get_latest_data_by_station,
    upsert_alert,
    remove_alert,
    get_station_alert,
    get_all_alerts_by_station
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_station_info(station_id: int) -> Optional[dict]:
    """Obtiene la metadata de la estación desde la configuración."""
    return next((s for s in STATIONS if s.get("id") == station_id), None)


def _get_current_conditions(station_id: int) -> dict:
    """Lee condiciones recientes desde el dataset limpio, con tolerancia a esquemas."""
    try:
        file_path = DATA_CLEAN_PATH / "master_dataset_final.csv"
        if not file_path.exists():
            raise FileNotFoundError()

        df = pd.read_csv(file_path)

        # Detectar columnas posibles
        station_col = "station_id" if "station_id" in df.columns else "ESTACION" if "ESTACION" in df.columns else None
        if station_col:
            station_df = df[df[station_col] == station_id]
        else:
            station_df = df

        if station_df.empty:
            station_df = df

        row = station_df.iloc[-1]
        ts_col = "FECHA" if "FECHA" in station_df.columns else "date" if "date" in station_df.columns else None
        ts_value = row[ts_col] if ts_col else datetime.utcnow().isoformat()

        return {
            "temperature": float(row.get("TEMP", 0)),
            "humidity": float(row.get("HUMEDAD", 0)),
            "rainfall": float(row.get("LLUVIA", 0)),
            "wind_speed": float(row.get("VIENTO", 0)),
            "timestamp": str(ts_value),
        }
    except Exception:
        return {
            "temperature": 0,
            "humidity": 0,
            "rainfall": 0,
            "wind_speed": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


def _manage_alert(station_id: int, station_name: str, alert_type: str, 
                  probability: float, risk_level: str) -> None:
    """
    Gestiona automáticamente las alertas basándose en la probabilidad.
    - Si probabilidad >= 50%: Crea/actualiza alerta
    - Si probabilidad < 51%: Elimina alerta si existe
    
    Args:
        station_id: ID de la estación
        station_name: Nombre de la estación
        alert_type: 'flood' o 'drought'
        probability: Probabilidad del riesgo (0.0 - 1.0)
        risk_level: Nivel de riesgo (GREEN, YELLOW, RED)
    """
    try:
        if probability >= 0.50:
            # Crear o actualizar alerta
            upsert_alert(station_id, station_name, alert_type, risk_level, probability)
        else:
            # Eliminar alerta si existe
            remove_alert(station_id, alert_type)
    except Exception as e:
        logger.warning(f"Error gestionando alerta para estación {station_id}: {e}")


@router.get("")
async def list_all_stations():
    """Retorna listado de estaciones con riesgo actual basado en datos reales de Meteosource."""
    try:
        # Obtener datos reales de todas las estaciones
        all_stations_data = get_all_stations_latest()
        
        predictor = Predictor()
        
        # Si no hay datos en la BD, devolver datos básicos de configuración
        if not all_stations_data:
            logger.warning(" No hay datos en la base de datos. Mostrando estaciones configuradas sin datos.")
            
            data = []
            for station in STATIONS:
                data.append({
                    "id": station.get("id"),
                    "name": station.get("name"),
                    "region": station.get("region"),
                    "lat": station.get("lat"),
                    "lon": station.get("lon"),
                    "elevation": station.get("elevation", 0),
                    "flood_risk": {
                        "probability": 0.0,
                        "level": "GREEN",
                        "alert": False,
                    },
                    "drought_risk": {
                        "probability": 0.0,
                        "level": "GREEN",
                        "alert": False,
                    },
                })
            
            return {
                "total_stations": len(data),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data,
                "data_source": "configuration",
                "warning": "No hay datos de Meteosource. Ejecuta el pipeline para obtener datos."
            }
        
        # Crear mapa de datos por estación
        station_data_map = {s["station_id"]: s for s in all_stations_data}
        
        # Cargar TODAS las alertas de una vez (evita 500+ consultas individuales)
        all_alerts = get_all_alerts_by_station()
        
        # Listas para operaciones batch de alertas
        alerts_to_upsert = []
        alerts_to_remove = []
        
        data = []
        for station in STATIONS:
            station_id = station.get("id")
            station_data = station_data_map.get(station_id)
            
            if not station_data:
                # Estación sin datos
                data.append({
                    "id": station_id,
                    "name": station.get("name"),
                    "region": station.get("region"),
                    "lat": station.get("lat"),
                    "lon": station.get("lon"),
                    "elevation": station.get("elevation", 0),
                    "flood_risk": {
                        "probability": 0.0,
                        "level": "GREEN",
                        "alert": False,
                    },
                    "drought_risk": {
                        "probability": 0.0,
                        "level": "GREEN",
                        "alert": False,
                    },
                })
                continue
            
            # Calcular probabilidades basadas en datos reales
            # Validar que los valores no sean None
            rainfall = station_data.get("precipitation_total") or 0.0
            humidity = station_data.get("humidity") or 0.0
            
            # Asegurar que sean float
            rainfall = float(rainfall)
            humidity = float(humidity)
            
            # Riesgo de inundación
            flood_prob = min(0.95, (rainfall / 50.0) * 0.6 + (humidity / 100.0) * 0.4)
            flood_level = predictor._get_risk_level(flood_prob)
            
            # Riesgo de sequía
            drought_prob = min(0.95, (1 - rainfall / 50.0) * 0.6 + (1 - humidity / 100.0) * 0.4)
            drought_level = predictor._get_risk_level(drought_prob)
            
            # Preparar operaciones de alertas (no ejecutar todavía)
            if flood_prob >= 0.50:
                alerts_to_upsert.append((station_id, station.get("name"), "flood", flood_level, flood_prob))
            else:
                alerts_to_remove.append((station_id, "flood"))
            
            if drought_prob >= 0.50:
                alerts_to_upsert.append((station_id, station.get("name"), "drought", drought_level, drought_prob))
            else:
                alerts_to_remove.append((station_id, "drought"))
            
            # Obtener timestamps de alertas del mapa precargado
            station_alerts = all_alerts.get(station_id, {})
            flood_alert = station_alerts.get("flood")
            drought_alert = station_alerts.get("drought")
            
            data.append({
                "id": station_id,
                "name": station.get("name"),
                "region": station.get("region"),
                "lat": station.get("lat"),
                "lon": station.get("lon"),
                "elevation": station.get("elevation", 0),
                "flood_risk": {
                    "probability": round(flood_prob, 3),
                    "level": flood_level,
                    "alert": flood_prob >= 0.5,
                    "triggered_at": flood_alert["triggered_at"] if flood_alert else None,
                },
                "drought_risk": {
                    "probability": round(drought_prob, 3),
                    "level": drought_level,
                    "alert": drought_prob >= 0.5,
                    "triggered_at": drought_alert["triggered_at"] if drought_alert else None,
                },
                "current_conditions": {
                    "temperature": station_data.get("temperature"),
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "wind_speed": station_data.get("wind_speed"),
                    "summary": station_data.get("summary"),
                },
                "last_update": station_data.get("timestamp"),
            })
        
        # Ejecutar operaciones de alertas en batch (fuera del loop principal)
        # Esto evita bloquear la respuesta con operaciones de escritura
        try:
            for station_id, station_name, alert_type, risk_level, probability in alerts_to_upsert:
                _manage_alert(station_id, station_name, alert_type, probability, risk_level)
            for station_id, alert_type in alerts_to_remove:
                if all_alerts.get(station_id, {}).get(alert_type):  # Solo remover si existe
                    remove_alert(station_id, alert_type)
        except Exception as e:
            logger.warning(f"Error actualizando alertas en batch: {e}")
        
        return {
            "total_stations": len(data),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
            "data_source": "meteosource_realtime",
        }
    except Exception as e:
        logger.error(f"Error al listar estaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar datos de estaciones: {str(e)}")


@router.get("/{station_id}")
async def get_station(station_id: int):
    """Detalle de una estación con condiciones actuales y riesgo."""
    try:
        station_info = _get_station_info(station_id)
        if not station_info:
            raise HTTPException(status_code=404, detail=f"Estación {station_id} no encontrada")

        predictor = Predictor()
        risk_calculator = RiskCalculator()

        flood_pred = predictor.predict_single_station(station_id, "flood")
        drought_pred = predictor.predict_single_station(station_id, "drought")

        if not flood_pred or not drought_pred:
            raise HTTPException(status_code=503, detail="Predicciones no disponibles para la estación")

        flood_level = flood_pred.get("risk_level", predictor._get_risk_level(flood_pred.get("probability", 0)))
        drought_level = drought_pred.get("risk_level", predictor._get_risk_level(drought_pred.get("probability", 0)))

        return {
            "id": station_id,
            "name": station_info.get("name"),
            "lat": station_info.get("lat"),
            "lon": station_info.get("lon"),
            "elevation": station_info.get("elevation", 0),
            "region": station_info.get("region", ""),
            "current_conditions": _get_current_conditions(station_id),
            "risk_assessment": {
                "flood": {
                    "probability": round(flood_pred.get("probability", 0), 3),
                    "level": flood_level,
                    "alert": flood_level == "RED",
                    "message": risk_calculator._generate_alert_message(flood_pred.get("probability", 0), flood_level),
                },
                "drought": {
                    "probability": round(drought_pred.get("probability", 0), 3),
                    "level": drought_level,
                    "alert": drought_level == "RED",
                    "message": risk_calculator._generate_alert_message(drought_pred.get("probability", 0), drought_level),
                },
            },
            "trend": {
                "flood_trend": "stable",  # TODO: calcular con históricos
                "drought_trend": "stable",  # TODO: calcular con históricos
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estación {station_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar datos de la estación")


@router.get("/{station_id}/history")
async def get_station_history(station_id: int, days: int = 30, variable: Optional[str] = None):
    """Histórico simple por estación (últimos `days`)."""
    try:
        station_info = _get_station_info(station_id)
        if not station_info:
            raise HTTPException(status_code=404, detail=f"Estación {station_id} no encontrada")

        file_path = DATA_CLEAN_PATH / "master_dataset_final.csv"
        if not file_path.exists():
            return {"station_id": station_id, "station_name": station_info.get("name"), "days": days, "data": []}

        df = pd.read_csv(file_path)

        date_col = "FECHA" if "FECHA" in df.columns else "date" if "date" in df.columns else None
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])

        station_col = "station_id" if "station_id" in df.columns else "ESTACION" if "ESTACION" in df.columns else None
        if station_col:
            df = df[df[station_col] == station_id]

        if df.empty:
            return {"station_id": station_id, "station_name": station_info.get("name"), "days": days, "data": []}

        if date_col:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
            df = df[df[date_col] >= cutoff]

        history = []
        for _, row in df.iterrows():
            history.append({
                "date": row[date_col].strftime("%Y-%m-%d") if date_col else None,
                "temperature": float(row.get("TEMP", 0)),
                "humidity": float(row.get("HUMEDAD", 0)),
                "rainfall": float(row.get("LLUVIA", 0)),
                "wind_speed": float(row.get("VIENTO", 0)),
            })

        return {
            "station_id": station_id,
            "station_name": station_info.get("name"),
            "days": days,
            "data": history,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener histórico de estación {station_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar histórico")


@router.get("/alerts")
async def get_all_alerts():
    """Obtiene todas las alertas activas de todas las estaciones basadas en datos reales de Meteosource."""
    try:
        # Obtener último dato de cada estación
        all_stations_data = get_all_stations_latest()
        
        if not all_stations_data:
            return {
                "alerts": [],
                "total_alerts": 0,
                "data_source": "meteosource_realtime",
                "message": "No hay datos disponibles en la base de datos"
            }
        
        predictor = Predictor()
        all_alerts = []
        
        for station_data in all_stations_data:
            station_id = station_data.get("station_id")
            
            # Condiciones actuales reales - validar None
            rainfall = float(station_data.get("precipitation_total") or 0.0)
            humidity = float(station_data.get("humidity") or 0.0)
            
            # Calcular probabilidades basadas en condiciones
            # Riesgo de inundación: aumenta con lluvia y humedad alta
            flood_prob = min(0.95, (rainfall / 50.0) * 0.6 + (humidity / 100.0) * 0.4)
            
            # Riesgo de sequía: aumenta con poca lluvia y baja humedad  
            drought_prob = min(0.95, (1 - rainfall / 50.0) * 0.6 + (1 - humidity / 100.0) * 0.4)
            
            # Generar alerta de inundación si probabilidad >= 50%
            if flood_prob >= 0.5:
                level = predictor._get_risk_level(flood_prob)
                all_alerts.append({
                    "station_id": station_id,
                    "station_name": station_data.get("station_name"),
                    "type": "flood",
                    "probability": round(flood_prob, 3),
                    "level": level,
                    "triggered_at": station_data.get("timestamp"),
                    "message": f"Riesgo de inundación. Precipitación: {rainfall:.1f}mm",
                    "current_conditions": {
                        "temperature": station_data.get("temperature"),
                        "humidity": humidity,
                        "rainfall": rainfall,
                        "wind_speed": station_data.get("wind_speed"),
                    }
                })
            
            # Generar alerta de sequía si probabilidad >= 50%
            if drought_prob >= 0.5:
                level = predictor._get_risk_level(drought_prob)
                all_alerts.append({
                    "station_id": station_id,
                    "station_name": station_data.get("station_name"),
                    "type": "drought",
                    "probability": round(drought_prob, 3),
                    "level": level,
                    "triggered_at": station_data.get("timestamp"),
                    "message": f"Riesgo de sequía. Precipitación: {rainfall:.1f}mm, Humedad: {humidity:.0f}%",
                    "current_conditions": {
                        "temperature": station_data.get("temperature"),
                        "humidity": humidity,
                        "rainfall": rainfall,
                        "wind_speed": station_data.get("wind_speed"),
                    }
                })
        
        # Ordenar por probabilidad descendente
        all_alerts.sort(key=lambda x: x["probability"], reverse=True)
        
        return {
            "alerts": all_alerts,
            "total_alerts": len(all_alerts),
            "data_source": "meteosource_realtime",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al procesar alertas")


@router.get("/{station_id}/alerts")
async def get_station_alerts(station_id: int):
    """Alertas activas para una estación basadas en datos reales de Meteosource."""
    try:
        
        station_info = _get_station_info(station_id)
        if not station_info:
            raise HTTPException(status_code=404, detail=f"Estación {station_id} no encontrada")

        # Obtener datos reales de la base de datos
        latest_data = get_latest_data_by_station(station_id, limit=24)
        
        if not latest_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No hay datos disponibles para la estación {station_id}"
            )
        
        # Usar el dato más reciente
        latest = latest_data[0]
        
        # Condiciones actuales reales de Meteosource - validar None
        current_conditions = {
            "temperature": latest.get("temperature") or 0.0,
            "humidity": latest.get("humidity") or 0.0,
            "rainfall": latest.get("precipitation_total") or 0.0,
            "wind_speed": latest.get("wind_speed") or 0.0,
            "pressure": latest.get("pressure") or 0.0,
            "cloud_cover": latest.get("cloud_cover") or 0,
            "summary": latest.get("summary") or "",
            "timestamp": latest.get("timestamp") or "",
        }
        
        # Calcular probabilidades de riesgo basadas en condiciones reales
        predictor = Predictor()
        risk_calculator = RiskCalculator()

        # Intentar obtener predicciones del modelo ML
        flood_pred = predictor.predict_single_station(station_id, "flood")
        drought_pred = predictor.predict_single_station(station_id, "drought")
        
        # Si no hay modelo entrenado, calcular basado en condiciones actuales
        if not flood_pred:
            # Lógica basada en precipitación y humedad - validar None
            rainfall = float(latest.get("precipitation_total") or 0.0)
            humidity = float(latest.get("humidity") or 0.0)
            
            # Riesgo de inundación aumenta con lluvia y humedad alta
            flood_prob = min(0.95, (rainfall / 50.0) * 0.6 + (humidity / 100.0) * 0.4)
            flood_pred = {
                "probability": flood_prob,
                "risk_level": predictor._get_risk_level(flood_prob),
                "is_calculated": True,
            }
        else:
            flood_pred["is_calculated"] = False
            
        if not drought_pred:
            # Lógica basada en precipitación y humedad (inversa a inundación) - validar None
            rainfall = float(latest.get("precipitation_total") or 0.0)
            humidity = float(latest.get("humidity") or 0.0)
            
            # Riesgo de sequía aumenta con poca lluvia y baja humedad
            drought_prob = min(0.95, (1 - rainfall / 50.0) * 0.6 + (1 - humidity / 100.0) * 0.4)
            drought_pred = {
                "probability": drought_prob,
                "risk_level": predictor._get_risk_level(drought_prob),
                "is_calculated": True,
            }
        else:
            drought_pred["is_calculated"] = False

        alerts = []

        # Generar alertas basadas en condiciones reales
        if flood_pred:
            flood_prob = flood_pred.get("probability", 0)
            level = flood_pred.get("risk_level", "GREEN")
            is_alert = flood_prob >= 0.5  # Alerta cuando >= 50%
            
            if is_alert:
                # Mensaje personalizado basado en condiciones reales
                rainfall = float(latest.get("precipitation_total") or 0.0)
                message = f"Riesgo de inundación detectado. Precipitación actual: {rainfall:.1f}mm"
                
                alerts.append({
                    "type": "flood",
                    "probability": round(flood_prob, 3),
                    "level": level,
                    "triggered_at": latest.get("timestamp"),
                    "message": message,
                    "data_source": "calculated" if flood_pred.get("is_calculated") else "ml_model",
                    "recommended_actions": [
                        "Activar plan de evacuación en zonas bajas" if level == "RED" else "Monitorear situación",
                        "Monitorear actualizaciones meteorológicas",
                        "Asegurar drenajes y equipos críticos",
                        "Preparar suministros de emergencia" if level == "RED" else "Estar preparado",
                    ],
                    "current_conditions": current_conditions,
                })

        if drought_pred:
            drought_prob = drought_pred.get("probability", 0)
            level = drought_pred.get("risk_level", "GREEN")
            is_alert = drought_prob >= 0.5  # Alerta cuando >= 50%
            
            if is_alert:
                # Mensaje personalizado basado en condiciones reales
                rainfall = float(latest.get("precipitation_total") or 0.0)
                humidity = float(latest.get("humidity") or 0.0)
                message = f"Riesgo de sequía detectado. Precipitación: {rainfall:.1f}mm, Humedad: {humidity:.0f}%"
                
                alerts.append({
                    "type": "drought",
                    "probability": round(drought_prob, 3),
                    "level": level,
                    "triggered_at": latest.get("timestamp"),
                    "message": message,
                    "data_source": "calculated" if drought_pred.get("is_calculated") else "ml_model",
                    "recommended_actions": [
                        "Implementar medidas de ahorro de agua" if level == "RED" else "Usar agua responsablemente",
                        "Restringir riego y consumos no críticos" if level == "RED" else "Monitorear consumo",
                        "Monitorear reservas de agua",
                        "Planificar fuentes alternativas" if level == "RED" else "Tener plan de contingencia",
                    ],
                    "current_conditions": current_conditions,
                })

        return {
            "station_id": station_id,
            "station_name": station_info.get("name"),
            "station_info": {
                "lat": station_info.get("lat"),
                "lon": station_info.get("lon"),
                "elevation": station_info.get("elevation"),
                "region": station_info.get("region"),
            },
            "active_alerts": alerts,
            "total_alerts": len(alerts),
            "data_source": "meteosource_realtime",
            "last_update": latest.get("timestamp"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener alertas de estación {station_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar alertas")


@router.get("/alerts/active")
async def get_active_alerts(alert_type: Optional[str] = None):
    """
    Obtiene todas las alertas activas del sistema.
    
    Args:
        alert_type: Filtrar por tipo ('flood' o 'drought'), None para todas
        
    Returns:
        Lista de alertas activas con timestamps reales
    """
    try:
        from core.database.weather_db import get_active_alerts
        
        alerts = get_active_alerts(alert_type)
        
        return {
            "total_alerts": len(alerts),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error al obtener alertas activas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener alertas")
