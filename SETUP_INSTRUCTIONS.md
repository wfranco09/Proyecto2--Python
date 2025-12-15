# Instrucciones de Configuración e Inicio del Proyecto

## Prerequisitos
- Python 3.13+ instalado
- Node.js y npm instalados
- Virtual environment activado: `source .venv/bin/activate`

---

## Paso 1: Inicializar Base de Datos

La base de datos SQLite se crea automáticamente con las tablas necesarias.

```bash
cd backend
python -c "from core.database.weather_db import init_database; init_database()"
```

**Resultado esperado:**
- Archivo `backend/core/database/raindrop.db` creado
- Tablas creadas: `stations`, `weather_hourly`, `weather_forecast`, `active_alerts`, `incident_reports`

---

## Paso 2: Cargar Estaciones

Las estaciones ya deben estar en el archivo `backend/config.py` (253 estaciones de ETESA).

Para verificar:
```bash
python -c "from config import STATIONS; print(f'Estaciones cargadas: {len(STATIONS)}')"
```

**Resultado esperado:**
```
Estaciones cargadas: 253
```

Si no hay estaciones, ejecutar el scraper:
```bash
python scripts/scrape_stations.py --update-db --limit 253
```

---

## Paso 3: Generar Datos Históricos para Entrenamiento (1 Año)

**Datos Sintéticos con Patrones Estacionales**

Generar 1 año de datos históricos para las 253+ estaciones con patrones estacionales realistas:

```bash
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=365, use_random=False)"
```

**Parámetros:**
- `days=365`: 1 año completo de historia (recomendado para buen entrenamiento)
- `use_random=False`: Usa patrones estacionales realistas de Panamá (recomendado)
- `use_random=True`: Genera datos completamente aleatorios (incluye escenarios extremos)
- `records_per_day=24`: Genera 24 registros/día (1 cada hora)

**Resultado esperado:**
```
✓ ~2,200,000 registros generados (253 estaciones × 365 días × 24 registros/día)
✓ Datos insertados en tabla weather_hourly
✓ Tiempo estimado: 5-10 minutos
```

**Otras opciones:**

Generar solo 90 días (3 meses):
```bash
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=90, use_random=False)"
```

Generar con datos aleatorios (más escenarios de riesgo):
```bash
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=365, use_random=True)"
```

**Opción B: Datos Reales (Si tienes acceso a API de ETESA/IMHPA)**

*Actualmente no implementado - requiere credenciales de API de ETESA*

---

## Paso 4: Entrenar Modelo de Machine Learning

Una vez que hay datos históricos, entrenar el modelo:

```bash
python -c "from services.model_trainer import train_all_models; train_all_models()"
```

**Resultado esperado:**
```
✓ Modelo de inundación entrenado: Accuracy ~85-92%
✓ Modelo de sequía entrenado: Accuracy ~80-88%
✓ Modelos guardados en ml_models/
  - flood_model.joblib
  - drought_model.joblib
  - risk_model.joblib (modelo combinado)
```

**Nota:** El modelo necesita al menos 100+ registros por estación para entrenamiento efectivo.

---

## Paso 5: Configurar Pronósticos Iniciales

Ejecutar pipeline de forecast para obtener pronósticos de las próximas 48 horas:

```bash
cd backend
python -c "from core.pipelines.etl.meteosource.forecast_pipeline import run; run()"
```

**Resultado esperado:**
```
✓ Forecasts obtenidos para 253 estaciones (2 días: hoy y mañana)
✓ Riesgos calculados automáticamente usando modelo ML
✓ 506 pronósticos guardados en weather_forecast (253 × 2 días)
```

**IMPORTANTE:** La API gratuita de Meteosource tiene límite de 500 requests/día. Si alcanzas el límite, espera 24 horas o usa una API key diferente.

**Si encuentras error de límite:**
```
⚠️ Daily amount of requests exceeded
```
Los forecasts se ejecutarán automáticamente cada 6 horas por el scheduler cuando el servidor esté corriendo.

---

## Paso 6: Iniciar Servidor Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Resultado esperado:**
```
✓ Servidor corriendo en http://localhost:8000
✓ Scheduler iniciado (pipelines automáticos cada 6 horas)
✓ Pipeline de forecast ejecutado al inicio
```

**Endpoints disponibles:**
- `GET /api/stations` - Lista de estaciones con riesgos actuales
- `GET /api/forecast?days=2` - Pronósticos para todas las estaciones
- `GET /api/forecast/summary?days=2` - Resumen de alertas por día
- `GET /api/incidents/active` - Reportes de incidentes activos
- `WS /ws/pipeline/{pipeline_id}` - WebSocket para ejecución de pipelines

---

## Paso 7: Iniciar Frontend

En una nueva terminal:

```bash
cd frontend
npm install  # Solo la primera vez
npm run dev
```

**Resultado esperado:**
```
✓ Frontend corriendo en http://localhost:5173
✓ Conectado a backend en http://localhost:8000
```

Abrir navegador en: **http://localhost:5173**

---

## Flujo de Operación Normal

### Pipelines Automáticos (Scheduler)

Una vez que el servidor backend está corriendo, los siguientes pipelines se ejecutan automáticamente:

#### 1. **Forecast Pipeline** (cada 6 horas)
- **Horarios:** 00:00, 06:00, 12:00, 18:00
- **Función:** Obtiene pronósticos de Meteosource API para las próximas 48 horas
- **Proceso:**
  1. Hace request a API para cada estación (253 requests)
  2. Calcula riesgos usando modelo ML
  3. Guarda en `weather_forecast` con riesgos pre-calculados
- **Resultado:** Pronósticos disponibles para frontend (carga en <50ms)

#### 2. **Métricas Horarias** (futuro - cuando se integre ETESA API)
- **Horario:** Cada hora
- **Función:** Obtiene datos climáticos actuales de cada estación
- **Proceso:**
  1. Hace request a API de ETESA/IMHPA
  2. Analiza con modelo ML para determinar riesgo actual
  3. Actualiza tabla `weather_hourly`
  4. Genera alertas automáticas si hay riesgo alto

---

## Verificación de Estado

### Verificar datos en BD:

```bash
python -c "
import sqlite3
from pathlib import Path

db = Path('backend/core/database/raindrop.db')
conn = sqlite3.connect(db)
cursor = conn.cursor()

# Contar registros
cursor.execute('SELECT COUNT(*) FROM stations')
stations_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM weather_hourly')
hourly_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM weather_forecast')
forecast_count = cursor.fetchone()[0]

print(f'Estaciones: {stations_count}')
print(f'Datos históricos: {hourly_count}')
print(f'Pronósticos: {forecast_count}')

conn.close()
"
```

### Verificar modelo entrenado:

```bash
ls -lh backend/ml_models/
```

Deberías ver:
```
risk_model.joblib  (~500KB - 2MB)
```

### Verificar forecast performance:

```bash
curl -s "http://localhost:8000/api/forecast/summary?days=2" | python -m json.tool
```

Debería responder en <50ms con:
```json
{
  "forecast_days": 2,
  "total_stations": 165,
  "daily_summary": [
    {
      "date": "2025-12-16",
      "flood_alerts": 12,
      "drought_alerts": 3,
      "high_flood_risk": 5,
      "high_drought_risk": 1
    },
    {
      "date": "2025-12-17",
      "flood_alerts": 8,
      "drought_alerts": 2,
      "high_flood_risk": 3,
      "high_drought_risk": 0
    }
  ]
}
```

---

## Mantenimiento y Re-entrenamiento

### Re-entrenar modelo con nuevos datos:

A medida que se acumulan más datos históricos reales:

```bash
python -c "from services.model_trainer import train_all_models; train_all_models()"
```

**Recomendación:** Re-entrenar el modelo cada 30-60 días con datos reales para mejorar precisión.

### Limpiar datos de prueba:

```bash
python core/pipelines/etl/clean_dummy_data.py
```

### Generar más datos sintéticos:

```bash
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=60, use_random=False)"
```

---

## Troubleshooting

### Error: "No module named 'config'"

**Solución:** Asegúrate de estar en el directorio `backend/` antes de ejecutar comandos Python.

```bash
cd backend
python -c "..."
```

### Error: "table weather_forecast has no column named flood_probability"

**Solución:** Ejecutar migración para agregar columnas de riesgo:

```bash
cd backend
python migrations/add_risk_columns.py
```

### Error: "Daily amount of requests exceeded" (API Meteosource)

**Solución:** 
1. Esperar 24 horas para que se reinicie el límite
2. Usar una API key diferente en `backend/config.py`:
   ```python
   METEOSOURCE_API_KEY = "tu_nueva_key_aqui"
   ```
3. El scheduler reintentará automáticamente en la próxima ejecución (6 horas)

### Frontend no se conecta al backend

**Verificar:**
1. Backend corriendo en puerto 8000: `curl http://localhost:8000/api/stations`
2. CORS habilitado en `backend/main.py`
3. URL correcta en frontend: `http://localhost:8000`

### Modelo con baja precisión (<70%)

**Causas comunes:**
1. Datos insuficientes (<100 registros por estación)
2. Datos sintéticos muy aleatorios (usar `use_random=False`)
3. Necesita más variedad de escenarios

**Solución:** Generar más datos históricos con patrones estacionales:
```bash
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=90, use_random=False)"
```

---

## Resumen de Comandos Completo

```bash
# 1. Activar entorno virtual
source .venv/bin/activate

# 2. Inicializar BD
cd backend
python -c "from core.database.weather_db import init_database; init_database()"

# 3. Generar datos históricos (30 días)
python -c "from core.pipelines.etl.generate_dummy_data import run; run(days=30, use_random=False)"

# 4. Entrenar modelo
python -c "from services.model_trainer import train_all_models; train_all_models()"

# 5. Ejecutar forecast inicial (opcional - también se ejecuta al iniciar servidor)
python -c "from core.pipelines.etl.meteosource.forecast_pipeline import run; run()"

# 6. Iniciar backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# En otra terminal:
# 7. Iniciar frontend
cd frontend
npm run dev
```

**Tiempo total estimado:** 5-10 minutos

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│                  http://localhost:5173                       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                  http://localhost:8000                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SCHEDULER (APScheduler)                 │   │
│  │  • Forecast Pipeline: cada 6 horas                  │   │
│  │  • Métricas horarias: cada hora (futuro)           │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ML MODEL (scikit-learn)                 │   │
│  │  • RandomForestClassifier                           │   │
│  │  • Entrenado con datos históricos                  │   │
│  │  • Calcula riesgos de inundación/sequía           │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           DATABASE (SQLite)                          │   │
│  │  • stations (253 estaciones ETESA)                 │   │
│  │  • weather_hourly (datos históricos)               │   │
│  │  • weather_forecast (pronósticos con riesgos)      │   │
│  │  • active_alerts (alertas automáticas)             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │ API Requests (cada 6h)
                         │
                ┌────────┴────────┐
                │  Meteosource API │
                │  (Forecasts)     │
                └──────────────────┘
```

---

## Notas Finales

1. **Datos Sintéticos vs Reales:** Los datos sintéticos son suficientes para demostración y desarrollo. Para producción, integrar con APIs reales de ETESA/IMHPA.

2. **Performance:** Con riesgos pre-calculados, los endpoints responden en <50ms para 253 estaciones.

3. **Escalabilidad:** El sistema puede manejar 500+ estaciones sin modificaciones. Para más, considerar PostgreSQL.

4. **Seguridad:** Para producción, agregar autenticación, rate limiting, y HTTPS.

5. **Monitoreo:** Los logs se guardan en `backend/logs/` (si está configurado). Revisar para debugging.
