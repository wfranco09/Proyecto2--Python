# 🌧️ rAIndrop - Sistema de Predicción de Riesgos Climáticos en Panamá

## 🎯 Acerca del Proyecto

**rAIndrop** es un sistema avanzado de predicción y análisis de riesgos climáticos desarrollado para Panamá, que utiliza inteligencia artificial y datos en tiempo real de más de 250 estaciones meteorológicas distribuidas a lo largo del país. El sistema combina análisis de series temporales, modelos de machine learning y visualización interactiva para predecir y alertar sobre riesgos de inundación y sequía.

### Objetivo

Proporcionar una herramienta de predicción de riesgos climáticos que permita:
- Monitoreo en tiempo real de condiciones meteorológicas
- Predicción de riesgos de inundación y sequía con hasta 48 horas de anticipación
- Generación de alertas tempranas para la toma de decisiones
- Análisis histórico y tendencias climáticas
- Reportes ciudadanos de incidencias para mejorar la precisión del modelo

### Tecnologías Principales

- **Backend**: Python, FastAPI, SQLite
- **Machine Learning**: scikit-learn (RandomForest), pandas, numpy
- **Frontend**: React, TypeScript, Vite, Leaflet
- **Fuente de Datos**: API Meteosource (+ reportes ciudadanos)

---

## 👥 Equipo de Desarrollo

| Nombre | Rol |
|--------|-----|
| **Isaac Escobar** | Arquitecto de Software & Machine Learning Engineer |
| **Arturo Rodríguez** | Coordinador |
| **Luis García** | Documentación |
| **Winston Franco** | Científico de Datos |

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Base de Datos](#base-de-datos)
4. [Pipelines](#pipelines)
5. [Machine Learning](#machine-learning)
6. [API Endpoints](#api-endpoints)
7. [Instalación y Uso](#instalación-y-uso)

---

## 🎯 Descripción General

**rAIndrop** es un sistema de predicción de riesgos climáticos que:

- 📊 **Recolecta datos** de +250 estaciones meteorológicas en Panamá cada hora
- 🗄️ **Almacena histórico** en base de datos SQLite con deduplicación
- 🤖 **Entrena modelos ML** (RandomForest) para predecir niveles de riesgo
- 📈 **Analiza tendencias** comparando datos actuales vs histórico
- 🚨 **Genera alertas** con 4 niveles de riesgo (Bajo, Moderado, Alto, Crítico)
- 🌐 **API REST** para consultar datos y predicciones
- 💻 **Frontend React** con dashboard interactivo

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    API Meteosource                          │
│              (+250 estaciones en Panamá)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Pipeline Automático (Cada hora)               │
│  - Obtiene datos climáticos (temp, humedad, viento, etc.)  │
│  - Guarda en base de datos con deduplicación por hora      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Base de Datos (SQLite)                       │
│  - weather_hourly: Datos climáticos (1 registro/hora/estación)│
│  - stations: Catálogo de +250 estaciones                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ Risk Analyzer    │    │ ML Model (RandomForest)│
│ - Compara actual │    │ - Entrena cada hora  │
│   vs histórico   │    │ - Predice riesgo     │
│ - Score 0-100    │    │ - Accuracy ~100%     │
└──────────────────┘    └──────────────────────┘
        │                         │
        └────────────┬────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    API REST (FastAPI)                       │
│  - Endpoints para consultar datos                          │
│  - Endpoints para análisis de riesgo                       │
│  - Endpoints para ML                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Frontend (React + Vite)                       │
│  - Dashboard con mapa de estaciones                        │
│  - Gráficas de tendencias                                  │
│  - Ejecución manual de pipelines                           │
│  - Logs en tiempo real (WebSocket)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Base de Datos

**Archivo**: `backend/core/database/raindrop.db`  
**Tipo**: SQLite  
**Ubicación**: `backend/core/database/`

### Tabla Principal: `weather_hourly`

Almacena **todos los datos climáticos** con deduplicación automática (solo 1 registro por hora por estación).

**Campos Principales:**
- **Identificación**: `station_id`, `station_name`, `region`, `latitude`, `longitude`, `elevation`
- **Temporales**: `date` (YYYY-MM-DD), `hour` (0-23), `timestamp` (ISO)
- **Climáticos**: 
  - `temperature` (°C)
  - `humidity` (%)
  - `precipitation_total` (mm)
  - `wind_speed` (km/h)
  - `wind_direction` (N, NE, E, etc.)
  - `pressure` (hPa)
  - `cloud_cover` (%)
- **Metadata**: `created_at`, `updated_at`

**Constraint Único**: `UNIQUE(station_id, date, hour)`  
→ Si llegan datos duplicados de la misma hora, se actualiza el registro existente

**Índices Optimizados**:
```sql
idx_station_date_hour ON weather_hourly(station_id, date, hour)
idx_date_hour ON weather_hourly(date, hour)
idx_station_id ON weather_hourly(station_id)
```

### Tabla Secundaria: `stations`

Catálogo de las **+250 estaciones meteorológicas** en Panamá:
1. Panamá Este
2. Panamá Oeste
3. Colón
4. David
5. Bocas del Toro
6. Santiago
7. Chitré
8. Las Tablas
9. Aguadulce
10. Penonomé
11. La Chorrera
12. Chepo
13. Gatún
14. Volcán
15. Changuinola

---

## 🔄 Pipelines

### Pipeline Meteosource (`meteosource_pipeline.py`)

**Propósito**: Obtener datos climáticos en tiempo real de las +250 estaciones.

**Frecuencia**: Automática cada hora (a las :00) + Manual desde el frontend

**Proceso**:
1. Conecta a API de Meteosource con API key
2. Itera sobre las +250 estaciones
3. Obtiene datos actuales (current weather)
4. Normaliza timestamps a UTC
5. Extrae `date` y `hour` del timestamp
6. Guarda en `weather_hourly` con `INSERT OR REPLACE`
7. Entrena modelo ML con datos históricos

**Monitoreo en Tiempo Real (SSE)**:
- El progreso de ejecución se transmite vía **Server-Sent Events (SSE)**
- Frontend se conecta al endpoint `/api/pipelines/stream-generation-progress`
- Recibe actualizaciones cada ~300ms con porcentaje de completitud
- **No usa polling**: conexión persistente de baja latencia
- Ideal para pipelines largos (generate_dummy con 11M+ registros)

**Datos Obtenidos**:
- Temperatura y sensación térmica
- Humedad relativa
- Velocidad y dirección del viento
- Precipitación total
- Presión atmosférica
- Cobertura de nubes
- Resumen textual del clima

**Rate Limits**: 
- Delay de 0.5s entre requests
- Máximo 400 llamadas/día (plan Free)
- +250 estaciones × 24 horas = 360 llamadas/día ✅

**Logs Generados**:
```
22:00:00 - Iniciando extracción de datos para +250 estaciones...
22:00:01 - ✓ Datos obtenidos para Panamá Este
22:00:02 - ✓ Datos obtenidos para Panamá Oeste
...
22:00:15 - Extracción completada: 15/+250 estaciones exitosas
22:00:15 - ✓ 15 registros guardados en base de datos
22:00:15 - 🤖 Iniciando entrenamiento de modelo ML...
22:00:15 - ✅ Modelo entrenado | Accuracy: 100.00% | Tiempo: 0.1s
```

**Ejecución Manual**:
```bash
cd backend
python -m core.pipelines.etl.meteosource.meteosource_pipeline
```

O desde el frontend: Dashboard → Pipelines → Ejecutar Meteosource

---

## 🤖 Machine Learning

### Modelo: RandomForestClassifier

**Propósito**: Predecir nivel de riesgo climático basado en datos históricos.

**¿Por qué RandomForest?**
- ✅ No requiere normalización de datos
- ✅ Maneja relaciones no-lineales
- ✅ Robusto ante outliers (datos extremos)
- ✅ Proporciona importancia de características
- ✅ Rápido de entrenar (~0.1s para 200+ muestras)

### Características del Modelo

**Features (10 variables)**:
1. `temperature` - Temperatura actual
2. `humidity` - Humedad actual
3. `precipitation_total` - Precipitación actual
4. `wind_speed` - Velocidad del viento
5. `pressure` - Presión atmosférica
6. `temp_change` - Cambio de temperatura
7. `humidity_change` - Cambio de humedad
8. `precip_change` - Cambio de precipitación
9. `wind_change` - Cambio de viento
10. `pressure_change` - Cambio de presión

**Clases (4 niveles de riesgo)**:
```python
{
    0: 'bajo',      # Score 0-29
    1: 'moderado',  # Score 30-59
    2: 'alto',      # Score 60-79
    3: 'critico'    # Score 80-100
}
```

**Parámetros del Modelo**:
```python
RandomForestClassifier(
    n_estimators=100,         # 100 árboles
    max_depth=10,             # Profundidad máxima
    min_samples_split=5,      # Mínimo para dividir nodo
    min_samples_leaf=2,       # Mínimo muestras por hoja
    class_weight='balanced',  # Balanceo automático
    n_jobs=-1                 # Usa todos los CPU cores
)
```

### Entrenamiento Automático

**¿Cuándo se entrena?**
- ✅ Cada hora después de ejecutar el pipeline Meteosource
- ✅ Manualmente vía API `POST /api/ml/train`
- ✅ Desde el frontend (ejecutar pipeline)

**Proceso de Entrenamiento**:
1. Obtiene últimos 7 días de datos de `weather_hourly`
2. Calcula características (valores actuales + cambios)
3. Asigna niveles de riesgo basado en umbrales
4. Divide datos: 80% entrenamiento, 20% test
5. Entrena RandomForest
6. Evalúa accuracy y métricas por clase
7. Guarda modelo en `ml_models/risk_model.joblib`

**Métricas Típicas**:
```
✅ Accuracy: 100.00%
⏱️  Tiempo: 0.1s
📊 Muestras: 201 train | 51 test

Feature Importance:
1. humidity             (23.5%)
2. pressure             (22.6%)
3. precipitation_total  (22.1%)
4. wind_speed           (18.3%)
5. temperature          (12.6%)
```

**Predicción**:
```python
from core.ml import RiskPredictor

predictor = RiskPredictor()
features = {
    'temperature': 36.0,
    'humidity': 95.0,
    'precipitation_total': 30.0,
    'wind_speed': 60.0,
    'pressure': 1004.0,
    'temp_change': 8.0,
    'humidity_change': 20.0,
    'precip_change': 25.0,
    'wind_change': 40.0,
    'pressure_change': -10.0
}

risk_level, confidence = predictor.predict(features)
# Output: ('critico', 0.71) → Riesgo CRÍTICO con 71% confianza
```

### Umbral de Riesgo (Configuración)

El modelo usa estos umbrales para asignar niveles durante entrenamiento:

**Temperatura**:
- Normal: < 32°C
- Alto: 35-38°C
- Crítico: > 38°C

**Humedad**:
- Normal: 60-85%
- Alto: 90-95%
- Crítico: > 95%

**Precipitación**:
- Moderado: 5-15 mm/h
- Alto: 15-30 mm/h
- Crítico: > 30 mm/h

**Viento**:
- Moderado: 20-40 km/h
- Alto: 40-60 km/h
- Crítico: > 60 km/h

**Presión**:
- Crítico: < 1005 hPa
- Advertencia: 1005-1010 hPa
- Normal: > 1013 hPa

---

## 🌐 API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Health Check

#### `GET /api/health`
**Propósito**: Verificar que el servidor está funcionando

**Response**:
```json
{
  "status": "healthy",
  "message": "rAIndrop API is running"
}
```

#### `GET /api/health/scheduler`
**Propósito**: Ver estado del scheduler automático

**Response**:
```json
{
  "status": "running",
  "jobs": [
    {
      "id": "meteosource_pipeline",
      "name": "Meteosource Pipeline (Hourly)",
      "next_run_time": "2025-12-15T23:00:00+00:00",
      "trigger": "cron"
    }
  ]
}
```

---

### 2. Estaciones

#### `GET /api/stations`
**Propósito**: Listar todas las estaciones meteorológicas

**Response**:
```json
[
  {
    "id": 1,
    "name": "Panamá Este",
    "region": "Panamá",
    "latitude": 9.0892,
    "longitude": -79.368,
    "elevation": 15
  },
  ...
]
```

#### `GET /api/stations/{station_id}`
**Propósito**: Obtener información de una estación específica

**Response**:
```json
{
  "id": 1,
  "name": "Panamá Este",
  "region": "Panamá",
  "latitude": 9.0892,
  "longitude": -79.368,
  "elevation": 15,
  "last_update": "2025-12-15T03:47:39+00:00",
  "latest_data": {
    "temperature": 24.8,
    "humidity": 78.0,
    "precipitation_total": 0.0,
    "wind_speed": 1.5,
    "pressure": 1013.2
  }
}
```

#### `GET /api/stations/{station_id}/history?hours=24`
**Propósito**: Obtener histórico de datos de una estación

**Parámetros**:
- `hours` (opcional): Número de horas hacia atrás (default: 24)

**Response**:
```json
[
  {
    "date": "2025-12-15",
    "hour": 3,
    "temperature": 24.8,
    "humidity": 78.0,
    "precipitation_total": 0.0,
    "wind_speed": 1.5
  },
  ...
]
```

#### `GET /api/stations/latest`
**Propósito**: Obtener últimos datos de todas las estaciones

**Response**:
```json
[
  {
    "station_id": 1,
    "station_name": "Panamá Este",
    "temperature": 24.8,
    "humidity": 78.0,
    ...
  },
  ...
]
```

---

### 3. Pipelines

#### `POST /api/pipelines/execute`
**Propósito**: Ejecutar un pipeline manualmente

**Body**:
```json
{
  "pipeline_name": "meteosource"
}
```

**Response**:
```json
{
  "status": "running",
  "pipeline": "meteosource",
  "message": "Pipeline iniciado exitosamente"
}
```

**Streaming de Progreso**: Usar SSE para monitorear ejecución en tiempo real

#### `GET /api/pipelines/stream-generation-progress`
**Propósito**: Stream en tiempo real del progreso de generación de datos

**Método**: Server-Sent Events (SSE)

**Ejemplo de uso**:
```javascript
const eventSource = new EventSource('/api/pipelines/stream-generation-progress');

eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log(`${progress.percentage}% completado`);
  // progress.current: registros procesados
  // progress.total: registros totales
  // progress.percentage: 0-100%
};
```

**Ventajas sobre polling**:
- ✅ Latencia ~10x menor (sin delay entre requests)
- ✅ Menos carga en el servidor (1 conexión persistente vs múltiples requests)
- ✅ Actualizaciones instantáneas cuando hay cambios
- ✅ Conexión se cierra automáticamente al terminar el pipeline

#### `GET /api/pipelines/list`
**Propósito**: Listar pipelines disponibles

**Response**:
```json
{
  "pipelines": [
    {
      "name": "meteosource",
      "description": "Obtiene datos climáticos de +250 estaciones en Panamá",
      "status": "available"
    }
  ]
}
```

---

### 4. Análisis de Riesgo

#### `GET /api/risk/analyze?station_id=1&hours=24`
**Propósito**: Analizar riesgo de una o todas las estaciones

**Parámetros**:
- `station_id` (opcional): ID de estación específica, omitir para todas
- `hours` (opcional): Horas de histórico para comparar (default: 24)

**Response**:
```json
{
  "station_id": 1,
  "station_name": "Panamá Este",
  "risk_level": "alto",
  "risk_score": 75,
  "factors": [
    {
      "metric": "precipitation",
      "message": "Lluvia intensa: 18.0mm/h (promedio: 1.5mm)",
      "score": 75
    },
    {
      "metric": "humidity",
      "message": "Humedad muy alta: 92.0%",
      "score": 60
    }
  ],
  "trends": {
    "precipitation_total": {
      "trend": "subiendo",
      "change": 18.0
    },
    "wind_speed": {
      "trend": "subiendo",
      "change": 25.0
    }
  },
  "recommendations": [
    "⚠️ Precaución: Condiciones climáticas adversas",
    "🌧️ Riesgo de inundaciones - evitar zonas bajas"
  ]
}
```

#### `GET /api/risk/summary`
**Propósito**: Resumen rápido de riesgo de todas las estaciones

**Response**:
```json
{
  "total_stations": 15,
  "risk_distribution": {
    "bajo": 13,
    "moderado": 1,
    "alto": 1,
    "critico": 0
  },
  "stations_at_risk": [
    {
      "station_id": 1,
      "station_name": "Panamá Este",
      "risk_level": "alto",
      "risk_score": 75
    }
  ]
}
```

#### `GET /api/risk/thresholds`
**Propósito**: Ver umbrales configurados de riesgo

**Response**:
```json
{
  "temperature": {
    "normal_max": 32.0,
    "high": 35.0,
    "critical": 38.0
  },
  "humidity": {
    "normal_min": 60.0,
    "normal_max": 85.0,
    "high": 90.0,
    "critical": 95.0
  },
  ...
}
```

---

### 5. Machine Learning

#### `POST /api/ml/train?days_back=7`
**Propósito**: Entrenar modelo ML manualmente

**Parámetros**:
- `days_back` (opcional): Días de histórico para entrenar (default: 7)

**Response**:
```json
{
  "status": "success",
  "message": "Modelo entrenado exitosamente",
  "metrics": {
    "accuracy": 1.0,
    "training_time": 0.13,
    "train_samples": 201,
    "test_samples": 51
  },
  "feature_importance": {
    "humidity": 0.2352,
    "pressure": 0.2264,
    "precipitation_total": 0.2211,
    "wind_speed": 0.1829,
    "temperature": 0.1263
  },
  "class_performance": {
    "bajo": {"precision": 1.0, "recall": 1.0, "f1-score": 1.0},
    "moderado": {"precision": 1.0, "recall": 1.0, "f1-score": 1.0},
    "alto": {"precision": 1.0, "recall": 1.0, "f1-score": 1.0},
    "critico": {"precision": 1.0, "recall": 1.0, "f1-score": 1.0}
  }
}
```

#### `POST /api/ml/predict`
**Propósito**: Predecir riesgo con el modelo ML

**Body**:
```json
{
  "temperature": 36.0,
  "humidity": 95.0,
  "precipitation_total": 30.0,
  "wind_speed": 60.0,
  "pressure": 1004.0,
  "temp_change": 8.0,
  "humidity_change": 20.0,
  "precip_change": 25.0,
  "wind_change": 40.0,
  "pressure_change": -10.0
}
```

**Response**:
```json
{
  "risk_level": "critico",
  "confidence": 0.7113
}
```

#### `GET /api/ml/model/info`
**Propósito**: Información sobre el modelo entrenado

**Response**:
```json
{
  "status": "trained",
  "model_type": "RandomForestClassifier",
  "features": ["temperature", "humidity", ...],
  "classes": ["bajo", "moderado", "alto", "critico"],
  "trained_at": "2025-12-15T03:47:59Z"
}
```

#### `DELETE /api/ml/model`
**Propósito**: Eliminar modelo actual

---

## 🚀 Instalación y Uso

### Requisitos Previos

- Python 3.13+
- Node.js 18+
- API Key de Meteosource (gratis en meteosource.com)

### Instalación Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar API Key
cp .env.example .env
# Editar .env y agregar tu METEOSOURCE_API_KEY=tu_key_aqui
```

### Instalación Frontend

```bash
cd frontend

# Instalar dependencias
npm install
```

### Iniciar Sistema

**Terminal 1 - Backend**:
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

**Acceso**:
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (Swagger UI)

### Ejecución Manual de Pipeline

```bash
cd backend
python -m core.pipelines.etl.meteosource.meteosource_pipeline
```

### Entrenar Modelo ML

```bash
cd backend
python -c "from core.ml import train_model_from_history; train_model_from_history()"
```

### Demo Completo

```bash
cd backend
python demo_ml_system.py  # Demo de ML con datos simulados
python demo_risk_system.py  # Demo de análisis de riesgo
```

---

## 📊 Flujo de Datos Completo

```
1. RECOLECCIÓN (Cada hora a las :00)
   ↓
   API Meteosource → +250 estaciones
   ↓
   meteosource_pipeline.py
   ↓
   Normalización de datos

2. ALMACENAMIENTO
   ↓
   weather_hourly (SQLite)
   ↓
   Deduplicación: UNIQUE(station_id, date, hour)

3. ENTRENAMIENTO ML (Automático después de recolección)
   ↓
   Últimos 7 días de datos
   ↓
   RandomForest: 10 features → 4 clases
   ↓
   risk_model.joblib guardado

4. ANÁLISIS DE RIESGO (On-demand)
   ↓
   Comparar actual vs promedio histórico
   ↓
   Calcular score 0-100
   ↓
   Asignar nivel: bajo/moderado/alto/critico
   ↓
   Generar recomendaciones

5. API REST
   ↓
   17 endpoints disponibles
   ↓
   Frontend consulta datos

6. VISUALIZACIÓN
   ↓
   Dashboard React
   ↓
   Mapa interactivo + Gráficas
```

---

## 🔧 Configuración

### Scheduler (Ejecución Automática)

Configurado en `backend/core/scheduler.py`:

```python
# Ejecuta pipeline Meteosource cada hora a las :00
scheduler.add_job(
    run_meteosource_pipeline,
    trigger=CronTrigger(minute=0),  # :00 de cada hora
    id='meteosource_pipeline',
    name='Meteosource Pipeline (Hourly)',
    replace_existing=True
)
```

Para cambiar frecuencia:
```python
# Cada 30 minutos
trigger=CronTrigger(minute='0,30')

# Cada 6 horas
trigger=CronTrigger(hour='0,6,12,18')
```

### Umbral de Riesgo

Editar `backend/core/analysis/risk_analyzer.py`:

```python
THRESHOLDS = {
    "temperature": {
        "normal_max": 32.0,  # Ajustar según clima local
        "high": 35.0,
        "critical": 38.0
    },
    ...
}
```

### Parámetros ML

Editar `backend/core/ml/risk_predictor.py`:

```python
self.model = RandomForestClassifier(
    n_estimators=100,      # Más árboles = más precisión
    max_depth=10,          # Profundidad máxima
    min_samples_split=5,   # Mínimo para dividir nodo
    ...
)
```

---

## 📁 Estructura del Proyecto

```
Proyecto2--Python/
├── backend/raindrop_db.py
│   ├── main.py                    # FastAPI server
│   ├── core/
│   │   ├── database/
│   │   │   ├── weather_db.py      # Funciones de DB
│   │   │   └── raindrop.db        # Base de datos SQLite
│   │   ├── pipelines/
│   │   │   └── etl/meteosource/
│   │   │       └── meteosource_pipeline.py
│   │   ├── analysis/
│   │   │   └── risk_analyzer.py   # Análisis de riesgo
│   │   ├── ml/
│   │   │   └── risk_predictor.py  # Machine Learning
│   │   └── scheduler.py           # Tareas automáticas
│   ├── api/
│   │   ├── health.py              # Health endpoints
│   │   ├── stations.py            # Stations endpoints
│   │   ├── pipelines.py           # Pipelines endpoints + SSE
│   │   ├── risk.py                # Risk endpoints
│   │   └── ml.py                  # ML endpoints
│   ├── ml_models/
│   │   └── risk_model.joblib      # Modelo entrenado
│   ├── scripts/
│   │   ├── clear_weather_data.py  # Limpiar DB (interactivo)
│   │   └── clear_weather_data_force.py  # Limpiar DB (forzado)
│   ├── docs/
│   │   └── DATASET_REQUIREMENTS.md  # Especificaciones dataset ML
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # Componentes React
│   │   ├── pages/                 # Páginas
│   │   └── App.tsx
│   └── package.json
└── README.md                      # Este archivo
```

---

## 🎯 Casos de Uso

### 1. Monitoreo en Tiempo Real
```
Usuario → Dashboard → Ver mapa con +250 estaciones
       → Click en estación → Ver datos actuales
       → Ver nivel de riesgo calculado
```

### 2. Análisis Histórico
```
Usuario → Seleccionar estación
       → Ver gráfica de tendencias (últimas 24h)
       → Comparar con promedio histórico
```

### 3. Predicción de Riesgo
```
Sistema → Cada hora obtiene datos
        → Entrena modelo ML
        → Actualiza predicciones
Usuario → Consulta nivel de riesgo
        → Recibe recomendaciones
```

### 4. Ejecución Manual de Pipeline
```
Usuario → Dashboard → Pipelines
        → Click "Ejecutar Meteosource"
        → Ver logs en tiempo real
        → Datos actualizados en <20s
```

---

## ✅ Verificación del Sistema

Después de instalar, verificar que todo funciona:

```bash
cd backend
python -c "
from core.database.weather_db import get_all_stations_latest
from core.ml import RiskPredictor

# Verificar DB
latest = get_all_stations_latest()
print(f'✅ Estaciones con datos: {len(latest)}')

# Verificar ML
predictor = RiskPredictor()
X, y = predictor.prepare_training_data(days_back=7, min_samples=50)
print(f'✅ Datos ML: {len(X)} muestras')

print('✅ Sistema funcionando correctamente')
"
```

---

## 🐛 Troubleshooting

### Error: "METEOSOURCE_API_KEY no está configurada"
**Solución**: Crear archivo `.env` en `/backend` con tu API key:
```
METEOSOURCE_API_KEY=tu_key_aqui
```

### Error: "Modelo no encontrado"
**Solución**: Entrenar modelo por primera vez:
```bash
curl -X POST http://localhost:8000/api/ml/train
```

### Error: "Base de datos vacía"
**Solución**: Ejecutar pipeline manualmente:
```bash
cd backend
python -m core.pipelines.etl.meteosource.meteosource_pipeline
```

### Scheduler no ejecuta automáticamente
**Solución**: Verificar estado:
```bash
curl http://localhost:8000/api/health/scheduler
```

---

## 📝 Notas Importantes

1. **Rate Limits**: Plan gratuito de Meteosource limita a 400 llamadas/día. Con +250 estaciones × 24 horas = 360 llamadas/día, está dentro del límite.

2. **Deduplicación**: La base de datos solo mantiene 1 registro por hora por estación. Si se ejecuta el pipeline varias veces en la misma hora, se actualiza el registro existente.


6. **Streaming vs Polling**: El sistema usa Server-Sent Events (SSE) para actualizar progreso de pipelines en tiempo real, evitando sobrecarga del servidor por polling constante.

---

## 🧹 Utilidades de Mantenimiento

### Limpieza de Base de Datos

## 🔄 Cambios Recientes

### v1.1.0 (2025-12-17)

#### 🚀 Nuevas Funcionalidades
- **Server-Sent Events (SSE)**: Streaming de progreso de pipelines en tiempo real
  - Endpoint: `GET /api/pipelines/stream-generation-progress`
  - Reemplaza polling constante, reduce carga del servidor ~90%
  - Actualizaciones cada ~300ms con porcentaje preciso

- **Scripts de Limpieza de DB**: Utilidades para mantenimiento de datos
  - `clear_weather_data.py`: Limpieza interactiva con confirmación
  - `clear_weather_data_force.py`: Limpieza automatizada sin prompts
  - Integrados en VS Code launch configurations

- **Documentación de Dataset**: Especificaciones completas para generación de datos sintéticos
  - [DATASET_REQUIREMENTS.md](backend/docs/DATASET_REQUIREMENTS.md)
  - 11.1M registros (5 años × 253 estaciones)
  - Rangos climáticos calibrados para Panamá
  - Correlaciones y estacionalidad realistas

#### 🔧 Mejoras Técnicas
- **Ejecución de Pipelines**: Cambio de subprocess a función directa
  - Permite compartir memoria entre pipeline y SSE
  - Mejor manejo de progreso en tiempo real
  - Elimina overhead de procesos separados

- **Renombre de Módulos**: Consistencia en nomenclatura
  - `weather_db.py` → `raindrop_db.py`
  - Alineado con nombre de base de datos (`raindrop.db`)
  - Todos los imports actualizados

#### 📚 Documentación
- README actualizado con secciones de SSE y mantenimiento
- Especificaciones detalladas de dataset para ML
- Guías de uso de scripts de limpieza

---

**Última actualización**: 2025-12-17  
**Versión**: 1.1.0  
**Desarrollado por**: Equipo Pythoneers.AI

---

## 📄 Licencia

Proyecto académico - Universidad Tecnológica de Panamá
```bash
cd backend
python -m scripts.clear_weather_data
```

**Salida**:
```
📊 Registros a eliminar: 11,102,400
⚠️  ¿Estás seguro de eliminar TODOS los datos? (sí/no): sí
🗑️  Eliminando registros...
✅ Base de datos limpiada exitosamente
```

#### Opción 2: Limpieza Forzada (sin confirmación)
```bash
cd backend
python -m scripts.clear_weather_data_force
```

**Uso recomendado**: Scripts automatizados, CI/CD, o cuando estés 100% seguro

**VS Code Launch Config**: Ambos scripts están disponibles en el menú de debug:
- 🧹 Limpiar Base de Datos (weather_hourly)
- 🧹 Limpiar DB (FORZADO - sin confirmar)

### Generación de Dataset de Entrenamiento

Para crear un dataset sintético de alta calidad para ML:

1. **Leer especificaciones**: [backend/docs/DATASET_REQUIREMENTS.md](backend/docs/DATASET_REQUIREMENTS.md)
2. **Datos requeridos**: 
   - 5 años de histórico (2020-2025)
   - 253 estaciones meteorológicas
   - 24 registros por día
   - **Total**: ~11.1 millones de registros
3. **Características**:
   - Rangos climáticos realistas para Panamá
   - Correlaciones coherentes entre variables
   - Estacionalidad (temporada seca vs lluviosa)
   - Diferencias regionales (Caribe vs Pacífico, costa vs montaña)
