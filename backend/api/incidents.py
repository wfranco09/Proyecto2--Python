"""
API router para reportes de incidencias y anomalías
"""

from datetime import datetime
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.database.raindrop_db import (
    insert_incident_report,
    get_active_incident_reports,
    get_all_incident_reports,
    update_incident_status
)

router = APIRouter()
logger = logging.getLogger(__name__)


class IncidentReportCreate(BaseModel):
    """Modelo para crear un reporte de incidencia"""
    incident_type: str = Field(..., description="Tipo: 'flood' o 'drought'")
    description: Optional[str] = Field("", max_length=500, description="Descripción opcional")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: Optional[str] = Field("medium", description="Severidad: 'low', 'medium', 'high'")
    reported_by: Optional[str] = Field("anonymous", description="Usuario que reporta")


class IncidentReportUpdate(BaseModel):
    """Modelo para actualizar un reporte"""
    status: str = Field(..., description="Estado: 'active', 'resolved', 'dismissed'")
    notes: Optional[str] = Field(None, max_length=500)


@router.post("")
async def create_incident_report(report: IncidentReportCreate):
    """Crea un nuevo reporte de incidencia/anomalía."""
    try:
        # Validar tipo de incidente
        if report.incident_type not in ['flood', 'drought']:
            raise HTTPException(
                status_code=400, 
                detail="incident_type debe ser 'flood' o 'drought'"
            )
        
        # Validar severidad
        if report.severity not in ['low', 'medium', 'high']:
            raise HTTPException(
                status_code=400,
                detail="severity debe ser 'low', 'medium' o 'high'"
            )
        
        # Insertar en base de datos
        report_data = {
            'incident_type': report.incident_type,
            'description': report.description,
            'latitude': report.latitude,
            'longitude': report.longitude,
            'severity': report.severity,
            'reported_by': report.reported_by
        }
        
        report_id = insert_incident_report(report_data)
        
        logger.info(f"Reporte creado: ID={report_id}, Tipo={report.incident_type}, Severidad={report.severity}")
        
        # Trigger automático de re-entrenamiento en background
        try:
            from core.ml.incident_correlation import get_incident_training_data
            import threading
            
            def retrain_model():
                """Re-entrena el modelo con el nuevo incidente."""
                try:
                    # Verificar que hay suficientes incidentes (mínimo 10)
                    X, y_flood, y_drought = get_incident_training_data()
                    if len(X) >= 10:
                        logger.info(f"🔄 Re-entrenando modelo con {len(X)} incidentes...")
                        from core.ml import train_model_from_history
                        train_model_from_history(days_back=7)
                        logger.info("✅ Modelo re-entrenado exitosamente")
                    else:
                        logger.info(f"⏳ Esperando más incidentes para re-entrenamiento ({len(X)}/10)")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo re-entrenar modelo: {e}")
            
            # Ejecutar en thread separado para no bloquear la respuesta
            thread = threading.Thread(target=retrain_model, daemon=True, name="ModelRetraining")
            thread.start()
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo iniciar re-entrenamiento automático: {e}")
        
        return {
            "id": report_id,
            "message": "Reporte de incidencia creado exitosamente",
            "incident_type": report.incident_type,
            "severity": report.severity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "auto_retrain": "Model retraining triggered in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando reporte: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al crear reporte de incidencia")


@router.get("")
async def list_incident_reports(
    status: Optional[str] = None,
    limit: int = 100
):
    """
    Lista todos los reportes de incidencias.
    
    Query params:
    - status: Filtrar por estado ('active', 'resolved', 'dismissed')
    - limit: Número máximo de resultados (default: 100)
    """
    try:
        if status and status not in ['active', 'resolved', 'dismissed']:
            raise HTTPException(
                status_code=400,
                detail="status debe ser 'active', 'resolved' o 'dismissed'"
            )
        
        reports = get_all_incident_reports(status=status, limit=limit)
        
        return {
            "total": len(reports),
            "status_filter": status,
            "reports": reports,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo reportes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener reportes")


@router.get("/active")
async def list_active_incidents(limit: int = 50):
    """Obtiene solo los reportes activos (para mostrar en el mapa)."""
    try:
        reports = get_active_incident_reports(limit=limit)
        
        return {
            "total": len(reports),
            "reports": reports,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo reportes activos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener reportes activos")


@router.patch("/{incident_id}")
async def update_incident_report(
    incident_id: int,
    update: IncidentReportUpdate
):
    """Actualiza el estado de un reporte de incidencia."""
    try:
        # Validar estado
        if update.status not in ['active', 'resolved', 'dismissed']:
            raise HTTPException(
                status_code=400,
                detail="status debe ser 'active', 'resolved' o 'dismissed'"
            )
        
        # Actualizar en base de datos
        success = update_incident_status(
            incident_id=incident_id,
            status=update.status,
            notes=update.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {incident_id} no encontrado"
            )
        
        logger.info(f"Reporte {incident_id} actualizado a estado: {update.status}")
        
        return {
            "id": incident_id,
            "status": update.status,
            "message": "Reporte actualizado exitosamente",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando reporte {incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al actualizar reporte")


@router.delete("/{incident_id}")
async def delete_incident_report(incident_id: int):
    """Elimina un reporte de incidencia."""
    try:
        from core.database.raindrop_db import DATABASE_PATH
        import sqlite3
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM incident_reports WHERE id = ?", (incident_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {incident_id} no encontrado"
            )
        
        logger.info(f"Reporte {incident_id} eliminado")
        
        return {
            "id": incident_id,
            "message": "Reporte eliminado exitosamente",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando reporte {incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al eliminar reporte")


@router.get("/{incident_id}")
async def get_incident_report(incident_id: int):
    """Obtiene un reporte específico por ID."""
    try:
        # Obtener todos y filtrar por ID (simple para este caso)
        all_reports = get_all_incident_reports(limit=1000)
        report = next((r for r in all_reports if r['id'] == incident_id), None)
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte con ID {incident_id} no encontrado"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo reporte {incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener reporte")
