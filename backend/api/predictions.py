"""
API router para métricas y predicciones de modelos
"""

from fastapi import APIRouter, HTTPException
import joblib
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

# Paths a los modelos
MODELS_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "ml", "models")


def load_model(model_type: str):
    """Carga el modelo especificado."""
    if model_type not in ["flood", "drought"]:
        raise HTTPException(status_code=400, detail="model_type debe ser 'flood' o 'drought'")
    
    model_path = os.path.join(MODELS_PATH, f"rf_{model_type}.joblib")
    
    if not os.path.exists(model_path):
        logger.error(f"Modelo no encontrado: {model_path}")
        raise HTTPException(status_code=404, detail=f"Modelo '{model_type}' no encontrado")
    
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        logger.error(f"Error al cargar modelo {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al cargar modelo")


@router.get("/{model_type}/metrics")
async def get_model_metrics(model_type: str):
    """
    Retorna métricas y características del modelo.
    
    - **model_type**: "flood" o "drought"
    """
    try:
        model = load_model(model_type)
        
        # Extraer feature importances si disponible
        feature_importances = {}
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            # Feature names por defecto si no están disponibles
            feature_names = getattr(model, 'feature_names_in_', None)
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(len(importances))]
            
            feature_importances = {
                str(name): float(imp) 
                for name, imp in zip(feature_names, importances)
            }
            # Ordenar por importancia descendente
            feature_importances = dict(sorted(
                feature_importances.items(),
                key=lambda x: x[1],
                reverse=True
            ))
        
        # Información general del modelo
        return {
            "model_type": model_type,
            "model_class": model.__class__.__name__,
            "feature_importances": feature_importances,
            "n_features": len(feature_importances) if feature_importances else "unknown",
            "status": "ready"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener métricas del modelo {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar modelo")


@router.get("/{model_type}/info")
async def get_model_info(model_type: str):
    """
    Retorna información detallada del modelo (parámetros, tipo).
    
    - **model_type**: "flood" o "drought"
    """
    try:
        model = load_model(model_type)
        
        # Información del modelo
        model_info = {
            "model_type": model_type,
            "algorithm": model.__class__.__name__,
            "parameters": model.get_params() if hasattr(model, 'get_params') else {},
        }
        
        # Información de entrenamiento si está disponible
        if hasattr(model, 'n_estimators'):
            model_info["n_estimators"] = int(model.n_estimators)
        
        if hasattr(model, 'max_depth'):
            model_info["max_depth"] = model.max_depth
        
        if hasattr(model, 'n_classes_'):
            model_info["n_classes"] = int(model.n_classes_)
        
        if hasattr(model, 'classes_'):
            model_info["classes"] = [int(c) for c in model.classes_]
        
        return model_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener info del modelo {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar modelo")


@router.get("/status/available")
async def list_available_models():
    """
    Retorna lista de modelos disponibles en el sistema.
    """
    available_models = []
    
    for model_type in ["flood", "drought"]:
        model_path = os.path.join(MODELS_PATH, f"rf_{model_type}.joblib")
        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                available_models.append({
                    "type": model_type,
                    "path": model_path,
                    "algorithm": model.__class__.__name__,
                    "available": True
                })
            except Exception as e:
                logger.warning(f"Modelo {model_type} presente pero no cargable: {str(e)}")
                available_models.append({
                    "type": model_type,
                    "available": False,
                    "error": str(e)
                })
        else:
            available_models.append({
                "type": model_type,
                "available": False,
                "error": "Archivo no encontrado"
            })
    
    return {
        "total_available": sum(1 for m in available_models if m.get('available')),
        "models": available_models
    }
