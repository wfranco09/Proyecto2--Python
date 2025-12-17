"""
Script para actualizar la configuración de estaciones desde el JSON de IMHPA
"""

import json
import sys
from pathlib import Path

def update_config_from_json(json_file: str = "scripts/stations_imhpa.json", 
                            config_file: str = "config.py"):
    """
    Actualiza config.py con las estaciones del JSON.
    
    Args:
        json_file: Archivo JSON con estaciones
        config_file: Archivo config.py a actualizar
    """
    # Leer JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stations = data['stations']
    
    print(f"Cargadas {len(stations)} estaciones desde {json_file}")
    
    # Generar código Python para STATIONS
    stations_code = "STATIONS = [\n"
    
    for station in stations:
        stations_code += "    {\n"
        stations_code += f'        "id": {station["id"]},\n'
        stations_code += f'        "name": "{station["name"]}",\n'
        stations_code += f'        "region": "{station["provincia"]}",\n'
        stations_code += f'        "lat": {station["lat"]},\n'
        stations_code += f'        "lon": {station["lon"]},\n'
        stations_code += f'        "elevation": {station["elevation"]},\n'
        stations_code += f'        "numero": "{station["numero"]}",\n'
        stations_code += f'        "tipo": "{station["tipo"]}"\n'
        stations_code += "    },\n"
    
    stations_code += "]\n"
    
    # Leer config.py actual
    with open(config_file, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # Buscar y reemplazar STATIONS
    import re
    
    # Pattern para encontrar STATIONS = [...]
    pattern = r'STATIONS\s*=\s*\[.*?\]'
    
    if re.search(pattern, config_content, re.DOTALL):
        # Reemplazar
        new_content = re.sub(pattern, stations_code.strip(), config_content, flags=re.DOTALL)
        
        # Guardar backup
        backup_file = config_file + '.backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ Backup guardado en: {backup_file}")
        
        # Guardar nuevo config
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Config actualizado: {config_file}")
        print(f"   Total estaciones: {len(stations)}")
        
        # Mostrar resumen por provincia
        provincias = {}
        for station in stations:
            prov = station["provincia"]
            if prov not in provincias:
                provincias[prov] = 0
            provincias[prov] += 1
        
        print("\nEstaciones por provincia:")
        for prov, count in sorted(provincias.items()):
            print(f"  {prov}: {count}")
    else:
        print("❌ No se encontró la variable STATIONS en config.py")
        print("\nAgrega manualmente:")
        print(stations_code)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Actualizar config.py con estaciones de IMHPA")
    parser.add_argument("--json", default="scripts/stations_imhpa.json",
                        help="Archivo JSON con estaciones")
    parser.add_argument("--config", default="config.py",
                        help="Archivo config.py a actualizar")
    
    args = parser.parse_args()
    
    # Verificar que existen los archivos
    if not Path(args.json).exists():
        print(f"❌ No se encontró: {args.json}")
        print("Ejecuta primero: python scripts/scrape_stations.py")
        sys.exit(1)
    
    if not Path(args.config).exists():
        print(f"❌ No se encontró: {args.config}")
        sys.exit(1)
    
    update_config_from_json(args.json, args.config)
