"""
API Router para Machine Learning
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
import logging
from pathlib import Path

from core.ml import RiskPredictor, train_model_from_history

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "ml_models"


@router.post("/train")
async def train_model(
    days_back: int = Query(
        7,
        description="Días de datos históricos para entrenamiento",
        ge=3,
        le=30
    )
):
    """
    Entrena el modelo de predicción de riesgo con datos históricos.
    
    **Nota:** El modelo se entrena automáticamente cada día a las 2:00 AM.
    Este endpoint permite entrenamiento manual bajo demanda.
    
    - **days_back**: Días de histórico para usar (default: 7)
    
    Returns:
        Métricas de entrenamiento y accuracy del modelo
    """
    try:
        logger.info(f"Iniciando entrenamiento con {days_back} días de datos...")
        
        metrics = train_model_from_history(days_back=days_back)
        
        # Extraer información relevante del reporte
        report = metrics['classification_report']
        
        return {
            "status": "success",
            "message": "Modelo entrenado exitosamente",
            "metrics": {
                "accuracy": round(metrics['accuracy'], 4),
                "training_time": round(metrics['training_time'], 2),
                "train_samples": metrics['train_samples'],
                "test_samples": metrics['test_samples'],
                "timestamp": metrics['timestamp']
            },
            "feature_importance": {
                k: round(v, 4) 
                for k, v in sorted(
                    metrics['feature_importance'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5
            },
            "class_performance": {
                "bajo": {
                    "precision": round(report['bajo']['precision'], 3),
                    "recall": round(report['bajo']['recall'], 3),
                    "f1-score": round(report['bajo']['f1-score'], 3)
                },
                "moderado": {
                    "precision": round(report['moderado']['precision'], 3),
                    "recall": round(report['moderado']['recall'], 3),
                    "f1-score": round(report['moderado']['f1-score'], 3)
                },
                "alto": {
                    "precision": round(report['alto']['precision'], 3),
                    "recall": round(report['alto']['recall'], 3),
                    "f1-score": round(report['alto']['f1-score'], 3)
                },
                "critico": {
                    "precision": round(report['critico']['precision'], 3),
                    "recall": round(report['critico']['recall'], 3),
                    "f1-score": round(report['critico']['f1-score'], 3)
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error entrenando modelo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict_risk(features: Dict):
    """
    Predice el nivel de riesgo usando el modelo entrenado.
    
    Body debe contener:
    ```json
    {
        "temperature": 28.5,
        "humidity": 85.0,
        "precipitation_total": 15.0,
        "wind_speed": 35.0,
        "pressure": 1010.0,
        "temp_change": 2.5,
        "humidity_change": 5.0,
        "precip_change": 10.0,
        "wind_change": 15.0,
        "pressure_change": -3.0
    }
    ```
    
    Returns:
        Predicción de nivel de riesgo con confianza
    """
    try:
        # Cargar modelo
        model_path = MODELS_DIR / "risk_model.joblib"
        
        if not model_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado. Entrena el modelo primero usando POST /api/ml/train"
            )
        
        predictor = RiskPredictor(model_path=model_path)
        
        # Predecir
        risk_level, confidence = predictor.predict(features)
        
        return {
            "risk_level": risk_level,
            "confidence": round(confidence, 4),
            "features_used": features
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prediciendo riesgo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info")
async def get_model_info():
    """
    Obtiene información sobre el modelo actual.
    
    Returns:
        Información del modelo guardado
    """
    try:
        model_path = MODELS_DIR / "risk_model.joblib"
        
        if not model_path.exists():
            return {
                "status": "not_trained",
                "message": "No hay modelo entrenado. Usa POST /api/ml/train para entrenar."
            }
        
        import joblib
        model_data = joblib.load(model_path)
        
        return {
            "status": "trained",
            "model_type": "RandomForestClassifier",
            "features": model_data['feature_names'],
            "classes": list(model_data['label_mapping'].keys()),
            "trained_at": model_data['timestamp'],
            "model_path": str(model_path)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo info del modelo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/model")
async def delete_model():
    """
    Elimina el modelo actual.
    
    Returns:
        Confirmación de eliminación
    """
    try:
        model_path = MODELS_DIR / "risk_model.joblib"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="No hay modelo para eliminar")
        
        model_path.unlink()
        
        return {
            "status": "success",
            "message": "Modelo eliminado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando modelo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
