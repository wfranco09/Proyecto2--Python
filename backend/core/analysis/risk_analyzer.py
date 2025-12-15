"""
Analizador de Riesgo Climático
Compara métricas actuales con históricas y predice nivel de riesgo
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Niveles de riesgo climático"""
    BAJO = "bajo"
    MODERADO = "moderado"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass
class RiskAnalysis:
    """Resultado del análisis de riesgo"""
    station_id: int
    station_name: str
    timestamp: str
    risk_level: RiskLevel
    risk_score: float  # 0-100
    factors: List[Dict]  # Factores que contribuyen al riesgo
    trends: Dict  # Tendencias de las métricas
    recommendations: List[str]
    current_metrics: Dict
    historical_avg: Dict


class RiskAnalyzer:
    """Analizador de riesgo basado en datos históricos"""
    
    # Umbrales de riesgo para Panamá
    THRESHOLDS = {
        "temperature": {
            "normal_max": 32.0,  # °C
            "high": 35.0,
            "critical": 38.0
        },
        "humidity": {
            "normal_min": 60.0,  # %
            "normal_max": 85.0,
            "high": 90.0,
            "critical": 95.0
        },
        "precipitation_total": {
            "moderate": 5.0,  # mm/hora
            "high": 15.0,
            "critical": 30.0
        },
        "wind_speed": {
            "moderate": 20.0,  # km/h
            "high": 40.0,
            "critical": 60.0
        },
        "pressure": {
            "low_critical": 1005.0,  # hPa
            "low_warning": 1010.0,
            "normal_min": 1013.0,
            "normal_max": 1020.0
        }
    }
    
    def __init__(self):
        """Inicializa el analizador"""
        from core.database.weather_db import (
            get_latest_data_by_station,
            get_data_by_date_range
        )
        self.get_latest = get_latest_data_by_station
        self.get_range = get_data_by_date_range
    
    def analyze_station_risk(
        self, 
        station_id: int, 
        hours_to_compare: int = 24
    ) -> Optional[RiskAnalysis]:
        """
        Analiza el riesgo para una estación comparando con histórico.
        
        Args:
            station_id: ID de la estación
            hours_to_compare: Horas de histórico para comparar (default: 24)
            
        Returns:
            RiskAnalysis con el resultado del análisis
        """
        try:
            # Obtener datos históricos
            historical_data = self.get_latest(station_id, limit=hours_to_compare)
            
            if not historical_data or len(historical_data) == 0:
                logger.warning(f"No hay datos históricos para estación {station_id}")
                return None
            
            # El primer registro es el más reciente
            current = historical_data[0]
            
            # Calcular promedios históricos (excluyendo el actual)
            historical_avg = self._calculate_averages(historical_data[1:])
            
            # Analizar cada métrica
            factors = []
            risk_scores = []
            
            # 1. Temperatura
            temp_risk = self._analyze_temperature(
                current.get('temperature'),
                historical_avg.get('temperature')
            )
            if temp_risk:
                factors.append(temp_risk)
                risk_scores.append(temp_risk['score'])
            
            # 2. Humedad
            humidity_risk = self._analyze_humidity(
                current.get('humidity'),
                historical_avg.get('humidity')
            )
            if humidity_risk:
                factors.append(humidity_risk)
                risk_scores.append(humidity_risk['score'])
            
            # 3. Precipitación
            precip_risk = self._analyze_precipitation(
                current.get('precipitation_total'),
                historical_avg.get('precipitation_total')
            )
            if precip_risk:
                factors.append(precip_risk)
                risk_scores.append(precip_risk['score'])
            
            # 4. Viento
            wind_risk = self._analyze_wind(
                current.get('wind_speed'),
                historical_avg.get('wind_speed')
            )
            if wind_risk:
                factors.append(wind_risk)
                risk_scores.append(wind_risk['score'])
            
            # 5. Presión
            pressure_risk = self._analyze_pressure(
                current.get('pressure'),
                historical_avg.get('pressure')
            )
            if pressure_risk:
                factors.append(pressure_risk)
                risk_scores.append(pressure_risk['score'])
            
            # Calcular score general y nivel de riesgo
            overall_score = max(risk_scores) if risk_scores else 0
            risk_level = self._calculate_risk_level(overall_score)
            
            # Calcular tendencias
            trends = self._calculate_trends(historical_data)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(
                risk_level, 
                factors, 
                trends
            )
            
            return RiskAnalysis(
                station_id=station_id,
                station_name=current.get('station_name', f'Estación {station_id}'),
                timestamp=current.get('timestamp'),
                risk_level=risk_level,
                risk_score=round(overall_score, 2),
                factors=factors,
                trends=trends,
                recommendations=recommendations,
                current_metrics={
                    'temperature': current.get('temperature'),
                    'humidity': current.get('humidity'),
                    'precipitation_total': current.get('precipitation_total'),
                    'wind_speed': current.get('wind_speed'),
                    'pressure': current.get('pressure')
                },
                historical_avg=historical_avg
            )
            
        except Exception as e:
            logger.error(f"Error analizando riesgo para estación {station_id}: {e}")
            return None
    
    def analyze_all_stations(
        self, 
        hours_to_compare: int = 24
    ) -> List[RiskAnalysis]:
        """
        Analiza el riesgo para todas las estaciones.
        
        Args:
            hours_to_compare: Horas de histórico para comparar
            
        Returns:
            Lista de análisis de riesgo por estación
        """
        results = []
        
        # IDs de las +250 estaciones en Panamá
        station_ids = range(1, 16)
        
        for station_id in station_ids:
            analysis = self.analyze_station_risk(station_id, hours_to_compare)
            if analysis:
                results.append(analysis)
        
        # Ordenar por score de riesgo (mayor a menor)
        results.sort(key=lambda x: x.risk_score, reverse=True)
        
        return results
    
    def _calculate_averages(self, data: List[Dict]) -> Dict:
        """Calcula promedios de métricas históricas"""
        if not data:
            return {}
        
        metrics = ['temperature', 'humidity', 'precipitation_total', 
                   'wind_speed', 'pressure']
        averages = {}
        
        for metric in metrics:
            values = [d.get(metric) for d in data if d.get(metric) is not None]
            if values:
                averages[metric] = sum(values) / len(values)
        
        return averages
    
    def _analyze_temperature(
        self, 
        current: Optional[float], 
        historical_avg: Optional[float]
    ) -> Optional[Dict]:
        """Analiza riesgo por temperatura"""
        if current is None:
            return None
        
        score = 0
        severity = "normal"
        message = f"Temperatura: {current}°C"
        
        # Verificar umbrales absolutos
        if current >= self.THRESHOLDS['temperature']['critical']:
            score = 90
            severity = "critical"
            message = f"Temperatura crítica: {current}°C"
        elif current >= self.THRESHOLDS['temperature']['high']:
            score = 70
            severity = "high"
            message = f"Temperatura alta: {current}°C"
        elif current >= self.THRESHOLDS['temperature']['normal_max']:
            score = 40
            severity = "moderate"
            message = f"Temperatura sobre el promedio: {current}°C"
        
        # Comparar con histórico
        if historical_avg:
            diff = current - historical_avg
            if diff > 5:
                score = max(score, 50)
                message += f" (+{diff:.1f}°C vs promedio)"
        
        return {
            'metric': 'temperature',
            'score': score,
            'severity': severity,
            'message': message,
            'current': current,
            'historical_avg': historical_avg
        }
    
    def _analyze_humidity(
        self, 
        current: Optional[float], 
        historical_avg: Optional[float]
    ) -> Optional[Dict]:
        """Analiza riesgo por humedad"""
        if current is None:
            return None
        
        score = 0
        severity = "normal"
        message = f"Humedad: {current}%"
        
        if current >= self.THRESHOLDS['humidity']['critical']:
            score = 80
            severity = "critical"
            message = f"Humedad crítica: {current}%"
        elif current >= self.THRESHOLDS['humidity']['high']:
            score = 60
            severity = "high"
            message = f"Humedad muy alta: {current}%"
        elif current < self.THRESHOLDS['humidity']['normal_min']:
            score = 30
            severity = "moderate"
            message = f"Humedad baja: {current}%"
        
        return {
            'metric': 'humidity',
            'score': score,
            'severity': severity,
            'message': message,
            'current': current,
            'historical_avg': historical_avg
        }
    
    def _analyze_precipitation(
        self, 
        current: Optional[float], 
        historical_avg: Optional[float]
    ) -> Optional[Dict]:
        """Analiza riesgo por precipitación"""
        if current is None:
            return None
        
        score = 0
        severity = "normal"
        message = f"Precipitación: {current}mm"
        
        if current >= self.THRESHOLDS['precipitation_total']['critical']:
            score = 95
            severity = "critical"
            message = f"Lluvia crítica: {current}mm/h"
        elif current >= self.THRESHOLDS['precipitation_total']['high']:
            score = 75
            severity = "high"
            message = f"Lluvia intensa: {current}mm/h"
        elif current >= self.THRESHOLDS['precipitation_total']['moderate']:
            score = 50
            severity = "moderate"
            message = f"Lluvia moderada: {current}mm/h"
        elif current > 0:
            score = 20
            severity = "low"
            message = f"Lluvia ligera: {current}mm/h"
        
        return {
            'metric': 'precipitation',
            'score': score,
            'severity': severity,
            'message': message,
            'current': current,
            'historical_avg': historical_avg
        }
    
    def _analyze_wind(
        self, 
        current: Optional[float], 
        historical_avg: Optional[float]
    ) -> Optional[Dict]:
        """Analiza riesgo por viento"""
        if current is None:
            return None
        
        score = 0
        severity = "normal"
        message = f"Viento: {current} km/h"
        
        if current >= self.THRESHOLDS['wind_speed']['critical']:
            score = 85
            severity = "critical"
            message = f"Vientos peligrosos: {current} km/h"
        elif current >= self.THRESHOLDS['wind_speed']['high']:
            score = 65
            severity = "high"
            message = f"Vientos fuertes: {current} km/h"
        elif current >= self.THRESHOLDS['wind_speed']['moderate']:
            score = 40
            severity = "moderate"
            message = f"Vientos moderados: {current} km/h"
        
        return {
            'metric': 'wind',
            'score': score,
            'severity': severity,
            'message': message,
            'current': current,
            'historical_avg': historical_avg
        }
    
    def _analyze_pressure(
        self, 
        current: Optional[float], 
        historical_avg: Optional[float]
    ) -> Optional[Dict]:
        """Analiza riesgo por presión atmosférica"""
        if current is None:
            return None
        
        score = 0
        severity = "normal"
        message = f"Presión: {current} hPa"
        
        if current <= self.THRESHOLDS['pressure']['low_critical']:
            score = 80
            severity = "critical"
            message = f"Presión muy baja: {current} hPa (tormenta posible)"
        elif current <= self.THRESHOLDS['pressure']['low_warning']:
            score = 55
            severity = "high"
            message = f"Presión baja: {current} hPa"
        elif current < self.THRESHOLDS['pressure']['normal_min']:
            score = 30
            severity = "moderate"
            message = f"Presión bajo el promedio: {current} hPa"
        
        return {
            'metric': 'pressure',
            'score': score,
            'severity': severity,
            'message': message,
            'current': current,
            'historical_avg': historical_avg
        }
    
    def _calculate_trends(self, historical_data: List[Dict]) -> Dict:
        """Calcula tendencias de las últimas horas"""
        if len(historical_data) < 3:
            return {}
        
        trends = {}
        metrics = ['temperature', 'humidity', 'precipitation_total', 
                   'wind_speed', 'pressure']
        
        for metric in metrics:
            # Tomar últimos 3 registros
            recent = [d.get(metric) for d in historical_data[:3] 
                     if d.get(metric) is not None]
            
            if len(recent) >= 2:
                # Calcular tendencia (simple: comparar primero vs último)
                change = recent[0] - recent[-1]
                trend = "estable"
                
                if abs(change) > 0.5:  # Umbral de cambio significativo
                    trend = "subiendo" if change > 0 else "bajando"
                
                trends[metric] = {
                    'trend': trend,
                    'change': round(change, 2),
                    'recent_values': recent
                }
        
        return trends
    
    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Calcula el nivel de riesgo basado en el score"""
        if score >= 80:
            return RiskLevel.CRITICO
        elif score >= 60:
            return RiskLevel.ALTO
        elif score >= 30:
            return RiskLevel.MODERADO
        else:
            return RiskLevel.BAJO
    
    def _generate_recommendations(
        self, 
        risk_level: RiskLevel, 
        factors: List[Dict],
        trends: Dict
    ) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones por nivel de riesgo general
        if risk_level == RiskLevel.CRITICO:
            recommendations.append(" ALERTA CRÍTICA: Condiciones climáticas peligrosas")
            recommendations.append("Evitar actividades al aire libre")
            recommendations.append("Mantenerse informado sobre alertas oficiales")
        elif risk_level == RiskLevel.ALTO:
            recommendations.append(" Precaución: Condiciones climáticas adversas")
            recommendations.append("Limitar actividades al aire libre")
        elif risk_level == RiskLevel.MODERADO:
            recommendations.append(" Atención: Monitorear condiciones climáticas")
        else:
            recommendations.append(" Condiciones normales")
        
        # Recomendaciones específicas por factor
        for factor in factors:
            if factor['severity'] in ['critical', 'high']:
                metric = factor['metric']
                
                if metric == 'precipitation':
                    recommendations.append(" Riesgo de inundaciones - evitar zonas bajas")
                elif metric == 'wind':
                    recommendations.append(" Vientos fuertes - asegurar objetos sueltos")
                elif metric == 'temperature':
                    recommendations.append(" Temperatura extrema - hidratarse adecuadamente")
                elif metric == 'pressure':
                    recommendations.append(" Presión baja - posible tormenta cercana")
        
        # Recomendaciones por tendencias
        if trends.get('precipitation_total', {}).get('trend') == 'subiendo':
            recommendations.append(" Precipitación en aumento - prepararse para lluvia")
        
        if trends.get('wind_speed', {}).get('trend') == 'subiendo':
            recommendations.append(" Vientos en aumento - tomar precauciones")
        
        return recommendations


def analyze_and_save_risk(station_id: Optional[int] = None) -> Dict:
    """
    Analiza riesgo y guarda en base de datos.
    
    Args:
        station_id: ID de estación específica, o None para todas
        
    Returns:
        Diccionario con resultados del análisis
    """
    analyzer = RiskAnalyzer()
    
    if station_id:
        analysis = analyzer.analyze_station_risk(station_id)
        results = [analysis] if analysis else []
    else:
        results = analyzer.analyze_all_stations()
    
    # Preparar respuesta
    response = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_stations': len(results),
        'risk_summary': {
            'critico': 0,
            'alto': 0,
            'moderado': 0,
            'bajo': 0
        },
        'stations': []
    }
    
    for analysis in results:
        # Contar por nivel de riesgo
        response['risk_summary'][analysis.risk_level.value] += 1
        
        # Agregar análisis de estación
        response['stations'].append({
            'station_id': analysis.station_id,
            'station_name': analysis.station_name,
            'risk_level': analysis.risk_level.value,
            'risk_score': analysis.risk_score,
            'factors': analysis.factors,
            'trends': analysis.trends,
            'recommendations': analysis.recommendations,
            'current_metrics': analysis.current_metrics,
            'historical_avg': analysis.historical_avg
        })
    
    return response


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Probar análisis
    print(" Analizando riesgo climático...\n")
    
    result = analyze_and_save_risk()
    
    print(f"Análisis completado:")
    print(f"  Total estaciones: {result['total_stations']}")
    print(f"  Riesgo crítico: {result['risk_summary']['critico']}")
    print(f"  Riesgo alto: {result['risk_summary']['alto']}")
    print(f"  Riesgo moderado: {result['risk_summary']['moderado']}")
    print(f"  Riesgo bajo: {result['risk_summary']['bajo']}\n")
    
    # Mostrar estaciones con mayor riesgo
    print(" Estaciones con mayor riesgo:\n")
    for station in result['stations'][:5]:
        print(f"  {station['station_name']}")
        print(f"    Nivel: {station['risk_level'].upper()} ({station['risk_score']}/100)")
        print(f"    Factores: {len(station['factors'])}")
        for factor in station['factors'][:2]:
            print(f"      - {factor['message']}")
        print()
