# Scripts de Actualización de Estaciones

Scripts para actualizar la configuración de estaciones meteorológicas desde IMHPA.

## Scripts Disponibles

### 1. `scrape_stations.py`

Hace scraping de la página web de IMHPA para obtener todas las estaciones meteorológicas.

**Características:**
- Extrae datos de https://www.imhpa.gob.pa/es/estaciones-meteorologicas
- Maneja paginación automáticamente
- Convierte coordenadas DMS (grados°minutos'segundos") a decimal
- Genera archivo JSON con todas las estaciones

**Uso:**

```bash
# Scraping básico (genera stations_imhpa.json)
python scripts/scrape_stations.py

# Especificar archivo de salida
python scripts/scrape_stations.py --output mi_archivo.json

# Actualizar base de datos directamente
python scripts/scrape_stations.py --update-db

# Limitar número de estaciones (para testing)
python scripts/scrape_stations.py --limit 10
```

**Campos extraídos:**
- `numero`: Código de la estación (ej: "91-026")
- `name`: Nombre de la estación
- `provincia`: Provincia donde se ubica
- `tipo`: Tipo de estación (AM, CA, CC, etc.)
- `elevation`: Elevación en metros
- `lat`: Latitud en formato decimal
- `lon`: Longitud en formato decimal (negativa para Oeste)

### 2. `update_config.py`

Actualiza el archivo `config.py` con las estaciones obtenidas del scraping.

**Características:**
- Lee el JSON generado por `scrape_stations.py`
- Actualiza la variable `STATIONS` en `config.py`
- Crea backup automático del config anterior
- Mantiene formato y estructura del código

**Uso:**

```bash
# Actualizar config.py con el JSON por defecto
python scripts/update_config.py

# Especificar archivos manualmente
python scripts/update_config.py --json mi_archivo.json --config config.py
```

## Flujo de Trabajo Completo

### Paso 1: Hacer Scraping

```bash
cd backend
python scripts/scrape_stations.py --output scripts/stations_imhpa.json
```

Esto genera `scripts/stations_imhpa.json` con todas las estaciones encontradas.

### Paso 2: Actualizar Configuración

```bash
python scripts/update_config.py
```

Esto actualiza `config.py` con las nuevas estaciones y crea `config.py.backup`.

### Paso 3: Reiniciar Backend

```bash
# El backend detectará automáticamente las nuevas estaciones
# al reiniciar
```

### Paso 4 (Opcional): Actualizar Base de Datos

Si quieres poblar la tabla `stations` en la BD:

```bash
python scripts/scrape_stations.py --update-db
```

## Formato de Coordenadas

El script convierte automáticamente coordenadas de DMS a decimal:

**Entrada (DMS):**
```
Latitud: 8° 57' 38"
Longitud: 82° 25' 28"
```

**Salida (Decimal):**
```
lat: 8.960556
lon: -82.424444  # Negativo para Oeste
```

## Estructura del JSON Generado

```json
{
  "total_stations": 25,
  "source": "IMHPA - https://www.imhpa.gob.pa/es/estaciones-meteorologicas",
  "last_updated": "2025-12-16",
  "stations": [
    {
      "numero": "91-026",
      "name": "CHANGUINOLA SUR",
      "provincia": "BOCAS DEL TORO",
      "tipo": "AM",
      "elevation": 400,
      "lat": 8.960556,
      "lon": -82.424444,
      "id": 1,
      "region": "BOCAS DEL TORO"
    },
    ...
  ]
}
```

## Notas Importantes

### Coordenadas en Panamá
- **Latitud:** Positiva (Norte del Ecuador)
- **Longitud:** Negativa (Oeste del Meridiano de Greenwich)

### Tipos de Estación
- **AM**: Agrometeorológica
- **CA**: Climatológica Automática  
- **CC**: Climatológica Convencional
- **CM**: Climatológica Manual
- **BA**: ?
- **AA**: ?

### Backup Automático
El script `update_config.py` crea automáticamente un backup del config.py anterior como `config.py.backup` antes de hacer cambios.

### Actualización Periódica
Se recomienda ejecutar estos scripts periódicamente para mantener actualizada la lista de estaciones, ya que IMHPA puede agregar o modificar estaciones.

## Dependencias

```bash
pip install beautifulsoup4 requests
```

## Troubleshooting

### Error: "No se encontró tabla"
La estructura HTML de la página cambió. Verifica la URL y actualiza los selectores en `scrape_stations.py`.

### Error: "Coordenadas inválidas"
Algunas estaciones pueden tener coordenadas mal formateadas. El script las omite y muestra un warning.

### Error: "No se encontró STATIONS en config.py"
El patrón regex no encontró la variable. Asegúrate de que `config.py` tenga la variable `STATIONS = [...]` definida.

## Ejemplos de Uso

### Solo quiero ver qué estaciones hay (sin guardar)
```bash
python scripts/scrape_stations.py --output /tmp/test.json
cat /tmp/test.json | python -m json.tool | grep '"name"'
```

### Actualizar todo en un solo comando
```bash
python scripts/scrape_stations.py && python scripts/update_config.py
```

### Ver resumen por provincia
```bash
python scripts/scrape_stations.py 2>&1 | grep -A 20 "Estaciones por provincia"
```
