#!/usr/bin/env python3
"""
Calcula y actualiza los riesgos para los forecasts existentes en la BD.
"""
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import sqlite3
from core.database.raindrop_db import DATABASE_PATH
from core.ml.risk_predictor import RiskPredictor

def populate_risks():
    """Calcula riesgos para todos los forecasts existentes."""
    print("=" * 60)
    print("CALCULANDO RIESGOS PARA FORECASTS EXISTENTES")
    print("=" * 60)
    
    # Conectar a BD
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener todos los forecasts
    cursor.execute("SELECT * FROM weather_forecast")
    forecasts = cursor.fetchall()
    
    if not forecasts:
        print("\n⚠️  No hay forecasts en la base de datos")
        conn.close()
        return
    
    print(f"\n📊 Encontrados {len(forecasts)} forecasts")
    
    # Cargar modelo ML
    model_path = backend_dir / "ml_models" / "risk_model.joblib"
    
    if not model_path.exists():
        print(f"\n⚠️  Modelo no encontrado en {model_path}")
        print("Usando valores por defecto...")
        use_model = False
    else:
        try:
            predictor = RiskPredictor(model_path=model_path)
            print(f"✓ Modelo ML cargado desde {model_path}")
            use_model = True
        except Exception as e:
            print(f"⚠️  Error cargando modelo: {e}")
            print("Usando valores por defecto...")
            use_model = False
    
    # Calcular riesgos
    updated = 0
    for forecast in forecasts:
        try:
            if use_model:
                # Preparar features (usar dict() para convertir Row a diccionario)
                f_dict = dict(forecast)
                features = {
                    'temperature': f_dict.get('temperature') or 0,
                    'humidity': f_dict.get('humidity') or 0,
                    'precipitation': f_dict.get('precipitation_total') or 0,
                    'wind_speed': f_dict.get('wind_speed_max') or 0,
                    'pressure': f_dict.get('pressure') or 1013.25,
                    'cloud_cover': f_dict.get('cloud_cover') or 0,
                    'uv_index': f_dict.get('uv_index') or 0,
                }
                
                # Predecir riesgo
                flood_risk = predictor.predict(features)
                flood_prob = flood_risk[1]
                flood_level = flood_risk[0]
                flood_alert = 1 if flood_level in ["YELLOW", "RED"] else 0
                
                # Por ahora usar mismos valores para sequía
                drought_prob = flood_prob * 0.3  # Sequía menos probable en zona tropical
                drought_level = "GREEN" if drought_prob < 0.3 else ("YELLOW" if drought_prob < 0.7 else "RED")
                drought_alert = 1 if drought_level in ["YELLOW", "RED"] else 0
            else:
                # Valores por defecto basados en precipitación
                f_dict = dict(forecast)
                rainfall = float(f_dict.get('precipitation_total') or 0.0)
                humidity = float(f_dict.get('humidity') or 0.0)
                
                flood_prob = min(0.95, (rainfall / 50.0) * 0.6 + (humidity / 100.0) * 0.4)
                flood_level = "GREEN" if flood_prob < 0.3 else ("YELLOW" if flood_prob < 0.7 else "RED")
                flood_alert = 1 if flood_level in ["YELLOW", "RED"] else 0
                
                drought_prob = min(0.95, (1 - rainfall / 50.0) * 0.4 + (1 - humidity / 100.0) * 0.3)
                drought_level = "GREEN" if drought_prob < 0.3 else ("YELLOW" if drought_prob < 0.7 else "RED")
                drought_alert = 1 if drought_level in ["YELLOW", "RED"] else 0
            
            # Actualizar en BD
            cursor.execute("""
                UPDATE weather_forecast
                SET flood_probability = ?,
                    flood_level = ?,
                    flood_alert = ?,
                    drought_probability = ?,
                    drought_level = ?,
                    drought_alert = ?
                WHERE station_id = ? AND forecast_date = ?
            """, (
                flood_prob, flood_level, flood_alert,
                drought_prob, drought_level, drought_alert,
                f_dict.get('station_id'), f_dict.get('forecast_date')
            ))
            
            updated += 1
            
            if updated % 50 == 0:
                print(f"  Procesados {updated}/{len(forecasts)}...")
        
        except Exception as e:
            f_dict = dict(forecast)
            print(f"⚠️  Error procesando forecast {f_dict.get('station_id')}/{f_dict.get('forecast_date')}: {e}")
            continue
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    print(f"\n✓ Actualización completada: {updated}/{len(forecasts)} forecasts")
    print("=" * 60)


if __name__ == "__main__":
    populate_risks()
