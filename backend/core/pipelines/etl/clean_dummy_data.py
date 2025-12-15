"""
Utilidad para limpiar datos dummy de la base de datos.

Permite eliminar todos los datos generados sintéticamente,
manteniendo solo los datos reales de Meteosource.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_PATH = Path(__file__).parent.parent / "database" / "raindrop.db"


def clean_dummy_data(cutoff_date: str = None):
    """
    Elimina datos dummy de la base de datos.
    
    Args:
        cutoff_date: Fecha de corte en formato 'YYYY-MM-DD'. 
                    Elimina registros antes de esta fecha.
                    Si no se proporciona, elimina todo excepto últimos 30 días.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Contar registros antes de limpiar
        cursor.execute("SELECT COUNT(*) FROM weather_hourly")
        total_before = cursor.fetchone()[0]
        
        if cutoff_date:
            logger.info(f" Eliminando registros antes de {cutoff_date}...")
            cursor.execute(
                "DELETE FROM weather_hourly WHERE date < ?",
                (cutoff_date,)
            )
        else:
            logger.info(" Eliminando todos los registros...")
            cursor.execute("DELETE FROM weather_hourly")
        
        conn.commit()
        
        # Contar registros después de limpiar
        cursor.execute("SELECT COUNT(*) FROM weather_hourly")
        total_after = cursor.fetchone()[0]
        
        deleted = total_before - total_after
        logger.info(f" Eliminados: {deleted} registros")
        logger.info(f" Restantes: {total_after} registros")
        
        return deleted
        
    except Exception as e:
        logger.error(f" Error limpiando datos: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def vacuum_database():
    """Optimiza el tamaño de la base de datos."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        logger.info(" Optimizando base de datos...")
        conn.execute("VACUUM")
        logger.info(" Base de datos optimizada")
    except Exception as e:
        logger.error(f" Error optimizando: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print(" UTILIDAD DE LIMPIEZA DE DATOS DUMMY")
    print("=" * 60)
    print()
    print("Opciones:")
    print("  1. Eliminar TODOS los registros")
    print("  2. Eliminar registros antes de fecha específica")
    print("  3. Cancelar")
    print()
    
    choice = input("Seleccione opción (1-3): ").strip()
    
    if choice == "1":
        confirm = input(" ¿Está seguro? Esto eliminará TODOS los datos (s/n): ").strip().lower()
        if confirm == 's':
            deleted = clean_dummy_data()
            if deleted > 0:
                vacuum_database()
                print(f" ✓ {deleted} registros eliminados exitosamente")
        else:
            print(" Operación cancelada")
            
    elif choice == "2":
        date_str = input("Ingrese fecha de corte (YYYY-MM-DD): ").strip()
        try:
            # Validar formato de fecha
            datetime.strptime(date_str, '%Y-%m-%d')
            confirm = input(f" ¿Eliminar registros antes de {date_str}? (s/n): ").strip().lower()
            if confirm == 's':
                deleted = clean_dummy_data(cutoff_date=date_str)
                if deleted > 0:
                    vacuum_database()
                    print(f" ✓ {deleted} registros eliminados exitosamente")
            else:
                print(" Operación cancelada")
        except ValueError:
            print(" Error: Formato de fecha inválido")
            
    else:
        print(" Operación cancelada")
