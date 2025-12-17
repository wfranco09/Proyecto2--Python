"""
RiskCalculator Service
Calculates risk scores and detects anomalies
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, List, Dict
from datetime import datetime
from scipy import stats

from config import (
    RISK_LEVELS,
    FLOOD_THRESHOLD_LOW,
    FLOOD_THRESHOLD_HIGH,
    DROUGHT_THRESHOLD_LOW,
    DROUGHT_THRESHOLD_HIGH,
)

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Service for calculating risk metrics and detecting anomalies
    """

    def __init__(self):
        self.risk_levels = RISK_LEVELS

    def compare_with_baseline(
        self, current_value: float, baseline: pd.Series, variable: str = "LLUVIA"
    ) -> Dict:
        """
        Compare current value with historical baseline

        Returns:
            {
                'current': float,
                'baseline_mean': float,
                'baseline_std': float,
                'z_score': float,
                'percentile': float,
                'anomaly': bool
            }
        """
        try:
            baseline_mean = baseline.mean()
            baseline_std = baseline.std()

            if baseline_std == 0:
                z_score = 0
                percentile = 50
            else:
                z_score = (current_value - baseline_mean) / baseline_std
                percentile = stats.norm.cdf(z_score) * 100

            # Anomalía si Z-score > 2 o < -2
            is_anomaly = abs(z_score) > 2

            return {
                "current": float(current_value),
                "baseline_mean": float(baseline_mean),
                "baseline_std": float(baseline_std),
                "z_score": float(z_score),
                "percentile": float(percentile),
                "anomaly": is_anomaly,
            }

        except Exception as e:
            logger.error(f" Error comparing with baseline: {str(e)}")
            return {
                "current": float(current_value),
                "baseline_mean": 0,
                "baseline_std": 0,
                "z_score": 0,
                "percentile": 50,
                "anomaly": False,
            }

    def detect_anomalies(
        self, data: pd.DataFrame, variable: str = "LLUVIA", z_threshold: float = 2.0
    ) -> List[Dict]:
        """
        Detect anomalies in data using Z-score method

        Returns:
            List of anomalies with station and details
        """
        try:
            if variable not in data.columns:
                logger.warning(f" Variable {variable} not found in data")
                return []

            anomalies = []

            # Agrupar por estación
            for station_id, group in data.groupby("station_id" if "station_id" in data.columns else 0):
                values = group[variable].dropna()

                if len(values) < 3:
                    continue

                # Calcular puntuaciones Z
                z_scores = np.abs(stats.zscore(values))

                # Encontrar anomalías
                anomaly_indices = np.where(z_scores > z_threshold)[0]

                for idx in anomaly_indices:
                    value = values.iloc[idx]
                    z_score = z_scores[idx]

                    anomalies.append(
                        {
                            "station_id": int(station_id),
                            "variable": variable,
                            "value": float(value),
                            "z_score": float(z_score),
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": "high" if z_score > 3 else "medium",
                        }
                    )

            logger.info(f" Detected {len(anomalies)} anomalies in {variable}")
            return anomalies

        except Exception as e:
            logger.error(f" Error detecting anomalies: {str(e)}")
            return []

    def generate_risk_alerts(self, predictions: List[Dict]) -> List[Dict]:
        """
        Generate alerts based on risk predictions

        Returns:
            List of alerts
        """
        try:
            alerts = []

            for pred in predictions:
                probability = pred.get("probability", 0)
                risk_level = pred.get("risk_level", "GREEN")

                # Generar alerta si el riesgo es alto
                if risk_level == "RED" or probability > FLOOD_THRESHOLD_HIGH:
                    alert = {
                        "station_id": pred.get("station_id"),
                        "station_name": pred.get("station_name"),
                        "risk_type": "flood",  # or drought
                        "probability": probability,
                        "risk_level": risk_level,
                        "message": self._generate_alert_message(probability, risk_level),
                        "timestamp": datetime.utcnow().isoformat(),
                        "action_required": risk_level == "RED",
                    }

                    alerts.append(alert)

            logger.info(f" Generated {len(alerts)} alerts")
            return alerts

        except Exception as e:
            logger.error(f" Error generating alerts: {str(e)}")
            return []

    def _generate_alert_message(self, probability: float, risk_level: str) -> str:
        """Generate human-readable alert message"""
        if risk_level == "RED":
            return f" HIGH RISK - Probability: {probability:.1%}. Immediate action recommended."
        elif risk_level == "YELLOW":
            return f" MEDIUM RISK - Probability: {probability:.1%}. Monitor closely."
        else:
            return f" LOW RISK - Probability: {probability:.1%}"

    def calculate_station_risk_aggregate(
        self, predictions: Dict, lookback_hours: int = 24
    ) -> Dict:
        """
        Calculate aggregated risk for each station
        Combines current prediction with recent trend

        Returns:
            {
                'station_id': {
                    'current_risk': float,
                    'trend': 'increasing' | 'stable' | 'decreasing',
                    'alert_status': 'red' | 'yellow' | 'green',
                    'confidence': float
                }
            }
        """
        try:
            aggregated = {}

            for station_pred in predictions.get("flood", []):
                station_id = station_pred["station_id"]
                probability = station_pred["probability"]

                aggregated[station_id] = {
                    "current_risk": probability,
                    "trend": "stable",  # TODO: calculate from history
                    "alert_status": station_pred["risk_level"].lower(),
                    "confidence": 0.95,  # TODO: from model
                }

            return aggregated

        except Exception as e:
            logger.error(f" Error calculating aggregated risk: {str(e)}")
            return {}

    def get_top_risk_stations(
        self, predictions: List[Dict], risk_type: str = "flood", top_n: int = 5
    ) -> List[Dict]:
        """
        Get top N stations with highest risk

        Returns:
            List of stations sorted by risk
        """
        try:
            # Ordenar por probabilidad
            sorted_preds = sorted(
                predictions, key=lambda x: x.get("probability", 0), reverse=True
            )

            # Retornar los primeros N
            return sorted_preds[:top_n]

        except Exception as e:
            logger.error(f" Error getting top risk stations: {str(e)}")
            return []

    def calculate_trend(
        self, historical_predictions: List[Dict], current_probability: float
    ) -> str:
        """
        Calculate risk trend
        """
        try:
            if not historical_predictions:
                return "stable"

            avg_historical = np.mean([p.get("probability", 0) for p in historical_predictions])

            diff = current_probability - avg_historical

            if diff > 0.1:
                return "increasing"
            elif diff < -0.1:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f" Error calculating trend: {str(e)}")
            return "unknown"
