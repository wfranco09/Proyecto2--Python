"""
Script para hacer scraping de estaciones meteorológicas desde IMHPA
URL: https://www.imhpa.gob.pa/es/estaciones-meteorologicas
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def dms_to_decimal(dms_str: str) -> Optional[float]:
    """
    Convierte coordenadas de DMS (grados° minutos' segundos") a decimal.
    
    Ejemplos:
        "8° 57' 38"" -> 8.9605556
        "82° 25' 28"" -> 82.4244444
    
    Args:
        dms_str: String con formato DMS
        
    Returns:
        Coordenada en formato decimal
    """
    if not dms_str or dms_str.strip() == "":
        return None
    
    try:
        # Extraer grados, minutos, segundos
        # Formato: 8° 57' 38"
        parts = re.findall(r'(\d+)', dms_str)
        
        if len(parts) < 2:
            return None
        
        degrees = float(parts[0])
        minutes = float(parts[1]) if len(parts) > 1 else 0
        seconds = float(parts[2]) if len(parts) > 2 else 0
        
        # Convertir a decimal
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # Determinar si es negativo (Oeste/Sur)
        # En Panamá, longitudes son Oeste (negativas)
        if 'W' in dms_str.upper() or 'O' in dms_str.upper():
            decimal = -decimal
        
        return round(decimal, 6)
    except Exception as e:
        logger.warning(f"Error convirtiendo DMS '{dms_str}': {e}")
        return None


def scrape_imhpa_stations(base_url: str = "https://www.imhpa.gob.pa/es/estaciones-meteorologicas") -> List[Dict]:
    """
    Hace scraping de todas las estaciones meteorológicas de IMHPA.
    
    Args:
        base_url: URL base de la página
        
    Returns:
        Lista de estaciones con sus datos
    """
    stations = []
    page = 1
    max_pages = 20  # Límite de seguridad
    
    logger.info("Iniciando scraping de estaciones IMHPA...")
    
    while page <= max_pages:
        try:
            # Construir URL con paginación
            # Formato: /estaciones-meteorologicas para página 1
            #          /estaciones-meteorologicas/p2 para página 2, etc.
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}/p{page}"
            
            logger.info(f"Scraping página {page}: {url}")
            
            # Hacer request
            response = requests.get(url, timeout=10)
            
            # Si la página no existe (404), terminamos
            if response.status_code == 404:
                logger.info(f"Página {page} no existe (404). Finalizando scraping.")
                break
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tabla
            table = soup.find('table')
            
            if not table:
                logger.info(f"No se encontró tabla en página {page}. Finalizando scraping.")
                break
            
            # Extraer filas
            rows = table.find_all('tr')
            
            if len(rows) <= 1:  # Solo header o vacío
                logger.info(f"No hay más datos en página {page}. Finalizando scraping.")
                break
            
            found_data = False
            
            # Procesar cada fila (skip header)
            for row in rows[1:]:
                cols = row.find_all('td')
                
                if len(cols) < 7:  # Validar que tenga suficientes columnas
                    continue
                
                found_data = True
                
                # Extraer datos
                numero = cols[0].get_text(strip=True)
                nombre = cols[1].get_text(strip=True)
                provincia = cols[2].get_text(strip=True)
                tipo = cols[3].get_text(strip=True)
                elevacion_str = cols[4].get_text(strip=True)
                latitud_str = cols[5].get_text(strip=True)
                longitud_str = cols[6].get_text(strip=True)
                
                # Convertir elevación
                try:
                    elevacion = int(elevacion_str) if elevacion_str.isdigit() else 0
                except:
                    elevacion = 0
                
                # Convertir coordenadas
                lat = dms_to_decimal(latitud_str)
                lon = dms_to_decimal(longitud_str)
                
                # Longitudes en Panamá son Oeste (negativas)
                if lon and lon > 0:
                    lon = -lon
                
                # Validar coordenadas
                if not lat or not lon:
                    logger.warning(f"Coordenadas inválidas para {nombre}: lat={latitud_str}, lon={longitud_str}")
                    continue
                
                # Crear objeto estación
                station = {
                    "numero": numero,
                    "name": nombre,
                    "provincia": provincia,
                    "tipo": tipo,
                    "elevation": elevacion,
                    "lat": lat,
                    "lon": lon,
                }
                
                stations.append(station)
                logger.info(f"  ✓ {numero} - {nombre} ({provincia})")
            
            if not found_data:
                logger.info(f"No se encontraron datos válidos en página {page}. Finalizando scraping.")
                break
            
            # Siguiente página
            page += 1
                
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 404:
                logger.info(f"Página {page} no encontrada. Finalizando scraping.")
                break
            logger.error(f"Error en request a página {page}: {e}")
            break
        except Exception as e:
            logger.error(f"Error procesando página {page}: {e}")
            break
    
    logger.info(f"\n✅ Total estaciones encontradas: {len(stations)}")
    return stations


def generate_config_file(stations: List[Dict], output_file: str = "stations_config.json"):
    """
    Genera archivo de configuración con las estaciones.
    
    Args:
        stations: Lista de estaciones
        output_file: Nombre del archivo de salida
    """
    # Numerar estaciones secuencialmente
    for i, station in enumerate(stations, start=1):
        station["id"] = i
        station["region"] = station["provincia"]
    
    config = {
        "total_stations": len(stations),
        "source": "IMHPA - https://www.imhpa.gob.pa/es/estaciones-meteorologicas",
        "last_updated": "2025-12-16",
        "stations": stations
    }
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📄 Configuración guardada en: {output_file}")


def update_database(stations: List[Dict]):
    """
    Actualiza la tabla de estaciones en la base de datos.
    
    Args:
        stations: Lista de estaciones
    """
    try:
        import sqlite3
        from pathlib import Path
        from datetime import datetime, timezone
        
        # Path a la base de datos
        db_path = Path(__file__).parent.parent / "core" / "database" / "raindrop.db"
        
        if not db_path.exists():
            logger.error(f"Base de datos no encontrada: {db_path}")
            logger.info("Creando base de datos...")
            # Importar e inicializar
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from core.database.raindrop_db import init_database
            init_database()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Limpiar tabla existente
        logger.info("Limpiando tabla de estaciones...")
        cursor.execute("DELETE FROM stations")
        
        # Insertar nuevas estaciones
        now = datetime.now(timezone.utc).isoformat()
        inserted = 0
        
        for station in stations:
            try:
                cursor.execute("""
                    INSERT INTO stations (id, name, region, latitude, longitude, elevation, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    station["id"],
                    station["name"],
                    station["provincia"],
                    station["lat"],
                    station["lon"],
                    station["elevation"],
                    now,
                    now
                ))
                inserted += 1
            except Exception as e:
                logger.warning(f"Error insertando estación {station['name']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"\n✅ Base de datos actualizada con {inserted}/{len(stations)} estaciones")
        
    except Exception as e:
        logger.error(f"Error actualizando base de datos: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape estaciones meteorológicas de IMHPA")
    parser.add_argument("--url", default="https://www.imhpa.gob.pa/es/estaciones-meteorologicas",
                        help="URL de la página de estaciones")
    parser.add_argument("--output", default="stations_imhpa.json",
                        help="Archivo de salida JSON")
    parser.add_argument("--update-db", action="store_true",
                        help="Actualizar base de datos")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limitar número de estaciones (para testing)")
    
    args = parser.parse_args()
    
    # Scrape estaciones
    stations = scrape_imhpa_stations(args.url)
    
    if not stations:
        logger.error("No se encontraron estaciones")
        exit(1)
    
    # Limitar si se especificó
    if args.limit:
        stations = stations[:args.limit]
        logger.info(f"Limitando a {args.limit} estaciones")
    
    # Generar archivo de configuración
    generate_config_file(stations, args.output)
    
    # Actualizar base de datos si se solicitó
    if args.update_db:
        update_database(stations)
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Total estaciones: {len(stations)}")
    print(f"Archivo generado: {args.output}")
    
    # Agrupar por provincia
    provincias = {}
    for station in stations:
        prov = station["provincia"]
        if prov not in provincias:
            provincias[prov] = 0
        provincias[prov] += 1
    
    print("\nEstaciones por provincia:")
    for prov, count in sorted(provincias.items()):
        print(f"  {prov}: {count}")
    
    print("="*60)
