"""
MetricsCalculator Service
Calculates and retrieves model performance metrics
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from config import MODELS_PATH, MODEL_METADATA, FEATURE_IMPORTANCES

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Service for retrieving model metrics and performance
    """

    def __init__(self):
        self.models_path = MODELS_PATH

    def get_model_metrics(self, model_type: str = "flood") -> Optional[Dict]:
        """
        Get stored metrics for a trained model

        Args:
            model_type: 'flood' or 'drought'

        Returns:
            Dict with model metrics or None
        """
        try:
            logger.info(f" Loading metrics for {model_type} model...")

            metadata_file = self.models_path / MODEL_METADATA
            if not metadata_file.exists():
                logger.warning(f" Metadata file not found: {metadata_file}")
                return None

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            metrics = metadata.get("metrics", {}).get(model_type, {})

            logger.info(f" Retrieved metrics for {model_type}")
            return metrics

        except Exception as e:
            logger.error(f" Error getting metrics: {str(e)}")
            return None

    def get_feature_importances(self, model_type: str = "flood") -> Optional[Dict]:
        """
        Get feature importances for a model

        Returns:
            Dict mapping feature names to importance scores
        """
        try:
            logger.info(f" Loading feature importances for {model_type}...")

            importance_file = self.models_path / FEATURE_IMPORTANCES
            if not importance_file.exists():
                logger.warning(f" Feature importances file not found: {importance_file}")
                return None

            with open(importance_file, "r") as f:
                importances = json.load(f)

            model_importances = importances.get(model_type, {})

            logger.info(f" Retrieved {len(model_importances)} feature importances")
            return model_importances

        except Exception as e:
            logger.error(f" Error getting feature importances: {str(e)}")
            return None

    def get_all_metrics(self) -> Optional[Dict]:
        """
        Get metrics for all models

        Returns:
            {
                'flood': {...},
                'drought': {...},
                'timestamp': '...'
            }
        """
        try:
            logger.info(" Loading all metrics...")

            flood_metrics = self.get_model_metrics("flood")
            drought_metrics = self.get_model_metrics("drought")

            result = {
                "flood": flood_metrics,
                "drought": drought_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(" All metrics loaded")
            return result

        except Exception as e:
            logger.error(f" Error getting all metrics: {str(e)}")
            return None

    def get_model_summary(self, model_type: str = "flood") -> Optional[Dict]:
        """
        Get summary of model performance

        Returns:
            {
                'type': 'flood',
                'accuracy': 0.95,
                'precision': 0.92,
                'recall': 0.88,
                'f1': 0.90,
                'auc_roc': 0.97,
                'n_features': 5,
                'n_samples': 145,
                'feature_importances': {...}
            }
        """
        try:
            metrics = self.get_model_metrics(model_type)
            if metrics is None:
                return None

            importances = self.get_feature_importances(model_type)
            if importances is None:
                importances = {}

            summary = {
                "type": model_type,
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1": metrics.get("f1"),
                "auc_roc": metrics.get("auc_roc"),
                "n_features": metrics.get("n_features"),
                "n_samples": metrics.get("n_samples"),
                "feature_importances": importances,
            }

            return summary

        except Exception as e:
            logger.error(f" Error getting model summary: {str(e)}")
            return None

    def format_metrics_for_api(self, model_type: str = "flood") -> Optional[Dict]:
        """
        Format metrics for API response

        Returns:
            {
                'model_type': 'flood',
                'performance': {
                    'accuracy': '95.2%',
                    'precision': '92.1%',
                    'recall': '88.5%',
                    'f1': '90.2%',
                    'auc_roc': '97.1%'
                },
                'features': {
                    'LLUVIA': '87.3%',
                    'HUMEDAD': '6.2%',
                    ...
                },
                'training_info': {
                    'n_samples': 145,
                    'n_features': 5,
                    'n_trees': 200
                }
            }
        """
        try:
            summary = self.get_model_summary(model_type)
            if summary is None:
                return None

            return {
                "model_type": model_type,
                "performance": {
                    "accuracy": f"{summary.get('accuracy', 0) * 100:.1f}%",
                    "precision": f"{summary.get('precision', 0) * 100:.1f}%",
                    "recall": f"{summary.get('recall', 0) * 100:.1f}%",
                    "f1": f"{summary.get('f1', 0) * 100:.1f}%",
                    "auc_roc": f"{summary.get('auc_roc', 0) * 100:.1f}%",
                },
                "feature_importances": {
                    name: f"{importance * 100:.1f}%"
                    for name, importance in summary.get("feature_importances", {}).items()
                },
                "training_info": {
                    "n_samples": summary.get("n_samples"),
                    "n_features": summary.get("n_features"),
                    "n_trees": 200,  # N_ESTIMATORS desde configuración
                },
            }

        except Exception as e:
            logger.error(f" Error formatting metrics: {str(e)}")
            return None

    def get_confusion_matrix(self, model_type: str = "flood") -> Optional[list]:
        """Get confusion matrix for model"""
        try:
            metrics = self.get_model_metrics(model_type)
            if metrics is None:
                return None

            return metrics.get("confusion_matrix")

        except Exception as e:
            logger.error(f" Error getting confusion matrix: {str(e)}")
            return None

    def get_classification_report(self, model_type: str = "flood") -> Optional[Dict]:
        """Get detailed classification report"""
        try:
            metrics = self.get_model_metrics(model_type)
            if metrics is None:
                return None

            return metrics.get("classification_report")

        except Exception as e:
            logger.error(f" Error getting classification report: {str(e)}")
            return None
