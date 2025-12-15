"""
Predictor Service
Generates real-time predictions on latest data
"""

import pandas as pd
import numpy as np
import logging
import joblib
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from config import (
    DATA_CLEAN_PATH,
    MODELS_PATH,
    DATA_CACHE_PATH,
    FEATURE_COLUMNS,
    MODEL_FLOOD,
    MODEL_DROUGHT,
    LATEST_IMHPA,
    PREDICTIONS_CACHE,
    RISK_LEVELS,
)

logger = logging.getLogger(__name__)


class Predictor:
    """
    Service for generating real-time predictions on climate data
    """

    def __init__(self):
        self.data_path = DATA_CLEAN_PATH
        self.models_path = MODELS_PATH
        self.cache_path = DATA_CACHE_PATH
        self.feature_columns = FEATURE_COLUMNS
        self.models = {}
        self.risk_levels = RISK_LEVELS

    def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            logger.info(" Loading models...")

            model_flood_path = self.models_path / MODEL_FLOOD
            model_drought_path = self.models_path / MODEL_DROUGHT

            if not model_flood_path.exists() or not model_drought_path.exists():
                logger.error(" Models not found. Train models first.")
                return False

            self.models["flood"] = joblib.load(model_flood_path)
            self.models["drought"] = joblib.load(model_drought_path)

            logger.info(" Models loaded successfully")
            return True

        except Exception as e:
            logger.error(f" Error loading models: {str(e)}")
            return False

    def get_latest_data(self) -> Optional[pd.DataFrame]:
        """
        Get latest data for prediction
        Tries IMHPA first, falls back to ETESA historical
        """
        try:
            logger.info(" Fetching latest data...")

            # Intentar obtener últimos datos de IMHPA
            imhpa_file = self.data_path / LATEST_IMHPA
            if imhpa_file.exists():
                df = pd.read_csv(imhpa_file)
                logger.info(f"    Using IMHPA data ({len(df)} records)")
                return df

            # Recurrir al conjunto de datos maestro
            master_file = self.data_path / "master_dataset_final.csv"
            if master_file.exists():
                df = pd.read_csv(master_file)
                # Obtener últimos registros por estación
                df = df.sort_values("date" if "date" in df.columns else 0).drop_duplicates(
                    subset=["station_id"] if "station_id" in df.columns else [0], keep="last"
                )
                logger.info(f"    Using master dataset latest records ({len(df)} records)")
                return df

            logger.error(" No data available for prediction")
            return None

        except Exception as e:
            logger.error(f" Error fetching latest data: {str(e)}")
            return None

    def predict_all_stations(self, model_type: str = "flood") -> Optional[List[Dict]]:
        """
        Generate predictions for all stations

        Args:
            model_type: 'flood' or 'drought'

        Returns:
            List of predictions with station info and scores
        """
        try:
            logger.info(f" Generating {model_type} predictions...")

            # Cargar modelos si es necesario
            if not self.models:
                if not self.load_models():
                    return None

            # Obtener datos
            df = self.get_latest_data()
            if df is None:
                return None

            # Preparar características
            available_features = [col for col in self.feature_columns if col in df.columns]
            if not available_features:
                logger.error(f" No feature columns found in data")
                return None

            X = df[available_features].fillna(df[available_features].median())

            # Obtener modelo
            if model_type not in self.models:
                logger.error(f" Model {model_type} not loaded")
                return None

            model = self.models[model_type]

            # Generar predicciones
            predictions_proba = model.predict_proba(X)[:, 1]
            predictions_class = model.predict(X)

            # Construir resultados
            results = []
            for idx, row in df.iterrows():
                prob = float(predictions_proba[idx])
                risk_level = self._get_risk_level(prob)

                result = {
                    "station_id": int(row.get("station_id", idx)),
                    "station_name": str(row.get("nombre_estacion", row.get("station_name", f"Station_{idx}"))),
                    "lat": float(row.get("lat", 0)),
                    "lon": float(row.get("lon", 0)),
                    "probability": prob,
                    "risk_level": risk_level,
                    "class_prediction": int(predictions_class[idx]),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                results.append(result)

            logger.info(f" Generated {len(results)} {model_type} predictions")
            return results

        except Exception as e:
            logger.error(f" Error predicting: {str(e)}")
            return None

    def predict_single_station(self, station_id: int, model_type: str = "flood") -> Optional[Dict]:
        """Get prediction for a specific station"""
        try:
            predictions = self.predict_all_stations(model_type)
            if predictions is None:
                return None

            for pred in predictions:
                if pred["station_id"] == station_id:
                    return pred

            logger.warning(f" Station {station_id} not found in predictions")
            return None

        except Exception as e:
            logger.error(f" Error predicting for station {station_id}: {str(e)}")
            return None

    def _get_risk_level(self, probability: float) -> str:
        """
        Classify probability into risk level

        Returns:
            'GREEN', 'YELLOW', or 'RED'
        """
        if probability < self.risk_levels["GREEN"][1]:
            return "GREEN"
        elif probability < self.risk_levels["YELLOW"][1]:
            return "YELLOW"
        else:
            return "RED"

    def predict_both_types(self) -> Optional[Dict]:
        """
        Generate both flood and drought predictions

        Returns:
            {
                'flood': [...],
                'drought': [...],
                'timestamp': '...'
            }
        """
        try:
            logger.info(" Generating all predictions...")

            flood_preds = self.predict_all_stations("flood")
            drought_preds = self.predict_all_stations("drought")

            if flood_preds is None or drought_preds is None:
                logger.error(" Failed to generate predictions")
                return None

            # Combinar predicciones
            merged = {}
            for flood_pred in flood_preds:
                station_id = flood_pred["station_id"]
                merged[station_id] = {"flood": flood_pred}

            for drought_pred in drought_preds:
                station_id = drought_pred["station_id"]
                if station_id in merged:
                    merged[station_id]["drought"] = drought_pred
                else:
                    merged[station_id] = {"drought": drought_pred}

            result = {
                "flood": flood_preds,
                "drought": drought_preds,
                "merged": merged,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f" Error in predict_both_types: {str(e)}")
            return None

    def cache_predictions(self, predictions: Dict) -> bool:
        """Save predictions to cache"""
        try:
            cache_file = self.cache_path / PREDICTIONS_CACHE
            with open(cache_file, "w") as f:
                json.dump(predictions, f, indent=2)
            logger.info(f" Predictions cached")
            return True
        except Exception as e:
            logger.error(f" Error caching predictions: {str(e)}")
            return False

    def get_cached_predictions(self) -> Optional[Dict]:
        """Load predictions from cache"""
        try:
            cache_file = self.cache_path / PREDICTIONS_CACHE
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f" Error loading cached predictions: {str(e)}")
            return None

    def prediction_pipeline(self) -> Optional[Dict]:
        """Complete prediction pipeline: load models -> get data -> predict -> cache"""
        # Cargar modelos
        if not self.load_models():
            return None

        # Generar predicciones
        predictions = self.predict_both_types()
        if predictions is None:
            return None

        # Cachear predicciones
        self.cache_predictions(predictions)

        return predictions
