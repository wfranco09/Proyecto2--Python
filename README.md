Sistema de Monitoreo Ambiental — Instalación

Repositorio con pipelines para ingerir y procesar datos climáticos (IMHPA, ETESA), enriquecimiento geoespacial y utilidades relacionadas.

# Sistema de Monitoreo Ambiental — Instalación

> Repositorio con pipelines para ingerir y procesar datos climáticos (IMHPA, ETESA), enriquecimiento geoespacial y utilidades relacionadas.

## Instalación (pip / venv)

1. Crear y activar el virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias runtime:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. (Opcional) Instalar dependencias de desarrollo / notebooks:

```bash
python -m pip install -r requirements-dev.txt
```

> Nota: si usas `conda`, puedes crear un entorno desde `conda-forge` y evitar problemas con compilación de librerías geoespaciales.

## Variables de entorno
Puedes colocar variables en un fichero `.env` en la raíz. Ejemplos útiles:


## Ejecutar tests

Desde la raíz del repo (con `.venv` activado):

```bash
PYTHONPATH=. pytest -q
```

Si tus imports fallan por `ModuleNotFoundError: pipelines`, asegúrate de ejecutar con `PYTHONPATH=.`, o lanzar el runner con `python -m pipelines.pipeline_runner`.

## Ejecutar los pipelines

Menú interactivo (recomendado para desarrollo):

```bash
python -m pipelines.pipeline_runner
```

Ejecutar todo programáticamente:

```bash
python -c "import pipelines.pipeline_runner as pr; pr.run_all_pipelines()"
```

Ejecutar un pipeline concreto (ejemplo IMHPA realtime):

```bash
python -m pipelines.imhpa.realtime_temp
```

## Estructura de datos en disco

Los módulos que escriben datos se encargan de crear sus carpetas con `os.makedirs(..., exist_ok=True)`. Además, el `pipeline_runner` crea las carpetas base al iniciar la ejecución completa.

## Notas sobre problemas comunes

## Contribuir


Si quieres, puedo añadir una sección de `environment.yml` (conda) o un README en inglés.

Sistema de Monitoreo Ambiental — Instalación

Este repositorio contiene pipelines para ingerir y procesar datos climáticos (IMHPA, ETESA), enriquecimiento geoespacial y utilidades relacionadas.

## Requisitos previos
- macOS / Linux / Windows con Python 3.10+ (se probó con 3.11/3.12).
- Recomiendo usar un entorno virtual (`venv`) o `conda`/`mamba` para aislar dependencias.
- Dependencias nativas para `geopandas` / `osmnx`: GDAL, Fiona, PROJ, GEOS. En macOS puedes instalarlas con `brew` o usar conda-forge para evitar compilaciones.

Ejemplos (macOS):

```bash
# brew (si no usas conda)
brew install gdal proj

# o conda (recomendado para reproducibilidad geoespacial)
conda create -n sm_env python=3.11 -y
conda activate sm_env
conda install -c conda-forge geopandas osmnx jupyterlab -y
```

## Instalación (pip / venv)

1. Crear y activar el virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias runtime:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. (Opcional) Instalar dependencias de desarrollo / notebooks:

```bash
python -m pip install -r requirements-dev.txt
```

Nota: si usas `conda`, puedes omitir el paso `brew` y crear un `environment.yml` a partir de `requirements.txt` si lo deseas.

## Variables de entorno
Puedes colocar variables en un fichero `.env` en la raíz. Ejemplos útiles:

- `DATA_RAW_PATH` — ruta raíz para datos crudos (por defecto `data_raw`)
- `IMHPA_MAX_WORKERS` — número de hilos para procesar estaciones IMHPA (por defecto `8`)
- `TERRAIN_MAX_WORKERS` — hilos para enriquecimiento de terreno
- `OSM_TILE_KM` y `OSM_MAX_WORKERS` — controlan el tiling y concurrencia en descargas OSM

## Ejecutar tests

Desde la raíz del repo (con `.venv` activado):

```bash
PYTHONPATH=. pytest -q
```

Si tus imports fallan por `ModuleNotFoundError: pipelines`, asegúrate de ejecutar con `PYTHONPATH=.` o de lanzar el runner con `python -m pipelines.pipeline_runner`.

## Ejecutar los pipelines

Menú interactivo (recomendado para desarrollo):

```bash
python -m pipelines.pipeline_runner
```

Ejecutar todo programáticamente:

```bash
python -c "import pipelines.pipeline_runner as pr; pr.run_all_pipelines()"
```

Algunos pipelines individuales también se pueden ejecutar directamente (por ejemplo IMHPA realtime):

```bash
python -m pipelines.imhpa.realtime_temp
```

## Estructura de datos en disco
- `data_raw/` — datos crudos y caches (ej.: `data_raw/imhpa`, `data_raw/etesa`, `data_raw/osm`)
- `data_clean/` — salidas limpias y datasets intermedios (ej.: `data_clean/imhpa`, `data_clean/master`)

Los módulos que escriben datos se encargan de crear sus carpetas con `os.makedirs(..., exist_ok=True)`. Además, el `pipeline_runner` crea las carpetas base al iniciar la ejecución completa.

## Notas sobre problemas comunes
- Geopandas/osmnx: si la instalación falla por dependencias nativas, usa conda-forge o instala `gdal`/`proj` vía `brew`.
- Overpass / OSM: el downloader tiene mecanimos de cache en `data_raw/osm` y descarga por tiles para evitar consultas demasiado grandes.
- Si tienes problemas con permisos al crear carpetas, revisa permisos del directorio de trabajo o ejecuta con un usuario con permisos adecuados.

## Contribuir
- Abrir issues para bugs o mejoras.
- Para cambios grandes, crear una rama y enviar un pull request.

---
 