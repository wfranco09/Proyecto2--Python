"""
API Router para análisis de riesgo climático
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from core.analysis.risk_analyzer import analyze_and_save_risk, RiskAnalyzer

router = APIRouter(prefix="/api/risk", tags=["risk"])
logger = logging.getLogger(__name__)


@router.get("/analyze")
async def analyze_risk(
    station_id: Optional[int] = Query(
        None, 
        description="ID de estación específica (1-15), o None para todas",
        ge=1,
        le=15
    ),
    hours: int = Query(
        24,
        description="Horas de histórico para comparar",
        ge=3,
        le=168  # Máximo 1 semana
    )
):
    """
    Analiza el riesgo climático basado en datos históricos.
    
    - **station_id**: ID de estación específica (1-15), o omitir para analizar todas
    - **hours**: Horas de histórico para comparar (default: 24)
    
    Returns:
        Análisis de riesgo con nivel, score, factores y recomendaciones
    """
    try:
        analyzer = RiskAnalyzer()
        
        if station_id:
            # Análisis de una estación específica
            analysis = analyzer.analyze_station_risk(station_id, hours)
            
            if not analysis:
                raise HTTPException(
                    status_code=404,
                    detail=f"No hay datos suficientes para la estación {station_id}"
                )
            
            return {
                'station_id': analysis.station_id,
                'station_name': analysis.station_name,
                'timestamp': analysis.timestamp,
                'risk_level': analysis.risk_level.value,
                'risk_score': analysis.risk_score,
                'factors': analysis.factors,
                'trends': analysis.trends,
                'recommendations': analysis.recommendations,
                'current_metrics': analysis.current_metrics,
                'historical_avg': analysis.historical_avg
            }
        else:
            # Análisis de todas las estaciones
            result = analyze_and_save_risk()
            return result
            
    except Exception as e:
        logger.error(f"Error analizando riesgo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_risk_summary():
    """
    Obtiene un resumen del riesgo actual en todas las estaciones.
    
    Returns:
        Resumen con contadores por nivel de riesgo y top 5 estaciones críticas
    """
    try:
        result = analyze_and_save_risk()
        
        # Filtrar solo estaciones con riesgo alto o crítico
        high_risk_stations = [
            s for s in result['stations']
            if s['risk_level'] in ['alto', 'critico']
        ]
        
        return {
            'timestamp': result['timestamp'],
            'total_stations': result['total_stations'],
            'risk_summary': result['risk_summary'],
            'high_risk_count': len(high_risk_stations),
            'high_risk_stations': high_risk_stations[:5],  # Top 5
            'overall_risk': _calculate_overall_risk(result['risk_summary'])
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de riesgo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/station/{station_id}/history")
async def get_station_risk_history(
    station_id: int,
    hours: int = Query(24, description="Horas de histórico", ge=1, le=168)
):
    """
    Obtiene el histórico de análisis de riesgo para una estación.
    
    - **station_id**: ID de la estación (1-15)
    - **hours**: Horas de histórico (default: 24)
    
    Returns:
        Histórico de métricas y análisis de tendencias
    """
    try:
        from core.database.weather_db import get_latest_data_by_station
        
        # Obtener datos históricos
        historical_data = get_latest_data_by_station(station_id, limit=hours)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"No hay datos históricos para la estación {station_id}"
            )
        
        # Analizar riesgo actual
        analyzer = RiskAnalyzer()
        current_analysis = analyzer.analyze_station_risk(station_id, hours)
        
        # Preparar respuesta con histórico
        history = []
        for record in historical_data:
            history.append({
                'timestamp': record.get('timestamp'),
                'date': record.get('date'),
                'hour': record.get('hour'),
                'temperature': record.get('temperature'),
                'humidity': record.get('humidity'),
                'precipitation_total': record.get('precipitation_total'),
                'wind_speed': record.get('wind_speed'),
                'pressure': record.get('pressure')
            })
        
        return {
            'station_id': station_id,
            'station_name': historical_data[0].get('station_name'),
            'current_analysis': {
                'risk_level': current_analysis.risk_level.value if current_analysis else 'unknown',
                'risk_score': current_analysis.risk_score if current_analysis else 0,
                'trends': current_analysis.trends if current_analysis else {}
            } if current_analysis else None,
            'history': history,
            'hours_analyzed': len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo histórico de estación {station_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds")
async def get_risk_thresholds():
    """
    Obtiene los umbrales de riesgo configurados para cada métrica.
    
    Returns:
        Diccionario con umbrales por métrica
    """
    return {
        'thresholds': RiskAnalyzer.THRESHOLDS,
        'risk_levels': {
            'bajo': '0-29 puntos',
            'moderado': '30-59 puntos',
            'alto': '60-79 puntos',
            'critico': '80-100 puntos'
        },
        'description': 'Umbrales de riesgo climático para Panamá'
    }


def _calculate_overall_risk(risk_summary: dict) -> str:
    """Calcula el nivel de riesgo general del sistema"""
    if risk_summary['critico'] > 0:
        return 'critico'
    elif risk_summary['alto'] >= 3:
        return 'alto'
    elif risk_summary['moderado'] >= 5:
        return 'moderado'
    else:
        return 'bajo'
