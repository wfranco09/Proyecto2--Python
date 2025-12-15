"""
Script para limpiar todos los datos de la tabla weather_hourly.
Útil para hacer pruebas limpias o resetear la base de datos.
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


def clear_weather_data():
    """Elimina todos los registros de la tabla weather_hourly"""
    
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
        logger.info(f"📊 Registros actuales: {count_before:,}")
        
        if count_before == 0:
            logger.info("✓ La tabla ya está vacía")
            conn.close()
            return True
        
        # Confirmar con el usuario (comentar esta parte si quieres que sea automático)
        print(f"\n⚠️  ¿Estás seguro de que quieres eliminar {count_before:,} registros?")
        confirmation = input("Escribe 'SI' para confirmar: ")
        
        if confirmation.strip().upper() != 'SI':
            logger.info("❌ Operación cancelada por el usuario")
            conn.close()
            return False
        
        # Eliminar todos los registros
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
    logger.info("🧹 LIMPIAR DATOS CLIMÁTICOS")
    logger.info("=" * 60)
    
    success = clear_weather_data()
    
    if success:
        logger.info("\n✅ Proceso completado exitosamente")
    else:
        logger.info("\n❌ Proceso finalizado con errores")
