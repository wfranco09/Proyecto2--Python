# Requerimientos para Generación de Dataset de Entrenamiento ML

## 📋 Objetivo

Crear un script automatizado que genere un dataset sintético **coherente y realista** para poblar la tabla `weather_hourly` con datos climáticos históricos de Panamá. Este dataset será utilizado como fuente principal para el entrenamiento del modelo de Machine Learning de predicción de riesgos.

---

## 📊 Especificaciones del Dataset

### Dimensiones Requeridas

- **Período temporal**: 5 años de datos históricos (1,825 días)
- **Frecuencia**: Registros horarios (24 registros por día)
- **Cobertura geográfica**: 253 estaciones meteorológicas (todas las estaciones en la tabla `stations`)
- **Total de registros**: **11,102,400 registros**
  - Cálculo: `253 estaciones × 5 años × 365 días × 24 horas = 11,102,400`

### Rango de Fechas

- **Fecha inicio**: 16 de diciembre de 2020 (5 años antes de hoy)
- **Fecha fin**: 16 de diciembre de 2025 (fecha actual)
- **Nota**: Considerar años bisiestos (2024 tiene 366 días)

---

## 🗄️ Estructura de la Tabla `weather_hourly`

El script debe generar datos para las siguientes columnas:

| Columna | Tipo | Descripción | Requerimientos |
|---------|------|-------------|----------------|
| `station_id` | INTEGER | ID de la estación | FK a tabla `stations` |
| `station_name` | TEXT | Nombre de la estación | Obtener de tabla `stations` |
| `region` | TEXT | Región de Panamá | Una de las 12 regiones |
| `latitude` | REAL | Latitud | Coordenada de la estación |
| `longitude` | REAL | Longitud | Coordenada de la estación |
| `elevation` | INTEGER | Elevación (metros) | Altura sobre nivel del mar |
| `date` | TEXT | Fecha (YYYY-MM-DD) | Sin duplicados para misma estación+hora |
| `hour` | INTEGER | Hora del día (0-23) | 24 registros por día |
| `timestamp` | TEXT | ISO 8601 timestamp | `YYYY-MM-DDTHH:00:00+00:00` |
| `temperature` | REAL | Temperatura (°C) | Ver rangos climáticos |
| `feels_like` | REAL | Sensación térmica (°C) | Correlacionada con temp, humedad, viento |
| `humidity` | REAL | Humedad relativa (%) | 40-100% |
| `wind_speed` | REAL | Velocidad del viento (km/h) | 0-60 km/h (hasta 100 en tormentas) |
| `wind_direction` | TEXT | Dirección del viento | N, NE, E, SE, S, SW, W, NW |
| `wind_angle` | INTEGER | Ángulo del viento (°) | 0-360° |
| `precipitation_total` | REAL | Precipitación total (mm) | 0-150 mm/hora (extremos raros) |
| `precipitation_type` | TEXT | Tipo de precipitación | rain, none |
| `pressure` | REAL | Presión atmosférica (hPa) | 1005-1020 hPa (nivel del mar) |
| `cloud_cover` | INTEGER | Cobertura de nubes (%) | 0-100% |
| `summary` | TEXT | Descripción del clima | Texto descriptivo |
| `icon` | TEXT | Código de ícono | cloudy, partly_sunny, rainy, etc. |
| `created_at` | TEXT | Fecha de creación | Timestamp actual |
| `updated_at` | TEXT | Fecha de actualización | Timestamp actual |

---

## 🌡️ Rangos Climáticos Realistas para Panamá

### Temperatura por Región y Elevación

| Región | Elevación | Temp Mín (°C) | Temp Máx (°C) | Temp Media (°C) |
|--------|-----------|---------------|---------------|-----------------|
| **Costera** (0-200m) | Baja | 22 | 34 | 27 |
| **Valle/Media** (200-800m) | Media | 18 | 32 | 25 |
| **Montaña** (800-2000m) | Alta | 12 | 26 | 19 |
| **Alta montaña** (>2000m) | Muy Alta | 8 | 22 | 15 |

### Variación Diaria de Temperatura

- **Hora más fría**: 5:00-6:00 AM (temp mínima)
- **Hora más cálida**: 1:00-3:00 PM (temp máxima)
- **Variación diurna típica**: 8-12°C entre min/max

### Estacionalidad en Panamá

#### Temporada Seca (Diciembre - Abril)
- Menor precipitación (0-5 mm/día en promedio)
- Temperaturas más altas
- Humedad relativa menor (60-75%)
- Cielos más despejados

#### Temporada Lluviosa (Mayo - Noviembre)
- Mayor precipitación (10-50 mm/día, picos de 100+ mm)
- Temperaturas ligeramente más bajas
- Humedad relativa alta (75-95%)
- Mayor cobertura de nubes
- **Pico de lluvias**: Septiembre - Octubre

### Precipitación

- **Distribución horaria**: Mayor probabilidad entre 2:00 PM y 7:00 PM (tormentas convectivas)
- **Lluvias nocturnas**: Posibles pero menos frecuentes (Pacífico) o más frecuentes (Caribe)
- **Costa Caribe vs Pacífico**: Caribe recibe más lluvia anual (3000-4000 mm vs 1500-2500 mm)

### Humedad Relativa

- **Costas**: 70-90% (alta todo el año)
- **Interior**: 60-85%
- **Montaña**: 75-95% (frecuentes nieblas)
- **Variación diaria**: Máxima en madrugada, mínima en horas de sol

### Viento

- **Velocidad típica**: 5-20 km/h
- **Vientos alisios**: Predominantes del noreste (NE) de diciembre a abril
- **Época lluviosa**: Vientos más variables y débiles
- **Costas**: Vientos más fuertes (hasta 40 km/h)

### Presión Atmosférica

- **Nivel del mar**: 1010-1015 hPa (promedio)
- **Ajuste por elevación**: -12 hPa por cada 100m de elevación
- **Variación diaria**: ±2-3 hPa (ciclo barométrico)
- **Sistemas meteorológicos**: Bajas presiones durante tormentas (995-1005 hPa)

---

## 🔗 Coherencia y Correlaciones Requeridas

### 1. Correlación Temperatura - Hora del Día

- **Curva sinusoidal**: Temperatura debe seguir patrón diurno natural
- **Mínimo**: 5:00-6:00 AM
- **Máximo**: 1:00-3:00 PM
- **Transición suave**: Sin cambios bruscos entre horas consecutivas (±1-3°C máximo)

### 2. Correlación Temperatura - Sensación Térmica

```
feels_like = temperatura + factor_humedad + factor_viento

- Alta humedad (>80%): feels_like = temp + 1 a 3°C
- Viento fuerte (>20 km/h): feels_like = temp - 1 a 3°C
- Condiciones normales: feels_like ≈ temperatura ± 1°C
```

### 3. Correlación Precipitación - Otros Parámetros

Cuando hay precipitación:
- **Humedad**: Aumenta a 85-100%
- **Temperatura**: Disminuye 2-5°C durante la lluvia
- **Presión**: Disminuye ligeramente (1-3 hPa)
- **Cloud cover**: 80-100%
- **Viento**: Puede aumentar (tormentas) o disminuir (lloviznas)

### 4. Correlación Elevación - Temperatura

- **Gradiente térmico**: -0.6°C por cada 100m de elevación
- **Estaciones en montaña** (>1000m): Temperaturas consistentemente más bajas

### 5. Correlación Nubosidad - Precipitación

- **Sin lluvia**: cloud_cover puede ser 0-100%
- **Con lluvia**: cloud_cover debe ser mínimo 60%, típicamente 80-100%
- **Lluvia intensa**: cloud_cover = 90-100%

### 6. Estacionalidad Regional

#### Costa Pacífico (Herrera, Los Santos, Panamá Oeste)
- Temporada seca muy marcada
- Menor precipitación anual

#### Costa Caribe (Bocas del Toro, Colón, Guna Yala)
- Lluvia más distribuida en el año
- Mayor precipitación anual
- Menos diferencia entre estaciones

#### Interior montañoso (Chiriquí alturas, Coclé alturas)
- Temperaturas más bajas
- Nieblas frecuentes (alta humedad)
- Microclimas específicos

---

## 🏢 Regiones de Panamá (12 regiones)

El dataset debe cubrir todas las estaciones en las siguientes regiones:

1. **BOCAS DEL TORO** - Costa Caribe, alta precipitación
2. **CHIRIQUI** - Montañas altas (Volcán Barú 3,475m), clima variado
3. **COCLE** - Pacífico central, montañas medias
4. **COLON** - Costa Caribe, alta precipitación
5. **DARIEN** - Selva tropical, alta humedad
6. **GNABE BUGLE** - Comarca montañosa, tierras altas
7. **GUNA YALA** - Archipiélago caribeño, clima marino
8. **HERRERA** - Pacífico seco, arco seco de Panamá
9. **LOS SANTOS** - Pacífico más seco, temporada seca marcada
10. **PANAMA** - Ciudad capital, área metropolitana
11. **PANAMA OESTE** - Pacífico central
12. **VERAGUAS** - Dos costas (Pacífico y Caribe), clima diverso

---

## 🧪 Validaciones Requeridas

### 1. Validaciones de Integridad

- [ ] No debe haber duplicados de `(station_id, date, hour)`
- [ ] Todas las 253 estaciones deben tener exactamente 43,800 registros (5 años × 365.25 días × 24 horas)
- [ ] Todas las fechas deben estar en el rango especificado
- [ ] Todas las horas deben estar en rango 0-23

### 2. Validaciones de Rangos

- [ ] `temperature`: 8-40°C (extremos raros fuera de este rango)
- [ ] `humidity`: 40-100%
- [ ] `wind_speed`: 0-100 km/h (>60 km/h solo en tormentas)
- [ ] `precipitation_total`: 0-150 mm/hora (>50 mm/hora son eventos extremos)
- [ ] `pressure`: Ajustado por elevación, coherente con nivel del mar
- [ ] `cloud_cover`: 0-100%

### 3. Validaciones de Coherencia

- [ ] Temperatura debe seguir patrón diurno (curva sinusoidal)
- [ ] No debe haber cambios bruscos entre horas consecutivas (>5°C)
- [ ] Precipitación debe correlacionar con humedad alta y cloud_cover alto
- [ ] Sensación térmica debe ser coherente con temperatura, humedad y viento
- [ ] Presión atmosférica debe ajustarse por elevación de la estación

### 4. Validaciones Temporales

- [ ] Estacionalidad debe ser coherente (seca vs lluviosa)
- [ ] Años bisiestos deben tener 366 días
- [ ] Timestamps deben ser válidos ISO 8601

---

## 📦 Formato de Salida

### Opción 1: Inserción Directa a Base de Datos

```python
# Usar función existente del sistema
from core.database.raindrop_db import insert_or_update_weather_data

# Insertar datos por lotes (batch de 1000-5000 registros)
```

### Opción 2: Archivo CSV

Si se prefiere generar CSV para revisión antes de insertar:

```csv
station_id,station_name,region,latitude,longitude,elevation,date,hour,timestamp,temperature,feels_like,humidity,wind_speed,wind_direction,wind_angle,precipitation_total,precipitation_type,pressure,cloud_cover,summary,icon
```

---

## 🛠️ Tecnologías Sugeridas

### Librerías Python Recomendadas

```python
import numpy as np              # Generación de datos con distribuciones
import pandas as pd             # Manipulación de datos
from datetime import datetime, timedelta
import sqlite3                  # Conexión a base de datos
from scipy.interpolate import interp1d  # Suavizado de curvas
```

### Estrategias de Generación

1. **Uso de distribuciones estadísticas**:
   - `np.random.normal()` para temperatura (distribución gaussiana)
   - `np.random.gamma()` para precipitación (sesgada hacia valores bajos)
   - `np.random.beta()` para humedad (concentrada en valores altos)

2. **Generación de series temporales**:
   - Curvas sinusoidales para temperatura diurna
   - Ruido browniano para variabilidad natural
   - Autocorrelación para suavidad temporal

3. **Modelos basados en físicas**:
   - Ecuación hipsométrica para presión por altitud
   - Índice de sensación térmica (heat index/wind chill)
   - Conservación de masa de agua (precipitación-evaporación)

---

## 📝 Entregables Esperados

1. **Script Python** (`generate_training_dataset.py`):
   - Generación completa de 11.1M registros
   - Tiempo de ejecución estimado: 10-30 minutos
   - Logging de progreso
   - Manejo de errores

2. **Documentación**:
   - README con instrucciones de uso
   - Explicación de algoritmos y parámetros usados
   - Ejemplos de validación

3. **Validación**:
   - Script de validación de calidad de datos
   - Estadísticas descriptivas del dataset generado
   - Visualizaciones de muestra (gráficas de temperatura, precipitación por región)

---

## 🎯 Criterios de Éxito

- ✅ Dataset completo con 11,102,400 registros (o 11,145,600 considerando bisiestos)
- ✅ Datos pasan todas las validaciones de integridad y coherencia
- ✅ Distribuciones estadísticas son realistas para clima panameño
- ✅ Estacionalidad es claramente observable en los datos
- ✅ Diferencias regionales son evidentes (Caribe vs Pacífico, costa vs montaña)
- ✅ No hay valores nulos o fuera de rango
- ✅ El modelo ML puede entrenarse exitosamente con estos datos

---

## 📚 Referencias Útiles

### Datos Climáticos de Panamá

- **ETESA** (Empresa de Transmisión Eléctrica S.A.): Autoridad meteorológica de Panamá
- **Promedios climáticos**: [Climate-Data.org - Panamá](https://es.climate-data.org/america-del-norte/panama-15/)
- **Atlas climático**: Promedios históricos por región

### Información Geográfica

- Tabla `stations` en la base de datos contiene 253 estaciones con:
  - Coordenadas (latitud, longitud)
  - Elevación
  - Región administrativa

### Validación de Coherencia

- Los datos generados deben ser comparables con patrones de `weather_hourly` existentes (si los hay)
- Distribuciones deben seguir patrones gaussianos o gamma según la variable

---

## 🚀 Próximos Pasos

1. **Fase 1**: Diseño del algoritmo de generación
2. **Fase 2**: Implementación del script con validaciones
3. **Fase 3**: Generación del dataset completo
4. **Fase 4**: Validación estadística y visual
5. **Fase 5**: Inserción en base de datos de producción
6. **Fase 6**: Entrenamiento del modelo ML con datos reales

---

## 💡 Notas Adicionales

- **Performance**: Considerar inserción por lotes (batch inserts) para optimizar velocidad
- **Reproducibilidad**: Usar semilla fija (`np.random.seed()`) para poder regenerar dataset idéntico
- **Escalabilidad**: El script debe poder generar datos para períodos adicionales en el futuro
- **Calidad > Cantidad**: Es preferible un dataset más pequeño pero altamente coherente que uno grande con inconsistencias

---

**Documento creado**: 16 de diciembre de 2025  
**Versión**: 1.0  
**Proyecto**: Sistema de Predicción de Riesgos Climáticos - Panamá
