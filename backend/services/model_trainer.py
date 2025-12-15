"""
ModelTrainer Service
Converts notebook training logic into a reusable service
"""

import pandas as pd
import numpy as np
import logging
import joblib
import json
from pathlib import Path
from typing import Optional, Tuple, Dict
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report,
)

from config import (
    DATA_CLEAN_PATH,
    MODELS_PATH,
    FEATURE_COLUMNS,
    LABEL_COLUMNS,
    TRAIN_TEST_SPLIT,
    RANDOM_STATE,
    N_ESTIMATORS,
    MAX_DEPTH,
    MIN_SAMPLES_SPLIT,
    MASTER_DATASET,
    MODEL_FLOOD,
    MODEL_DROUGHT,
    MODEL_METADATA,
    FEATURE_IMPORTANCES,
)

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Service for training machine learning models
    Converted from notebooks/Train_and_Visualize.ipynb
    """

    def __init__(self):
        self.data_path = DATA_CLEAN_PATH
        self.models_path = MODELS_PATH
        self.feature_columns = FEATURE_COLUMNS
        self.models = {}
        self.metadata = {}

    def load_training_data(self) -> Optional[pd.DataFrame]:
        """Load clean dataset for training"""
        try:
            data_file = self.data_path / MASTER_DATASET
            if not data_file.exists():
                logger.error(f" Training data not found: {data_file}")
                return None

            df = pd.read_csv(data_file)
            logger.info(f" Training data loaded: {len(df)} rows, {len(df.columns)} columns")
            return df

        except Exception as e:
            logger.error(f" Error loading training data: {str(e)}")
            return None

    def prepare_data(self, df: pd.DataFrame) -> Optional[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        Prepare data for training
        - Convert to numeric
        - Create labels
        - Handle missing values
        - Select features

        Returns:
            Tuple[X, y_flood, y_drought] or None
        """
        try:
            logger.info(" Preparing training data...")

            df = df.copy()

            # Convertir a numérico
            for col in self.feature_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Manejar valores faltantes (por mediana de estación, luego global)
            if "station_id" in df.columns:
                for col in self.feature_columns:
                    if col in df.columns:
                        df[col] = df.groupby("station_id")[col].transform(
                            lambda x: x.fillna(x.median())
                        )

            for col in self.feature_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(df[col].median())

            # Crear etiquetas si no existen
            if "flood_label" not in df.columns:
                # Inundación: LLUVIA > 30mm
                df["flood_label"] = (df["LLUVIA"] > 30).astype(int)

            if "drought_label" not in df.columns:
                # Sequía: LLUVIA < 5mm
                df["drought_label"] = (df["LLUVIA"] < 5).astype(int)

            # Seleccionar características (asegurar que existan)
            available_features = [col for col in self.feature_columns if col in df.columns]
            X = df[available_features].dropna()

            y_flood = df.loc[X.index, "flood_label"]
            y_drought = df.loc[X.index, "drought_label"]

            logger.info(
                f" Data prepared: {len(X)} samples, {len(available_features)} features"
            )
            logger.info(f"   Flood positive: {y_flood.sum()}, Drought positive: {y_drought.sum()}")

            return X, y_flood, y_drought

        except Exception as e:
            logger.error(f" Error preparing data: {str(e)}")
            return None

    def train_and_evaluate(
        self, X: pd.DataFrame, y: pd.Series, model_type: str
    ) -> Optional[Tuple[RandomForestClassifier, Dict]]:
        """
        Train Random Forest model and evaluate

        Args:
            X: Features
            y: Labels
            model_type: 'flood' or 'drought'

        Returns:
            Tuple[trained_model, metrics] or None
        """
        try:
            logger.info(f" Training {model_type} model...")

            # Manejar conjuntos de datos pequeños
            n_test = max(1, int(len(X) * TRAIN_TEST_SPLIT))
            if len(X) < 10:
                logger.warning(f" Very small dataset: {len(X)} samples")
                n_test = 1

            # Dividir datos
            stratify = y if len(np.unique(y)) > 1 else None

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=n_test,
                random_state=RANDOM_STATE,
                stratify=stratify,
            )

            logger.info(f"   Train: {len(X_train)}, Test: {len(X_test)}")

            # Entrenar modelo
            model = RandomForestClassifier(
                n_estimators=N_ESTIMATORS,
                max_depth=MAX_DEPTH,
                min_samples_split=MIN_SAMPLES_SPLIT,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )

            model.fit(X_train, y_train)
            logger.info(f"    Model trained")

            # Evaluar
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1] if len(np.unique(y_test)) > 1 else np.zeros(len(y_test))

            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred, zero_division=0)),
                "recall": float(recall_score(y_test, y_pred, zero_division=0)),
                "f1": float(f1_score(y_test, y_pred, zero_division=0)),
                "auc_roc": float(
                    roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0
                ),
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
                "classification_report": classification_report(y_test, y_pred, output_dict=True),
                "n_features": X.shape[1],
                "n_samples": len(X),
                "model_type": model_type,
            }

            logger.info(
                f" {model_type} model trained - Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc_roc']:.3f}"
            )

            return model, metrics

        except Exception as e:
            logger.error(f" Error training {model_type} model: {str(e)}")
            return None

    def train_all_models(self, df: pd.DataFrame) -> Optional[Dict]:
        """Train both flood and drought models"""
        try:
            logger.info(" Starting complete model training...")

            # Preparar datos
            result = self.prepare_data(df)
            if result is None:
                return None

            X, y_flood, y_drought = result

            # Entrenar modelo de inundación
            flood_result = self.train_and_evaluate(X, y_flood, "flood")
            if flood_result is None:
                return None

            model_flood, metrics_flood = flood_result
            self.models["flood"] = model_flood
            self.metadata["flood"] = metrics_flood

            # Entrenar modelo de sequía
            drought_result = self.train_and_evaluate(X, y_drought, "drought")
            if drought_result is None:
                return None

            model_drought, metrics_drought = drought_result
            self.models["drought"] = model_drought
            self.metadata["drought"] = metrics_drought

            # Guardar modelos
            self.save_models()

            logger.info(" All models trained and saved")
            return self.metadata

        except Exception as e:
            logger.error(f" Error in train_all_models: {str(e)}")
            return None

    def save_models(self) -> bool:
        """Save trained models and metadata"""
        try:
            logger.info(" Saving models...")

            for model_type, model in self.models.items():
                model_file = self.models_path / (
                    MODEL_FLOOD if model_type == "flood" else MODEL_DROUGHT
                )
                joblib.dump(model, model_file)
                logger.info(f"    Saved {model_file}")

            # Guardar metadatos
            metadata_file = self.models_path / MODEL_METADATA
            with open(metadata_file, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "metrics": {k: v for k, v in self.metadata.items()},
                    },
                    f,
                    indent=2,
                )
            logger.info(f"    Saved {metadata_file}")

            # Guardar importancia de características
            importances = {}
            for model_type, model in self.models.items():
                if hasattr(model, "feature_importances_"):
                    importances[model_type] = {
                        feature: float(importance)
                        for feature, importance in zip(
                            self.feature_columns, model.feature_importances_
                        )
                    }

            importance_file = self.models_path / FEATURE_IMPORTANCES
            with open(importance_file, "w") as f:
                json.dump(importances, f, indent=2)
            logger.info(f"    Saved {importance_file}")

            return True

        except Exception as e:
            logger.error(f" Error saving models: {str(e)}")
            return False

    def train_pipeline(self) -> Optional[Dict]:
        """
        Complete training pipeline: load -> prepare -> train -> save
        """
        # Cargar datos
        df = self.load_training_data()
        if df is None:
            return None

        # Entrenar todos los modelos
        return self.train_all_models(df)

    def get_feature_importances(self) -> Optional[Dict]:
        """Get feature importances from trained models"""
        try:
            importance_file = self.models_path / FEATURE_IMPORTANCES
            if importance_file.exists():
                with open(importance_file, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f" Error reading feature importances: {str(e)}")
            return None
