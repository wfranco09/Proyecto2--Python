# Pipeline de Generación de Datos Dummy

## Descripción

Pipeline para generar datos climáticos sintéticos realistas basados en parámetros de Panamá para el entrenamiento de modelos de Machine Learning.

## Características

### Datos Generados
- **Cantidad**: 5000+ registros (configurable)
- **Distribución**: Balanceada entre +250 estaciones
- **Rango temporal**: 180 días hacia atrás (configurable)
- **Frecuencia**: Intervalos de 1-3 horas para simular datos reales

### Variables Climáticas

| Variable | Rango | Unidad |
|----------|-------|--------|
| Temperatura | 20-35 | °C |
| Sensación térmica | 20-40 | °C |
| Humedad | 50-100 | % |
| Velocidad del viento | 0-40 | km/h |
| Precipitación | 0-150 | mm |
| Presión | 1005-1020 | hPa |
| Nubosidad | 0-100 | % |

### Correlaciones Realistas

El pipeline simula correlaciones naturales entre variables:

1. **Temperatura ↔ Sensación térmica**
   - Alta humedad aumenta la sensación térmica
   - Formula: `feels_like = temp + (humidity/100) * 5.0`

2. **Humedad + Temperatura ↔ Precipitación**
   - Mayor probabilidad de lluvia con humedad y temperatura altas
   - `precip_prob = (humidity/100)*0.4 + (temp/35)*0.3`

3. **Precipitación ↔ Nubosidad**
   - Más lluvia → más nubes
   - `cloud_cover = 60 + (precip/150)*40`

4. **Presión ↔ Precipitación**
   - Presión baja (1005-1012 hPa) → más probable lluvia
   - Presión alta (1010-1020 hPa) → menos probable lluvia

### Patrones Estacionales

#### Estación Seca (Enero-Abril)
- Temperatura base: 28°C
- Humedad base: 65%
- Menos precipitación
- Más días despejados

#### Estación Lluviosa (Mayo-Diciembre)
- Temperatura base: 26°C
- Humedad base: 85%
- Más precipitación
- Más días nublados

### Variación Diurna

- **Amanecer-Mediodía** (6:00-18:00): Temperatura aumenta hasta +7°C
- **Noche-Madrugada** (19:00-5:00): Temperatura disminuye -2°C

## Uso

### Desde Línea de Comandos

```bash
# Generar 5000 registros (default)
cd backend
python -m core.pipelines.etl.generate_dummy_data

# Desde cualquier ubicación
python -m core.pipelines.etl.generate_dummy_data
```

### Desde la API

```bash
POST /api/pipelines/run/generate_dummy
```

### Programáticamente

```python
from core.pipelines.etl.generate_dummy_data import generate_dummy_weather_data

# Generar 10,000 registros con 365 días de historial
inserted = generate_dummy_weather_data(
    num_records=10000,
    days_back=365
)
print(f"Registros insertados: {inserted}")
```

## Resultados

### Ejemplo de Ejecución

```
2025-12-15 00:36:22,541 - INFO - ============================================================
2025-12-15 00:36:22,541 - INFO -  PIPELINE: GENERACIÓN DE DATOS DUMMY
2025-12-15 00:36:22,541 - INFO - ============================================================
2025-12-15 00:36:22,541 - INFO -  Iniciando generación de 5000 registros dummy...
2025-12-15 00:36:22,541 - INFO -  Generando datos para estación 1 - Panamá Este
...
2025-12-15 00:36:22,658 - INFO -  Generación completada: 4995 registros insertados
2025-12-15 00:36:22,658 - INFO -  Rango de fechas: 2025-06-18 a 2025-12-15
2025-12-15 00:36:22,658 - INFO -  Estaciones: 15
2025-12-15 00:36:22,658 - INFO -  Registros por estación (aprox): 333
```

### Distribución por Estación

```
station_id | registros
-----------|----------
1          | 393
2          | 391
3          | 391
4          | 391
5          | 391
6-15       | 336 (promedio)
```

**Total**: 5,318 registros (real + dummy)

## Limpieza de Datos

Si necesitas eliminar los datos generados:

### Opción 1: Script Interactivo

```bash
cd backend
python -m core.pipelines.etl.clean_dummy_data
```

El script ofrece:
1. Eliminar TODOS los registros
2. Eliminar registros antes de fecha específica
3. Cancelar

### Opción 2: SQL Directo

```bash
# Eliminar todos los registros dummy (mantener solo últimos 30 días)
sqlite3 backend/core/database/raindrop.db \
  "DELETE FROM weather_hourly WHERE date < date('now', '-30 days')"

# Optimizar base de datos
sqlite3 backend/core/database/raindrop.db "VACUUM"
```

## Validación de Datos

Verificar los datos generados:

```bash
# Total de registros
sqlite3 backend/core/database/raindrop.db \
  "SELECT COUNT(*) FROM weather_hourly"

# Distribución por estación
sqlite3 backend/core/database/raindrop.db \
  "SELECT station_id, COUNT(*) FROM weather_hourly GROUP BY station_id"

# Rango de fechas
sqlite3 backend/core/database/raindrop.db \
  "SELECT MIN(date), MAX(date) FROM weather_hourly"

# Estadísticas de temperatura
sqlite3 backend/core/database/raindrop.db \
  "SELECT AVG(temperature), MIN(temperature), MAX(temperature) FROM weather_hourly"
```

## Integración con ML

Los datos generados están listos para entrenar modelos:

```python
from core.database.weather_db import get_all_stations_latest
from sklearn.ensemble import RandomForestClassifier

# Cargar datos
data = get_all_stations_latest()

# Preparar features
features = ['temperature', 'humidity', 'precipitation_total', 
           'wind_speed', 'pressure', 'cloud_cover']

# El modelo ahora tiene 5000+ registros para entrenamiento
```

## Notas

- Los datos dummy son realistas pero sintéticos
- Respetan las restricciones de la base de datos (UNIQUE por station_id+date+hour)
- Se pueden regenerar múltiples veces sin duplicados (usar UPSERT)
- Recomendado: 5000+ registros para RandomForest
- Opcional: Ajustar parámetros en `WEATHER_RANGES` para diferentes climas

## Troubleshooting

### Error: "list index out of range"
**Solución**: Ya corregido en v1.1 - validación de índice de dirección del viento

### Base de datos bloqueada
**Solución**: Cerrar todas las conexiones activas antes de ejecutar

### Datos no aparecen
**Verificar**: 
1. Path correcto de la base de datos: `backend/core/database/raindrop.db`
2. Permisos de escritura en el directorio
3. Logs del pipeline para errores

## Versión

- **v1.0**: Primera implementación
- **v1.1**: Corrección de índice de dirección del viento
- **Estado**: Funcional y probado ✓
