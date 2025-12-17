#!/usr/bin/env python3
"""
Script de prueba para verificar que los riesgos se calculan y almacenan correctamente.
"""
from datetime import date, timedelta
from core.database.raindrop_db import insert_or_update_forecast_data
from pathlib import Path
from core.ml.risk_predictor import RiskPredictor

def generate_test_forecasts():
    """Genera datos de forecast de prueba con riesgos calculados."""
    
    # Cargar modelo ML
    model_path = Path(__file__).parent / "ml_models" / "risk_model.joblib"
    predictor = None
    if model_path.exists():
        predictor = RiskPredictor(model_path=model_path)
        print(f"✓ Modelo ML cargado desde {model_path}")
    else:
        print(f"⚠ Modelo ML no encontrado, usando valores por defecto")
    
    # Datos de prueba para 3 estaciones, 2 días
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    test_data = []
    
    # Estación 1: Alto riesgo de inundación
    for day in [today, tomorrow]:
        forecast = {
            "station_id": 1,
            "forecast_date": day.isoformat(),
            "temperature": 28.0,
            "humidity": 95.0,
            "precipitation_total": 150.0,  # Mucha lluvia
            "precipitation_probability": 90,
            "wind_speed_max": 25.0,
            "pressure": 1010.0,
            "cloud_cover": 90,
            "uv_index": 5,
            "temp_min": 24.0,
            "temp_max": 32.0,
            "summary": "Heavy rain expected",
            "icon": "rain"
        }
        
        # Calcular riesgos
        if predictor:
            features = {
                'temperature': forecast['temperature'],
                'humidity': forecast['humidity'],
                'precipitation': forecast['precipitation_total'],
                'wind_speed': forecast['wind_speed_max'],
                'pressure': forecast['pressure'],
                'cloud_cover': forecast['cloud_cover'],
                'uv_index': forecast['uv_index'],
            }
            flood_risk = predictor.predict(features)
            forecast["flood_probability"] = flood_risk[1]
            forecast["flood_level"] = flood_risk[0]
            forecast["flood_alert"] = 1 if flood_risk[0] in ["YELLOW", "RED"] else 0
            
            # Por ahora drought usa mismas features (ajustar en producción)
            drought_risk = predictor.predict(features)
            forecast["drought_probability"] = drought_risk[1] * 0.1  # Reducir para drought
            forecast["drought_level"] = "GREEN"
            forecast["drought_alert"] = 0
        else:
            # Valores por defecto - alto riesgo de inundación
            forecast["flood_probability"] = 0.85
            forecast["flood_level"] = "RED"
            forecast["flood_alert"] = 1
            forecast["drought_probability"] = 0.1
            forecast["drought_level"] = "GREEN"
            forecast["drought_alert"] = 0
        
        test_data.append(forecast)
    
    # Estación 2: Riesgo moderado
    for day in [today, tomorrow]:
        forecast = {
            "station_id": 2,
            "forecast_date": day.isoformat(),
            "temperature": 27.0,
            "humidity": 70.0,
            "precipitation_total": 25.0,  # Lluvia moderada
            "precipitation_probability": 60,
            "wind_speed_max": 15.0,
            "pressure": 1013.0,
            "cloud_cover": 60,
            "uv_index": 6,
            "temp_min": 23.0,
            "temp_max": 31.0,
            "summary": "Partly cloudy with rain",
            "icon": "partly-cloudy"
        }
        
        if predictor:
            features = {
                'temperature': forecast['temperature'],
                'humidity': forecast['humidity'],
                'precipitation': forecast['precipitation_total'],
                'wind_speed': forecast['wind_speed_max'],
                'pressure': forecast['pressure'],
                'cloud_cover': forecast['cloud_cover'],
                'uv_index': forecast['uv_index'],
            }
            flood_risk = predictor.predict(features)
            forecast["flood_probability"] = flood_risk[1]
            forecast["flood_level"] = flood_risk[0]
            forecast["flood_alert"] = 1 if flood_risk[0] in ["YELLOW", "RED"] else 0
            
            drought_risk = predictor.predict(features)
            forecast["drought_probability"] = drought_risk[1] * 0.3
            forecast["drought_level"] = "GREEN"
            forecast["drought_alert"] = 0
        else:
            forecast["flood_probability"] = 0.55
            forecast["flood_level"] = "YELLOW"
            forecast["flood_alert"] = 1
            forecast["drought_probability"] = 0.2
            forecast["drought_level"] = "GREEN"
            forecast["drought_alert"] = 0
        
        test_data.append(forecast)
    
    # Estación 3: Bajo riesgo
    for day in [today, tomorrow]:
        forecast = {
            "station_id": 3,
            "forecast_date": day.isoformat(),
            "temperature": 29.0,
            "humidity": 50.0,
            "precipitation_total": 2.0,  # Poca lluvia
            "precipitation_probability": 20,
            "wind_speed_max": 10.0,
            "pressure": 1015.0,
            "cloud_cover": 30,
            "uv_index": 8,
            "temp_min": 25.0,
            "temp_max": 33.0,
            "summary": "Mostly sunny",
            "icon": "sunny"
        }
        
        if predictor:
            features = {
                'temperature': forecast['temperature'],
                'humidity': forecast['humidity'],
                'precipitation': forecast['precipitation_total'],
                'wind_speed': forecast['wind_speed_max'],
                'pressure': forecast['pressure'],
                'cloud_cover': forecast['cloud_cover'],
                'uv_index': forecast['uv_index'],
            }
            flood_risk = predictor.predict(features)
            forecast["flood_probability"] = flood_risk[1]
            forecast["flood_level"] = flood_risk[0]
            forecast["flood_alert"] = 1 if flood_risk[0] in ["YELLOW", "RED"] else 0
            
            drought_risk = predictor.predict(features)
            forecast["drought_probability"] = drought_risk[1] * 0.8  # Más probable sequía
            forecast["drought_level"] = drought_risk[0]
            forecast["drought_alert"] = 1 if drought_risk[0] in ["YELLOW", "RED"] else 0
        else:
            forecast["flood_probability"] = 0.15
            forecast["flood_level"] = "GREEN"
            forecast["flood_alert"] = 0
            forecast["drought_probability"] = 0.45
            forecast["drought_level"] = "YELLOW"
            forecast["drought_alert"] = 1
        
        test_data.append(forecast)
    
    return test_data


if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Almacenamiento de riesgos pre-calculados")
    print("=" * 60)
    
    # Generar datos de prueba
    test_forecasts = generate_test_forecasts()
    print(f"\n✓ Generados {len(test_forecasts)} pronósticos de prueba")
    
    # Guardar en BD
    saved = insert_or_update_forecast_data(test_forecasts)
    print(f"✓ Guardados {saved} pronósticos en la BD")
    
    # Verificar que se guardaron con riesgos
    import sqlite3
    conn = sqlite3.connect("database/weather.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT station_id, forecast_date, 
               flood_probability, flood_level, flood_alert,
               drought_probability, drought_level, drought_alert
        FROM weather_forecast
        ORDER BY station_id, forecast_date
    """)
    
    rows = cursor.fetchall()
    print(f"\n✓ Verificación en BD ({len(rows)} registros):")
    print("-" * 60)
    for row in rows:
        print(f"Estación {row[0]}, Fecha {row[1]}:")
        print(f"  Flood:   prob={row[2]:.3f}, level={row[3]}, alert={row[4]}")
        print(f"  Drought: prob={row[5]:.3f}, level={row[6]}, alert={row[7]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ TEST COMPLETADO")
    print("=" * 60)
    print("\nAhora puedes probar los endpoints:")
    print("  curl 'http://localhost:8000/api/forecast/summary?days=2'")
    print("  curl 'http://localhost:8000/api/forecast?days=2'")
