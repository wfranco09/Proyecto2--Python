"""
SCRIPT: generate_training_dataset.py

OBJETIVO:
- Generar ~11.1 MILLONES de registros climáticos horarios sintéticos
- Dataset 100% compatible con ModelTrainer (SIN modificar el modelo)
- Usar config.py como fuente única de verdad

SALIDA:
- CSV guardado exactamente donde ModelTrainer lo espera
"""

# ============================================================
# IMPORTS
# ============================================================
import numpy as np
import pandas as pd
import random
import math
from datetime import datetime, timedelta

# ============================================================
# CONFIG DEL PROYECTO (MISMO QUE USA EL MODELO)
# ============================================================
from config import (
    FEATURE_COLUMNS,
    MASTER_DATASET,
    DATA_CLEAN_PATH
)

# ============================================================
# SEMILLAS (REPRODUCIBLE)
# ============================================================
np.random.seed(42)
random.seed(42)

# ============================================================
# PARÁMETROS GLOBALES
# ============================================================
START_DATE = datetime(2020, 1, 1)
END_DATE   = datetime(2025, 1, 1)   # 5 años
N_STATIONS = 253                    # ajustado para ~11.1M
OUTPUT_FILE = DATA_CLEAN_PATH / MASTER_DATASET

# ============================================================
# REGIONES DE PANAMÁ Y FACTOR DE LLUVIA
# ============================================================
REGIONS = {
    "BOCAS DEL TORO": 1.4,
    "CHIRIQUI": 1.1,
    "COCLE": 0.9,
    "COLON": 1.3,
    "DARIEN": 1.2,
    "COMARCA": 1.0,
    "GUNA YALA": 1.5,
    "HERRERA": 0.7,
    "LOS SANTOS": 0.6,
    "PANAMA": 1.0,
    "PANAMA OESTE": 0.9,
    "VERAGUAS": 1.1,
}

# ============================================================
# DEFINIMOS ESTA FUNCIÓN PARA CREAR ESTACIONES SINTÉTICAS
# Parámetros: ninguno
# Retorna: DataFrame con metadata básica de estaciones
# ============================================================
def generate_stations():
    stations = []
    regions = list(REGIONS.keys())

    for i in range(N_STATIONS):
        region = random.choice(regions)

        stations.append({
            "station_id": i + 1,
            "region": region,
            "latitude": np.random.uniform(7.0, 9.6),
            "longitude": np.random.uniform(-83.6, -77.2),
            "elevation": np.random.uniform(5, 1200)
        })

    return pd.DataFrame(stations)

# ============================================================
# DEFINIMOS ESTA FUNCIÓN PARA SABER SI ES TEMPORADA LLUVIOSA
# Panamá: mayo a noviembre
# ============================================================
def is_rainy_season(date):
    return 5 <= date.month <= 11

# ============================================================
# DEFINIMOS ESTA FUNCIÓN PARA CICLO DIURNO DE TEMPERATURA
# ============================================================
def diurnal_temperature(hour, tmin, tmax):
    angle = (hour - 6) / 24 * 2 * math.pi
    return (tmax + tmin) / 2 + (tmax - tmin) / 2 * math.sin(angle)

# ============================================================
# FUNCIÓN PRINCIPAL DE GENERACIÓN DEL DATASET
# ============================================================
def generate_dataset():
    print(" Generando estaciones...")
    stations = generate_stations()

    records = []
    current_date = START_DATE

    print(" Generando datos climáticos horarios...")
    while current_date < END_DATE:
        rainy = is_rainy_season(current_date)

        for _, st in stations.iterrows():
            elev_factor = -0.006 * st.elevation
            tmin = 22 + elev_factor
            tmax = 34 + elev_factor
            rain_factor = REGIONS[st.region]

            for hour in range(24):
                # ================================
                # TEMPERATURA
                # ================================
                temperature = diurnal_temperature(hour, tmin, tmax)
                temperature += np.random.normal(0, 0.8)

                # ================================
                # LLUVIA (CLAVE PARA EL MODELO)
                # ================================
                prob = 0.35 if rainy else 0.05
                if rainy and 14 <= hour <= 19:
                    prob += 0.25

                if np.random.rand() < prob:
                    LLUVIA = min(np.random.gamma(2.0, 12.0) * rain_factor, 120)
                else:
                    LLUVIA = 0.0

                # ================================
                # HUMEDAD
                # ================================
                humidity = (
                    np.random.uniform(85, 100)
                    if LLUVIA > 0
                    else np.random.uniform(55, 85)
                )

                # ================================
                # VIENTO
                # ================================
                wind_speed = np.random.uniform(3, 12)
                if LLUVIA > 0:
                    wind_speed += np.random.uniform(5, 15)

                # ================================
                # PRESIÓN
                # ================================
                pressure = 1013 - (st.elevation / 100) * 12
                pressure += np.random.uniform(-2, 2)

                # ================================
                # ARMAMOS EL REGISTRO (USANDO FEATURE_COLUMNS)
                # ================================
                record = {
                    "station_id": st.station_id
                }

                if "TEMP" in FEATURE_COLUMNS:
                    record["TEMP"] = round(temperature, 2)

                if "HUMEDAD" in FEATURE_COLUMNS:
                    record["HUMEDAD"] = round(humidity, 2)

                if "VIENTO" in FEATURE_COLUMNS:
                    record["VIENTO"] = round(wind_speed, 2)

                if "elevation_m" in FEATURE_COLUMNS:
                    record["elevation_m"] = round(pressure, 2)

                if "LLUVIA" in FEATURE_COLUMNS:
                    record["LLUVIA"] = round(LLUVIA, 2)

                records.append(record)

        current_date += timedelta(days=1)

    # ========================================================
    # GUARDAMOS DATASET FINAL
    # ========================================================
    df = pd.DataFrame(records)

    DATA_CLEAN_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("=======================================")
    print(f" Dataset generado correctamente")
    print(f" Filas: {len(df):,}")
    print(f" Archivo: {OUTPUT_FILE}")
    print("=======================================")

# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    generate_dataset()
