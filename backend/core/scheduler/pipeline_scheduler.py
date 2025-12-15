"""
Scheduler para ejecutar el pipeline de Meteosource automáticamente cada hora.

Utiliza APScheduler para programar la ejecución del pipeline y garantizar
que los datos se actualicen regularmente.
"""

import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Suprimir warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Scheduler global
scheduler = None


def run_meteosource_pipeline():
    """Ejecuta el pipeline de Meteosource."""
    try:
        logger.info("=" * 50)
        logger.info("Iniciando ejecución programada del pipeline")
        logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 50)
        
        # Importar y ejecutar el pipeline
        from core.pipelines.etl.meteosource.meteosource_pipeline import run
        
        success = run()
        
        if success:
            logger.info(" Pipeline ejecutado exitosamente")
        else:
            logger.error(" Pipeline falló")
            
        return success
        
    except Exception as e:
        logger.error(f"Error ejecutando pipeline programado: {e}", exc_info=True)
        return False


def run_forecast_pipeline():
    """Ejecuta el pipeline de pronósticos (forecast) en un thread separado para no bloquear el servidor."""
    import threading
    
    def _run_in_thread():
        try:
            logger.info("=" * 50)
            logger.info("Iniciando ejecución programada del pipeline de pronósticos")
            logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
            logger.info("=" * 50)
            
            # Importar y ejecutar el pipeline de forecast
            from core.pipelines.etl.meteosource.forecast_pipeline import run
            
            success = run()
            
            if success:
                logger.info(" Pipeline de pronósticos ejecutado exitosamente")
            else:
                logger.error(" Pipeline de pronósticos falló")
                
            return success
            
        except Exception as e:
            logger.error(f"Error ejecutando pipeline de pronósticos: {e}", exc_info=True)
            return False
    
    # Ejecutar en thread separado para no bloquear el servidor
    thread = threading.Thread(target=_run_in_thread, daemon=True, name="ForecastPipeline")
    thread.start()
    logger.info(" Pipeline de pronósticos iniciado en thread separado")
    return True


def run_model_training():
    """Ejecuta el entrenamiento del modelo ML."""
    try:
        logger.info("=" * 50)
        logger.info("Iniciando entrenamiento programado del modelo ML")
        logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 50)
        
        # Importar y ejecutar el entrenamiento
        from core.ml import train_model_from_history
        
        # Entrenar con 7 días de datos históricos
        metrics = train_model_from_history(days_back=7)
        
        if metrics:
            logger.info(" Modelo entrenado exitosamente")
            logger.info(f"   - Accuracy: {metrics.get('accuracy', 'N/A'):.4f}")
            logger.info(f"   - Muestras de entrenamiento: {metrics.get('train_samples', 0)}")
            logger.info(f"   - Tiempo de entrenamiento: {metrics.get('training_time', 0):.2f}s")
            return True
        else:
            logger.error(" Entrenamiento del modelo falló")
            return False
            
    except Exception as e:
        logger.error(f"Error ejecutando entrenamiento programado: {e}", exc_info=True)
        return False


def start_scheduler():
    """Inicia el scheduler para ejecutar el pipeline cada hora."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler ya está iniciado")
        return scheduler
    
    logger.info("Iniciando scheduler de pipelines")
    
    # Crear scheduler
    scheduler = BackgroundScheduler(timezone="America/Panama")
    
    # Programar ejecución cada hora en el minuto 0
    # Ejemplo: 00:00, 01:00, 02:00, etc.
    scheduler.add_job(
        run_meteosource_pipeline,
        trigger=CronTrigger(minute=0, hour='*'),  # Cada hora en el minuto 0
        id='meteosource_pipeline',
        name='Meteosource Pipeline - Hourly',
        replace_existing=True,
        max_instances=1  # Solo una instancia a la vez
    )
    
    # Programar pipeline de pronósticos cada 6 horas (0, 6, 12, 18)
    scheduler.add_job(
        run_forecast_pipeline,
        trigger=CronTrigger(minute=0, hour='0,6,12,18'),  # Cada 6 horas
        id='forecast_pipeline',
        name='Forecast Pipeline - Every 6 hours',
        replace_existing=True,
        max_instances=1  # Solo una instancia a la vez
    )
    
    # Programar entrenamiento del modelo cada 24 horas a las 2:00 AM
    scheduler.add_job(
        run_model_training,
        trigger=CronTrigger(hour=2, minute=0),  # Todos los días a las 2:00 AM
        id='model_training',
        name='Model Training - Daily',
        replace_existing=True,
        max_instances=1  # Solo una instancia a la vez
    )
    
    scheduler.start()
    
    logger.info(" Scheduler iniciado")
    logger.info("Jobs programados:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}")
        logger.info(f"    Próxima ejecución: {job.next_run_time}")
    
    return scheduler


def stop_scheduler():
    """Detiene el scheduler."""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler no está iniciado")
        return
    
    logger.info("Deteniendo scheduler...")
    scheduler.shutdown()
    scheduler = None
    logger.info(" Scheduler detenido")


def get_scheduler_status():
    """Obtiene el estado del scheduler."""
    if scheduler is None:
        return {
            "running": False,
            "num_jobs": 0,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": True,
        "num_jobs": len(jobs),
        "jobs": jobs
    }


def execute_pipeline_now():
    """Ejecuta el pipeline inmediatamente (útil para testing)."""
    logger.info("Ejecución manual del pipeline solicitada")
    return run_meteosource_pipeline()


def execute_training_now():
    """Ejecuta el entrenamiento del modelo inmediatamente (útil para testing)."""
    logger.info("Ejecución manual del entrenamiento solicitada")
    return run_model_training()


def execute_forecast_now():
    """Ejecuta el pipeline de pronósticos inmediatamente en un thread separado."""
    logger.info("Ejecución manual del pipeline de pronósticos solicitada")
    return run_forecast_pipeline()  # Ya ejecuta en thread separado


if __name__ == "__main__":
    # Para testing: iniciar scheduler y mantenerlo corriendo
    import time
    
    try:
        scheduler = start_scheduler()
        
        # Ejecutar inmediatamente para testing
        logger.info("\nEjecutando pipeline inmediatamente para testing...")
        execute_pipeline_now()
        
        logger.info("\nScheduler corriendo. Presiona Ctrl+C para detener.")
        logger.info("El modelo se entrenará automáticamente cada día a las 2:00 AM")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\nInterrupción detectada")
        stop_scheduler()
        logger.info("Scheduler detenido correctamente")
