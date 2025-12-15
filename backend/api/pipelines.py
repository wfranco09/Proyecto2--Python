"""
API Router para ejecutar pipelines de ETL
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, List
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

# Logger
logger = logging.getLogger(__name__)

# Almacenar conexiones WebSocket activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando mensaje: {e}")
                disconnected.append(connection)
        
        # Eliminarr conexiones desconectadas
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Mapeo de pipelines disponibles
AVAILABLE_PIPELINES = {
    "meteosource": {
        "name": "Meteosource Real-Time",
        "description": "Obtiene datos climáticos en tiempo real de las +250 estaciones usando Meteosource API",
        "command": ["python", "-m", "core.pipelines.etl.meteosource.meteosource_pipeline"],
    },
    "generate_dummy": {
        "name": "Generar Datos Dummy",
        "description": "Genera datos climáticos sintéticos para entrenamiento del modelo ML (5000+ registros)",
        "command": ["python", "-m", "core.pipelines.etl.generate_dummy_data"],
    },
}


@router.get("/available")
async def get_available_pipelines():
    """Obtener lista de pipelines disponibles"""
    return {
        "pipelines": [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
            }
            for key, value in AVAILABLE_PIPELINES.items()
        ]
    }


@router.post("/run/{pipeline_name}")
async def run_pipeline(pipeline_name: str, use_random: bool = True):
    """
    Ejecutar un pipeline específico.
    El progreso se envía por WebSocket.
    
    Args:
        pipeline_name: Nombre del pipeline a ejecutar
        use_random: Para generate_dummy - genera datos aleatorios (True) o basados en conocimiento (False)
    """
    if pipeline_name not in AVAILABLE_PIPELINES:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_name}' no encontrado"
        )
    
    pipeline_config = AVAILABLE_PIPELINES[pipeline_name].copy()
    
    # Si es generate_dummy, agregar parámetro use_random al comando
    if pipeline_name == "generate_dummy":
        pipeline_config["use_random"] = use_random
    
    # Enviar notificación de inicio
    await manager.broadcast({
        "type": "pipeline_started",
        "pipeline": pipeline_name,
        "timestamp": datetime.now().isoformat(),
    })
    
    try:
        # Verificar si es una secuencia de pipelines
        if pipeline_name == "all" and "sequence" in pipeline_config:
            # Ejecutar secuencia en background
            asyncio.create_task(
                execute_pipeline_sequence(pipeline_name, pipeline_config["sequence"])
            )
        else:
            # Ejecutar pipeline individual en background
            asyncio.create_task(
                execute_pipeline_background(pipeline_name, pipeline_config)
            )
        
        return {
            "status": "started",
            "pipeline": pipeline_name,
            "message": f"Pipeline '{pipeline_config['name']}' iniciado",
        }
    except Exception as e:
        logger.error(f"Error ejecutando pipeline: {e}")
        await manager.broadcast({
            "type": "pipeline_error",
            "pipeline": pipeline_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        raise HTTPException(status_code=500, detail=str(e))


async def execute_pipeline_sequence(sequence_name: str, pipeline_ids: List[str]):
    """
    Ejecutar múltiples pipelines en secuencia
    """
    total = len(pipeline_ids)
    
    try:
        for idx, pipeline_id in enumerate(pipeline_ids, 1):
            if pipeline_id not in AVAILABLE_PIPELINES:
                logger.error(f"Pipeline {pipeline_id} no encontrado en secuencia")
                continue
            
            pipeline_config = AVAILABLE_PIPELINES[pipeline_id]
            
            # Notificar inicio del pipeline individual
            await manager.broadcast({
                "type": "pipeline_log",
                "pipeline": sequence_name,
                "message": f"[{idx}/{total}] Iniciando {pipeline_config['name']}...",
                "level": "info",
                "timestamp": datetime.now().isoformat(),
            })
            
            # Ejecutar pipeline y esperar a que termine
            success = await execute_single_pipeline(pipeline_id, pipeline_config, sequence_name)
            
            if not success:
                # Si falla, detener la secuencia
                await manager.broadcast({
                    "type": "pipeline_completed",
                    "pipeline": sequence_name,
                    "status": "error",
                    "error": f"La secuencia falló en: {pipeline_config['name']}",
                    "timestamp": datetime.now().isoformat(),
                })
                return
            
            # Notificar completado del pipeline individual
            await manager.broadcast({
                "type": "pipeline_log",
                "pipeline": sequence_name,
                "message": f"[{idx}/{total}]  {pipeline_config['name']} completado",
                "level": "info",
                "timestamp": datetime.now().isoformat(),
            })
        
        # Todos completados exitosamente
        await manager.broadcast({
            "type": "pipeline_completed",
            "pipeline": sequence_name,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Error en secuencia {sequence_name}: {e}", exc_info=True)
        await manager.broadcast({
            "type": "pipeline_completed",
            "pipeline": sequence_name,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })


async def execute_single_pipeline(pipeline_id: str, pipeline_config: Dict, parent_name: str = None) -> bool:
    """
    Ejecutar un pipeline individual y retornar si fue exitoso
    """
    try:
        # Para generate_dummy, ejecutar directamente como función para compartir estado
        if pipeline_id == "generate_dummy":
            from core.pipelines.etl.generate_dummy_data import generate_dummy_weather_data
            
            use_random = pipeline_config.get("use_random", True)
            logger.info(f"Ejecutando generate_dummy directamente (use_random={use_random})")
            
            # Ejecutar en thread pool para no bloquear el loop asyncio
            loop = asyncio.get_event_loop()
            try:
                await loop.run_in_executor(
                    None,
                    generate_dummy_weather_data,
                    365,  # days_back
                    None,  # stations_to_use (None = todas)
                    use_random,
                    24  # records_per_day
                )
                return True
            except Exception as e:
                logger.error(f"Error en generate_dummy: {e}", exc_info=True)
                return False
        
        # Para otros pipelines, continuar con subprocess
        backend_path = Path(__file__).parent.parent
        
        logger.info(f"Ejecutando pipeline: {pipeline_id}")
        
        # Construir comando base
        cmd = pipeline_config["command"].copy()
        
        # Crear proceso
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(backend_path),
        )
        
        # Leer stdout y stderr en paralelo
        async def read_stream(stream, is_error=False):
            while True:
                line = await stream.readline()
                if not line:
                    break
                
                log_line = line.decode().strip()
                if log_line:
                    logger.info(f"[{pipeline_id}] {log_line}")
                    
                    # Detectar nivel real del log (INFO, ERROR, WARNING)
                    # Los logs de Python pueden venir por stderr incluso si son INFO
                    detected_level = "info"
                    if "ERROR" in log_line.upper() or "EXCEPTION" in log_line.upper():
                        detected_level = "error"
                    elif "WARNING" in log_line.upper():
                        detected_level = "warning"
                    
                    await manager.broadcast({
                        "type": "pipeline_log",
                        "pipeline": parent_name or pipeline_id,
                        "message": log_line,  # Sin espacios adicionales
                        "level": detected_level,
                        "timestamp": datetime.now().isoformat(),
                    })
        
        # Leer ambos streams en paralelo
        await asyncio.gather(
            read_stream(process.stdout, False),
            read_stream(process.stderr, True)
        )
        
        # Esperar a que termine el proceso
        await process.wait()
        
        return process.returncode == 0
    
    except Exception as e:
        logger.error(f"Error en pipeline {pipeline_id}: {e}", exc_info=True)
        return False


async def execute_pipeline_background(pipeline_name: str, pipeline_config: Dict):
    """
    Ejecutar pipeline en background y enviar logs por WebSocket
    """
    success = await execute_single_pipeline(pipeline_name, pipeline_config)
    
    if success:
        logger.info(f"Pipeline {pipeline_name} completado exitosamente")
        await manager.broadcast({
            "type": "pipeline_completed",
            "pipeline": pipeline_name,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        })
    else:
        logger.error(f"Pipeline {pipeline_name} falló")
        await manager.broadcast({
            "type": "pipeline_completed",
            "pipeline": pipeline_name,
            "status": "error",
            "error": "El pipeline finalizó con errores",
            "timestamp": datetime.now().isoformat(),
        })


@router.get("/progress/generate_dummy")
async def stream_generation_progress():
    """
    Stream del progreso de generación de datos dummy usando Server-Sent Events (SSE).
    
    Envía actualizaciones en tiempo real del progreso:
    - is_running: bool - Si el proceso está en ejecución
    - current_station: int - Estación actual procesándose
    - total_stations: int - Total de estaciones
    - station_name: str - Nombre de la estación actual
    - records_generated: int - Total de registros generados
    - percentage: float - Porcentaje de completado (0-100)
    - start_time: str - Timestamp de inicio
    - error: str|None - Mensaje de error si ocurrió alguno
    """
    from core.pipelines.etl.generate_dummy_data import generation_progress
    
    logger.info("Cliente SSE conectado para progreso de generate_dummy")
    
    async def event_generator():
        """Genera eventos SSE con el progreso"""
        last_state = None
        max_iterations = 600  # Máximo 3 minutos (600 * 300ms)
        iteration = 0
        
        while iteration < max_iterations:
            try:
                # Copiar el estado actual
                progress = generation_progress.copy()
                
                # Calcular porcentaje
                if progress["total_stations"] > 0:
                    progress["percentage"] = round(
                        (progress["current_station"] / progress["total_stations"]) * 100, 2
                    )
                else:
                    progress["percentage"] = 0.0
                
                # Enviar solo si hay cambios o es la primera iteración
                current_state = json.dumps(progress, sort_keys=True)
                if current_state != last_state or iteration == 0:
                    last_state = current_state
                    yield f"data: {json.dumps(progress)}\n\n"
                    
                    # Si no está corriendo desde el inicio, enviar y terminar
                    if not progress["is_running"] and iteration == 0:
                        logger.info("Pipeline no está corriendo, enviando estado inicial y cerrando stream SSE")
                        await asyncio.sleep(0.5)  # Pausa para asegurar que el evento se envíe
                        break
                
                # Si ya no está corriendo (terminó durante ejecución), enviar mensaje final y terminar
                if not progress["is_running"] and iteration > 0:
                    logger.info("Pipeline terminado, cerrando stream SSE")
                    await asyncio.sleep(0.5)  # Pausa para asegurar entrega
                    break
                
                # Esperar antes de la siguiente actualización
                await asyncio.sleep(0.3)  # Actualizar cada 300ms
                iteration += 1
                
            except Exception as e:
                logger.error(f"Error en stream de progreso: {e}")
                error_data = {"error": str(e), "is_running": False}
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket para recibir logs de pipelines en tiempo real
    """
    await manager.connect(websocket)
    logger.info("Cliente WebSocket conectado")
    
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            logger.debug(f"Mensaje recibido: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"Error WebSocket: {e}")
        manager.disconnect(websocket)


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Obtiene el estado del scheduler y próximas ejecuciones
    """
    try:
        from core.scheduler import get_scheduler_status
        status = get_scheduler_status()
        return status
    except Exception as e:
        logger.error(f"Error obteniendo estado del scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))
