#!/usr/bin/env python3
"""
Migración de BD: Agregar columnas de riesgo pre-calculado a weather_forecast
"""
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "core" / "database" / "raindrop.db"

def migrate():
    """Agrega columnas de riesgo a la tabla weather_forecast."""
    print("=" * 60)
    print("MIGRACIÓN: Agregar columnas de riesgo")
    print("=" * 60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Verificar si las columnas ya existen
    cursor.execute("PRAGMA table_info(weather_forecast)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\nColumnas actuales: {len(columns)}")
    
    # Columnas a agregar
    new_columns = [
        ("flood_probability", "REAL DEFAULT 0.0"),
        ("flood_level", "TEXT DEFAULT 'GREEN'"),
        ("flood_alert", "INTEGER DEFAULT 0"),
        ("drought_probability", "REAL DEFAULT 0.0"),
        ("drought_level", "TEXT DEFAULT 'GREEN'"),
        ("drought_alert", "INTEGER DEFAULT 0"),
    ]
    
    added = 0
    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE weather_forecast ADD COLUMN {col_name} {col_type}")
                print(f"✓ Agregada columna: {col_name} {col_type}")
                added += 1
            except Exception as e:
                print(f"✗ Error agregando {col_name}: {e}")
        else:
            print(f"  Columna {col_name} ya existe")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Migración completada: {added} columnas agregadas")
    print("=" * 60)

if __name__ == "__main__":
    migrate()
