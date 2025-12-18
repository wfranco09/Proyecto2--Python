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
        logger.info(f"🚀 Iniciando entrenamiento DUAL MODELS (flood + drought) con datos históricos completos...")
        
        metrics = train_model_from_history(days_back=days_back)
        
        # Extraer información de ambos modelos
        flood_model = metrics['flood_model']
        drought_model = metrics['drought_model']
        
        return {
            "status": "success",
            "message": "Modelos entrenados exitosamente (flood + drought)",
            "metrics": {
                "training_time": round(metrics['training_time'], 2),
                "train_samples": metrics['train_samples'],
                "test_samples": metrics['test_samples'],
                "timestamp": metrics['timestamp']
            },
            "flood_model": {
                "r2_score": round(flood_model['r2'], 4),
                "mae": round(flood_model['mae'], 4),
                "mse": round(flood_model['mse'], 4),
                "top_features": {
                    k: round(v, 4)
                    for k, v in sorted(
                        flood_model['feature_importance'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                }
            },
            "drought_model": {
                "r2_score": round(drought_model['r2'], 4),
                "mae": round(drought_model['mae'], 4),
                "mse": round(drought_model['mse'], 4),
                "top_features": {
                    k: round(v, 4)
                    for k, v in sorted(
                        drought_model['feature_importance'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
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
                detail="Modelos no encontrados. Entrena los modelos primero usando POST /api/ml/train"
            )
        
        predictor = RiskPredictor(model_path=model_path)
        
        # Predecir con ambos modelos
        predictions = predictor.predict(features)
        
        return {
            "flood_risk": round(predictions['flood_risk'], 4),
            "drought_risk": round(predictions['drought_risk'], 4),
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
            "model_type": "Dual RandomForestRegressor (flood + drought)",
            "features": model_data['feature_names'],
            "output_format": {
                "flood_risk": "float [0.0 - 1.0]",
                "drought_risk": "float [0.0 - 1.0]"
            },
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
