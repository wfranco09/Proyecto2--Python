"""
Script para limpiar todos los datos de la tabla weather_hourly SIN confirmación.
Útil para scripts automatizados o CI/CD.

⚠️ CUIDADO: Este script elimina datos sin pedir confirmación
"""

import sqlite3
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def clear_weather_data_force():
    """Elimina todos los registros de la tabla weather_hourly sin confirmación"""
    
    # Ruta a la base de datos
    db_path = Path(__file__).parent.parent / "core" / "database" / "raindrop.db"
    
    if not db_path.exists():
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        # Conectar a la base de datos
        logger.info(f"📂 Conectando a: {db_path}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Contar registros antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM weather_hourly")
        count_before = cursor.fetchone()[0]
        logger.info(f"📊 Registros a eliminar: {count_before:,}")
        
        if count_before == 0:
            logger.info("✓ La tabla ya está vacía")
            conn.close()
            return True
        
        # Eliminar todos los registros (sin confirmación)
        logger.info("🗑️  Eliminando registros...")
        cursor.execute("DELETE FROM weather_hourly")
        conn.commit()
        
        # Verificar que se eliminaron
        cursor.execute("SELECT COUNT(*) FROM weather_hourly")
        count_after = cursor.fetchone()[0]
        
        # Optimizar la base de datos (recuperar espacio)
        logger.info("🔧 Optimizando base de datos (VACUUM)...")
        cursor.execute("VACUUM")
        
        conn.close()
        
        logger.info(f"✅ ¡Completado! Registros eliminados: {count_before:,}")
        logger.info(f"📊 Registros restantes: {count_after}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧹 LIMPIAR DATOS CLIMÁTICOS (MODO FORZADO)")
    logger.info("=" * 60)
    logger.warning("⚠️  Este script elimina datos SIN confirmación")
    
    success = clear_weather_data_force()
    
    if success:
        logger.info("\n✅ Proceso completado exitosamente")
    else:
        logger.info("\n❌ Proceso finalizado con errores")
