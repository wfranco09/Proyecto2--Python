"""
Configuration for rAIndrop Backend
"""

from pathlib import Path
from typing import List

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = Path(__file__).parent.parent

# Data paths
DATA_RAW_PATH = BACKEND_DIR / "core" / "data" / "data_raw"
DATA_CLEAN_PATH = BACKEND_DIR / "core" / "data" / "data_clean"
DATA_CACHE_PATH = BACKEND_DIR / "core" / "data" / "data_cache"
MODELS_PATH = BACKEND_DIR / "core" / "ml" / "models"

# Crear directorios si no existen
DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_CLEAN_PATH.mkdir(parents=True, exist_ok=True)
DATA_CACHE_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)

# Model file names
MODEL_FLOOD = "rf_flood.joblib"
MODEL_DROUGHT = "rf_drought.joblib"
MODEL_METADATA = "model_metadata.json"
FEATURE_IMPORTANCES = "feature_importances.json"

# Data file names
MASTER_DATASET = "master_dataset_final.csv"
STATION_RISK_CACHE = "station_risk_cache.json"
PREDICTIONS_CACHE = "predictions_cache.json"
LATEST_IMHPA = "latest_imhpa_data.csv"

# Scheduler configuration
SCHEDULER_INTERVAL_HOURS = 1
RETRAIN_INTERVAL_DAYS = 1
RETRAIN_TIME = "00:00"  # Midnight UTC

# Model parameters
TRAIN_TEST_SPLIT = 0.2
RANDOM_STATE = 42
N_ESTIMATORS = 200
MAX_DEPTH = None
MIN_SAMPLES_SPLIT = 2

# Risk thresholds
FLOOD_THRESHOLD_LOW = 0.3        # 30%
FLOOD_THRESHOLD_HIGH = 0.8       # 80%
DROUGHT_THRESHOLD_LOW = 0.3      # 30%
DROUGHT_THRESHOLD_HIGH = 0.8     # 80%

# Risk level categories
RISK_LEVELS = {
    "GREEN": (0.0, 0.3),      # Low risk
    "YELLOW": (0.3, 0.8),     # Medium risk
    "RED": (0.8, 1.0),        # High risk
}

# Feature columns
FEATURE_COLUMNS = ["TEMP", "HUMEDAD", "LLUVIA", "VIENTO", "elevation_m"]
LABEL_COLUMNS = {
    "flood": "flood_label",
    "drought": "drought_label",
}

# Información de estaciones (+250 estaciones en Panamá)
STATIONS = [
    {
        "id": 1,
        "name": "CHANGUINOLA SUR",
        "region": "BOCAS DEL TORO",
        "lat": 8.960556,
        "lon": -82.424444,
        "elevation": 400,
        "numero": "91-026",
        "tipo": "AM"
    },
    {
        "id": 2,
        "name": "CHANGUINOLA SIERRA",
        "region": "BOCAS DEL TORO",
        "lat": 8.853333,
        "lon": -82.406667,
        "elevation": 1220,
        "numero": "91-027",
        "tipo": "CA"
    },
    {
        "id": 3,
        "name": "CHANGUINOLA 2",
        "region": "BOCAS DEL TORO",
        "lat": 8.930278,
        "lon": -82.689722,
        "elevation": 1800,
        "numero": "91-029",
        "tipo": "CA"
    },
    {
        "id": 4,
        "name": "EL SILENCIO",
        "region": "BOCAS DEL TORO",
        "lat": 9.349722,
        "lon": -82.549722,
        "elevation": 20,
        "numero": "91-030",
        "tipo": "CC"
    },
    {
        "id": 5,
        "name": "CHANGUINOLA ARRIBA",
        "region": "BOCAS DEL TORO",
        "lat": 9.121667,
        "lon": -82.502222,
        "elevation": 152,
        "numero": "91-032",
        "tipo": "AA"
    },
    {
        "id": 6,
        "name": "SE CHANGUINOLA",
        "region": "BOCAS DEL TORO",
        "lat": 9.406667,
        "lon": -82.563889,
        "elevation": 22,
        "numero": "91-033",
        "tipo": "AA"
    },
    {
        "id": 7,
        "name": "AEROPUERTO DE BOCAS",
        "region": "BOCAS DEL TORO",
        "lat": 9.340278,
        "lon": -82.245,
        "elevation": 2,
        "numero": "93-002",
        "tipo": "AM"
    },
    {
        "id": 8,
        "name": "MIRAMAR",
        "region": "BOCAS DEL TORO",
        "lat": 9.001667,
        "lon": -82.259167,
        "elevation": 23,
        "numero": "93-007",
        "tipo": "BA"
    },
    {
        "id": 9,
        "name": "CHIRIQUI GRANDE 2",
        "region": "BOCAS DEL TORO",
        "lat": 8.949167,
        "lon": -82.116667,
        "elevation": 48,
        "numero": "93-008",
        "tipo": "AA"
    },
    {
        "id": 10,
        "name": "CANQUINTU",
        "region": "BOCAS DEL TORO",
        "lat": 8.853333,
        "lon": -81.816389,
        "elevation": 69,
        "numero": "95-001",
        "tipo": "CA"
    },
    {
        "id": 11,
        "name": "CUSAPIN",
        "region": "BOCAS DEL TORO",
        "lat": 9.178333,
        "lon": -81.889167,
        "elevation": 2,
        "numero": "95-002",
        "tipo": "CM"
    },
    {
        "id": 12,
        "name": "SANTA CATALINA",
        "region": "BOCAS DEL TORO",
        "lat": 8.781667,
        "lon": -81.339444,
        "elevation": 2,
        "numero": "95-003",
        "tipo": "CM"
    },
    {
        "id": 13,
        "name": "GUABAL",
        "region": "VERAGUAS",
        "lat": 8.5775,
        "lon": -81.203056,
        "elevation": 100,
        "numero": "97-003",
        "tipo": "CM"
    },
    {
        "id": 14,
        "name": "RIO LUIS",
        "region": "VERAGUAS",
        "lat": 8.683056,
        "lon": -81.219167,
        "elevation": 100,
        "numero": "97-004",
        "tipo": "CM"
    },
    {
        "id": 15,
        "name": "SE PROGRESO",
        "region": "CHIRIQUI",
        "lat": 8.439167,
        "lon": -82.818056,
        "elevation": 10,
        "numero": "100-037",
        "tipo": "AA"
    },
    {
        "id": 16,
        "name": "LIMONES 2",
        "region": "CHIRIQUI",
        "lat": 8.104444,
        "lon": -82.868056,
        "elevation": 58,
        "numero": "100-138",
        "tipo": "AA"
    },
    {
        "id": 17,
        "name": "LA ESPERANZA",
        "region": "CHIRIQUI",
        "lat": 8.404444,
        "lon": -82.79,
        "elevation": 18,
        "numero": "100-139",
        "tipo": "AA"
    },
    {
        "id": 18,
        "name": "CERRO PUNTA",
        "region": "CHIRIQUI",
        "lat": 8.866667,
        "lon": -82.583056,
        "elevation": 1830,
        "numero": "102-001",
        "tipo": "CC"
    },
    {
        "id": 19,
        "name": "BAJO GRANDE",
        "region": "CHIRIQUI",
        "lat": 8.849722,
        "lon": -82.549722,
        "elevation": 2300,
        "numero": "102-009",
        "tipo": "BC"
    },
    {
        "id": 20,
        "name": "CAÑAS GORDAS",
        "region": "CHIRIQUI",
        "lat": 8.75,
        "lon": -82.910833,
        "elevation": 1158,
        "numero": "102-014",
        "tipo": "CA"
    },
    {
        "id": 21,
        "name": "BRENON",
        "region": "CHIRIQUI",
        "lat": 8.635278,
        "lon": -82.828889,
        "elevation": 700,
        "numero": "102-015",
        "tipo": "CC"
    },
    {
        "id": 22,
        "name": "GOMEZ ARRIBA",
        "region": "CHIRIQUI",
        "lat": 8.566667,
        "lon": -82.733056,
        "elevation": 380,
        "numero": "102-016",
        "tipo": "CC"
    },
    {
        "id": 23,
        "name": "SANTA CRUZ",
        "region": "CHIRIQUI",
        "lat": 8.65,
        "lon": -82.766667,
        "elevation": 670,
        "numero": "102-017",
        "tipo": "CM"
    },
    {
        "id": 24,
        "name": "COTITO",
        "region": "CHIRIQUI",
        "lat": 8.878056,
        "lon": -82.705556,
        "elevation": 1900,
        "numero": "102-019",
        "tipo": "CA"
    },
    {
        "id": 25,
        "name": "PIEDRA CANDELA",
        "region": "CHIRIQUI",
        "lat": 8.876389,
        "lon": -82.775833,
        "elevation": 1440,
        "numero": "102-020",
        "tipo": "CC"
    },
    {
        "id": 26,
        "name": "CHIRIQUI VIEJO VOLCAN",
        "region": "CHIRIQUI",
        "lat": 8.8125,
        "lon": -82.628056,
        "elevation": 1537,
        "numero": "102-035",
        "tipo": "CA"
    },
    {
        "id": 27,
        "name": "CERRO PUNTA 2",
        "region": "CHIRIQUI",
        "lat": 8.857222,
        "lon": -82.587778,
        "elevation": 1874,
        "numero": "102-040",
        "tipo": "CA"
    },
    {
        "id": 28,
        "name": "PIEDRA CANDELA 2",
        "region": "CHIRIQUI",
        "lat": 8.874444,
        "lon": -82.778333,
        "elevation": 1338,
        "numero": "102-041",
        "tipo": "CA"
    },
    {
        "id": 29,
        "name": "BELEN 2",
        "region": "COLON",
        "lat": 8.883056,
        "lon": -80.869167,
        "elevation": 3,
        "numero": "103-002",
        "tipo": "CA"
    },
    {
        "id": 30,
        "name": "CUESTA DE PIEDRA",
        "region": "CHIRIQUI",
        "lat": 8.676944,
        "lon": -82.624444,
        "elevation": 1000,
        "numero": "104-001",
        "tipo": "CM"
    },
    {
        "id": 31,
        "name": "SORTOVA",
        "region": "CHIRIQUI",
        "lat": 8.546389,
        "lon": -82.651111,
        "elevation": 400,
        "numero": "104-008",
        "tipo": "CA"
    },
    {
        "id": 32,
        "name": "BOCA DE TOABRE",
        "region": "COCLE",
        "lat": 8.916667,
        "lon": -80.549722,
        "elevation": 170,
        "numero": "105-001",
        "tipo": "CM"
    },
    {
        "id": 33,
        "name": "CHIGUIRI ARRIBA",
        "region": "COCLE",
        "lat": 8.672778,
        "lon": -80.1875,
        "elevation": 180,
        "numero": "105-002",
        "tipo": "CC"
    },
    {
        "id": 34,
        "name": "COCLE DEL NORTE",
        "region": "COLON",
        "lat": 9.073056,
        "lon": -80.572778,
        "elevation": 2,
        "numero": "105-003",
        "tipo": "CM"
    },
    {
        "id": 35,
        "name": "TOABRE",
        "region": "COCLE",
        "lat": 8.640833,
        "lon": -80.349167,
        "elevation": 200,
        "numero": "105-005",
        "tipo": "BC"
    },
    {
        "id": 36,
        "name": "SAN LUCAS",
        "region": "COLON",
        "lat": 9.006667,
        "lon": -80.581667,
        "elevation": 30,
        "numero": "105-007",
        "tipo": "BC"
    },
    {
        "id": 37,
        "name": "SABANITA VERDE",
        "region": "COLON",
        "lat": 8.816389,
        "lon": -80.376667,
        "elevation": 100,
        "numero": "105-008",
        "tipo": "CM"
    },
    {
        "id": 38,
        "name": "SANTA ANA(OBRE)",
        "region": "COCLE",
        "lat": 8.816667,
        "lon": -80.266667,
        "elevation": 200,
        "numero": "105-010",
        "tipo": "CC"
    },
    {
        "id": 39,
        "name": "LOS DARIELES",
        "region": "COCLE",
        "lat": 8.816667,
        "lon": -80.266667,
        "elevation": 177,
        "numero": "105-023",
        "tipo": "AA"
    },
    {
        "id": 40,
        "name": "SAN LUCAS 2",
        "region": "COLON",
        "lat": 9.006389,
        "lon": -80.565278,
        "elevation": 90,
        "numero": "105-028",
        "tipo": "AA"
    },
    {
        "id": 41,
        "name": "TOABRE 2",
        "region": "COCLE",
        "lat": 8.640833,
        "lon": -80.349167,
        "elevation": 200,
        "numero": "105-029",
        "tipo": "AA"
    },
    {
        "id": 42,
        "name": "MACANO ARRIBA",
        "region": "CHIRIQUI",
        "lat": 8.611944,
        "lon": -82.586389,
        "elevation": 520,
        "numero": "106-004",
        "tipo": "CM"
    },
    {
        "id": 43,
        "name": "CORDILLERA ARRIBA",
        "region": "CHIRIQUI",
        "lat": 8.752222,
        "lon": -82.610278,
        "elevation": 1446,
        "numero": "106-013",
        "tipo": "AG"
    },
    {
        "id": 44,
        "name": "QUEREVALO_2",
        "region": "CHIRIQUI",
        "lat": 8.350556,
        "lon": -82.5125,
        "elevation": 18,
        "numero": "106-014",
        "tipo": "AA"
    },
    {
        "id": 45,
        "name": "FINCA LERIDA",
        "region": "CHIRIQUI",
        "lat": 8.8,
        "lon": -82.483056,
        "elevation": 1700,
        "numero": "108-001",
        "tipo": "CC"
    },
    {
        "id": 46,
        "name": "EL VALLE",
        "region": "CHIRIQUI",
        "lat": 8.426667,
        "lon": -82.337778,
        "elevation": 40,
        "numero": "108-002",
        "tipo": "CA"
    },
    {
        "id": 47,
        "name": "CALDERA(PUEBLO NUEVO)",
        "region": "CHIRIQUI",
        "lat": 8.653056,
        "lon": -82.381667,
        "elevation": 365,
        "numero": "108-004",
        "tipo": "CA"
    },
    {
        "id": 48,
        "name": "LOS PALOMOS",
        "region": "CHIRIQUI",
        "lat": 8.583056,
        "lon": -82.466667,
        "elevation": 420,
        "numero": "108-009",
        "tipo": "CC"
    },
    {
        "id": 49,
        "name": "ANGOSTURA DE COCHEA",
        "region": "CHIRIQUI",
        "lat": 8.566667,
        "lon": -82.383056,
        "elevation": 210,
        "numero": "108-013",
        "tipo": "CM"
    },
    {
        "id": 50,
        "name": "VELADERO GUALACA",
        "region": "CHIRIQUI",
        "lat": 8.430556,
        "lon": -82.286667,
        "elevation": 45,
        "numero": "108-014",
        "tipo": "CC"
    },
    {
        "id": 51,
        "name": "CERMENO",
        "region": "CHIRIQUI",
        "lat": 8.520278,
        "lon": -82.432778,
        "elevation": 170,
        "numero": "108-015",
        "tipo": "CM"
    },
    {
        "id": 52,
        "name": "LOS NARANJOS",
        "region": "CHIRIQUI",
        "lat": 8.792222,
        "lon": -82.440556,
        "elevation": 1200,
        "numero": "108-017",
        "tipo": "AG"
    },
    {
        "id": 53,
        "name": "PAJA DE SOMBRERO",
        "region": "CHIRIQUI",
        "lat": 8.685278,
        "lon": -82.320556,
        "elevation": 388,
        "numero": "108-018",
        "tipo": "BC"
    },
    {
        "id": 54,
        "name": "FORTUNA",
        "region": "CHIRIQUI",
        "lat": 8.743889,
        "lon": -82.249167,
        "elevation": 1040,
        "numero": "108-019",
        "tipo": "CC"
    },
    {
        "id": 55,
        "name": "QUEBRADA BIJAO",
        "region": "CHIRIQUI",
        "lat": 8.745278,
        "lon": -82.165556,
        "elevation": 1080,
        "numero": "108-020",
        "tipo": "CA"
    },
    {
        "id": 56,
        "name": "HORNITOS",
        "region": "CHIRIQUI",
        "lat": 8.718056,
        "lon": -82.228056,
        "elevation": 1340,
        "numero": "108-022",
        "tipo": "CA"
    },
    {
        "id": 57,
        "name": "DAVID",
        "region": "CHIRIQUI",
        "lat": 8.396667,
        "lon": -82.428056,
        "elevation": 27,
        "numero": "108-023",
        "tipo": "AC"
    },
    {
        "id": 58,
        "name": "FORTUNA (CASA CONTROL)",
        "region": "CHIRIQUI",
        "lat": 8.679167,
        "lon": -82.261667,
        "elevation": 1062,
        "numero": "108-042",
        "tipo": "CA"
    },
    {
        "id": 59,
        "name": "GUALACA II",
        "region": "CHIRIQUI",
        "lat": 8.521944,
        "lon": -82.300556,
        "elevation": 100,
        "numero": "108-043",
        "tipo": "BC"
    },
    {
        "id": 60,
        "name": "LONDRES (GUALACA)",
        "region": "CHIRIQUI",
        "lat": 8.602778,
        "lon": -82.185,
        "elevation": 511,
        "numero": "108-046",
        "tipo": "AA"
    },
    {
        "id": 61,
        "name": "BELLA VISTA 2",
        "region": "CHIRIQUI",
        "lat": 8.601667,
        "lon": -82.230556,
        "elevation": 724,
        "numero": "108-048",
        "tipo": "AA"
    },
    {
        "id": 62,
        "name": "SE GUASQUITAS",
        "region": "CHIRIQUI",
        "lat": 8.541389,
        "lon": -82.294444,
        "elevation": 132,
        "numero": "108-049",
        "tipo": "AA"
    },
    {
        "id": 63,
        "name": "BOQUETE",
        "region": "CHIRIQUI",
        "lat": 8.755,
        "lon": -82.431389,
        "elevation": 1398,
        "numero": "108-053",
        "tipo": "AA"
    },
    {
        "id": 64,
        "name": "RIO HORNITOS 2",
        "region": "CHIRIQUI",
        "lat": 8.718056,
        "lon": -82.228056,
        "elevation": 1100,
        "numero": "108-058",
        "tipo": "CA"
    },
    {
        "id": 65,
        "name": "DOLEGA (PUEBLO NUEVO)",
        "region": "CHIRIQUI",
        "lat": 8.602778,
        "lon": -82.38,
        "elevation": 275,
        "numero": "108-060",
        "tipo": "AG"
    },
    {
        "id": 66,
        "name": "LOS MOLINOS",
        "region": "CHIRIQUI",
        "lat": 8.661667,
        "lon": -82.450556,
        "elevation": 2800,
        "numero": "108-061",
        "tipo": "CA"
    },
    {
        "id": 67,
        "name": "MIGUEL DE LA BORDA",
        "region": "COLON",
        "lat": 9.153333,
        "lon": -80.299444,
        "elevation": 2,
        "numero": "109-001",
        "tipo": "CA"
    },
    {
        "id": 68,
        "name": "MANSUETO",
        "region": "COLON",
        "lat": 9.165278,
        "lon": -80.280556,
        "elevation": 14,
        "numero": "109-003",
        "tipo": "AA"
    },
    {
        "id": 69,
        "name": "CERRO BANCO",
        "region": "CHIRIQUI",
        "lat": 8.453333,
        "lon": -82.034167,
        "elevation": 340,
        "numero": "110-003",
        "tipo": "CC"
    },
    {
        "id": 70,
        "name": "SOLOY",
        "region": "CHIRIQUI",
        "lat": 8.484167,
        "lon": -82.085833,
        "elevation": 600,
        "numero": "110-008",
        "tipo": "CA"
    },
    {
        "id": 71,
        "name": "URACILLO (RIO INDIO)",
        "region": "COCLE",
        "lat": 8.966667,
        "lon": -80.176667,
        "elevation": 60,
        "numero": "111-005",
        "tipo": "CA"
    },
    {
        "id": 72,
        "name": "LOS CHORROS 2",
        "region": "PANAMA",
        "lat": 8.761944,
        "lon": -80.126944,
        "elevation": 270,
        "numero": "111-008",
        "tipo": "CA"
    },
    {
        "id": 73,
        "name": "SAN FELIX",
        "region": "CHIRIQUI",
        "lat": 8.286944,
        "lon": -81.873056,
        "elevation": 110,
        "numero": "112-003",
        "tipo": "CC"
    },
    {
        "id": 74,
        "name": "QUEBRADA LORO",
        "region": "CHIRIQUI",
        "lat": 8.366667,
        "lon": -81.9,
        "elevation": 390,
        "numero": "112-004",
        "tipo": "CC"
    },
    {
        "id": 75,
        "name": "RATON",
        "region": "CHIRIQUI",
        "lat": 8.539722,
        "lon": -81.819167,
        "elevation": 1520,
        "numero": "112-014",
        "tipo": "AM"
    },
    {
        "id": 76,
        "name": "VELADERO TOLE",
        "region": "CHIRIQUI",
        "lat": 8.244444,
        "lon": -81.665556,
        "elevation": 0,
        "numero": "112-015",
        "tipo": "AG"
    },
    {
        "id": 77,
        "name": "ICACAL",
        "region": "COLON",
        "lat": 9.204444,
        "lon": -80.145833,
        "elevation": 11,
        "numero": "113-001",
        "tipo": "BC"
    },
    {
        "id": 78,
        "name": "ICACAL 2",
        "region": "COLON",
        "lat": 9.198889,
        "lon": -80.151667,
        "elevation": 8,
        "numero": "113-008",
        "tipo": "AA"
    },
    {
        "id": 79,
        "name": "CAMARON TABASARA",
        "region": "CHIRIQUI",
        "lat": 8.0625,
        "lon": -81.650278,
        "elevation": 20,
        "numero": "114-002",
        "tipo": "CM"
    },
    {
        "id": 80,
        "name": "PENA BLANCA",
        "region": "CHIRIQUI",
        "lat": 8.469444,
        "lon": -81.688333,
        "elevation": 870,
        "numero": "114-006",
        "tipo": "CA"
    },
    {
        "id": 81,
        "name": "CERRO IGLESIA",
        "region": "CHIRIQUI",
        "lat": 8.290556,
        "lon": -81.565278,
        "elevation": 370,
        "numero": "114-007",
        "tipo": "CC"
    },
    {
        "id": 82,
        "name": "OJO DE AGUA",
        "region": "VERAGUAS",
        "lat": 8.199167,
        "lon": -81.521944,
        "elevation": 358,
        "numero": "114-010",
        "tipo": "AM"
    },
    {
        "id": 83,
        "name": "LLANO TUGRI",
        "region": "GNABE BUGLE",
        "lat": 8.480833,
        "lon": -81.717222,
        "elevation": 1225,
        "numero": "114-013",
        "tipo": "AG"
    },
    {
        "id": 84,
        "name": "AGUA CLARA",
        "region": "COLON",
        "lat": 9.364167,
        "lon": -79.705833,
        "elevation": 460,
        "numero": "115-001",
        "tipo": "CA"
    },
    {
        "id": 85,
        "name": "BARRO COLORADO",
        "region": "PANAMA",
        "lat": 9.165278,
        "lon": -79.836389,
        "elevation": 34,
        "numero": "115-002",
        "tipo": "CA"
    },
    {
        "id": 86,
        "name": "CANDELARIA",
        "region": "PANAMA",
        "lat": 9.382778,
        "lon": -79.516389,
        "elevation": 98,
        "numero": "115-003",
        "tipo": "CA"
    },
    {
        "id": 87,
        "name": "CHICO",
        "region": "PANAMA",
        "lat": 9.263333,
        "lon": -79.509444,
        "elevation": 104,
        "numero": "115-004",
        "tipo": "CA"
    },
    {
        "id": 88,
        "name": "CIENTO",
        "region": "COLON",
        "lat": 9.297778,
        "lon": -79.728056,
        "elevation": 38,
        "numero": "115-005",
        "tipo": "CA"
    },
    {
        "id": 89,
        "name": "EL CHORRO",
        "region": "PANAMA",
        "lat": 8.975556,
        "lon": -79.990278,
        "elevation": 43,
        "numero": "115-007",
        "tipo": "CA"
    },
    {
        "id": 90,
        "name": "ESCANDALOSA",
        "region": "COLON",
        "lat": 9.423333,
        "lon": -79.578056,
        "elevation": 480,
        "numero": "115-008",
        "tipo": "CA"
    },
    {
        "id": 91,
        "name": "GAMBOA",
        "region": "COLON",
        "lat": 9.111944,
        "lon": -79.693889,
        "elevation": 31,
        "numero": "115-010",
        "tipo": "AA"
    },
    {
        "id": 92,
        "name": "GATUN RAIN Z.C.",
        "region": "COLON",
        "lat": 9.268056,
        "lon": -79.920556,
        "elevation": 31,
        "numero": "115-011",
        "tipo": "AA"
    },
    {
        "id": 93,
        "name": "LAS RAICES",
        "region": "COLON",
        "lat": 9.091667,
        "lon": -79.987778,
        "elevation": 34,
        "numero": "115-014",
        "tipo": "CA"
    },
    {
        "id": 94,
        "name": "MONTELIRIO",
        "region": "PANAMA",
        "lat": 9.240833,
        "lon": -79.853056,
        "elevation": 34,
        "numero": "115-016",
        "tipo": "CA"
    },
    {
        "id": 95,
        "name": "PELUCA",
        "region": "PANAMA",
        "lat": 9.38,
        "lon": -79.560833,
        "elevation": 107,
        "numero": "115-017",
        "tipo": "CA"
    },
    {
        "id": 96,
        "name": "SALAMANCA",
        "region": "COLON",
        "lat": 9.304167,
        "lon": -79.583056,
        "elevation": 79,
        "numero": "115-018",
        "tipo": "CA"
    },
    {
        "id": 97,
        "name": "SAN MIGUEL",
        "region": "PANAMA",
        "lat": 9.419722,
        "lon": -79.504167,
        "elevation": 520,
        "numero": "115-019",
        "tipo": "CA"
    },
    {
        "id": 98,
        "name": "CANO(LAGO GATUN)",
        "region": "COLON",
        "lat": 9.076389,
        "lon": -79.822778,
        "elevation": 33,
        "numero": "115-024",
        "tipo": "CA"
    },
    {
        "id": 99,
        "name": "LA HUMEDAD",
        "region": "COLON",
        "lat": 9.048056,
        "lon": -80.039167,
        "elevation": 30,
        "numero": "115-025",
        "tipo": "AA"
    },
    {
        "id": 100,
        "name": "LAGO ALAJUELA",
        "region": "PANAMA",
        "lat": 9.206389,
        "lon": -79.620556,
        "elevation": 40,
        "numero": "115-026",
        "tipo": "CA"
    },
    {
        "id": 101,
        "name": "EMPIRE",
        "region": "PANAMA",
        "lat": 9.058056,
        "lon": -79.681389,
        "elevation": 61,
        "numero": "115-044",
        "tipo": "CA"
    },
    {
        "id": 102,
        "name": "LOS CANONES",
        "region": "PANAMA",
        "lat": 8.948889,
        "lon": -80.0625,
        "elevation": 104,
        "numero": "115-071",
        "tipo": "CA"
    },
    {
        "id": 103,
        "name": "EL CACAO",
        "region": "PANAMA",
        "lat": 7.440833,
        "lon": -80.409444,
        "elevation": 180,
        "numero": "115-081",
        "tipo": "CA"
    },
    {
        "id": 104,
        "name": "CIRI GRANDE",
        "region": "PANAMA",
        "lat": 8.772222,
        "lon": -80.058056,
        "elevation": 200,
        "numero": "115-083",
        "tipo": "CM"
    },
    {
        "id": 105,
        "name": "GUACHA",
        "region": "COLON",
        "lat": 9.176667,
        "lon": -79.938889,
        "elevation": 29,
        "numero": "115-085",
        "tipo": "CA"
    },
    {
        "id": 106,
        "name": "CASCADAS",
        "region": "PANAMA",
        "lat": 9.081389,
        "lon": -79.68,
        "elevation": 47,
        "numero": "115-086",
        "tipo": "CA"
    },
    {
        "id": 107,
        "name": "SARDINILLA",
        "region": "COLON",
        "lat": 9.089167,
        "lon": -79.679167,
        "elevation": 63,
        "numero": "115-088",
        "tipo": "AA"
    },
    {
        "id": 108,
        "name": "RIO PIEDRAS 2",
        "region": "PANAMA",
        "lat": 9.281667,
        "lon": -79.398056,
        "elevation": 198,
        "numero": "115-090",
        "tipo": "CA"
    },
    {
        "id": 109,
        "name": "RIO PIEDRAS ARRIBA",
        "region": "PANAMA",
        "lat": 9.331667,
        "lon": -79.399167,
        "elevation": 254,
        "numero": "115-094",
        "tipo": "AA"
    },
    {
        "id": 110,
        "name": "SANTA ROSA",
        "region": "COLON",
        "lat": 9.185556,
        "lon": -79.654167,
        "elevation": 28,
        "numero": "115-100",
        "tipo": "CA"
    },
    {
        "id": 111,
        "name": "GATUN WEST",
        "region": "COLON",
        "lat": 9.263056,
        "lon": -79.929167,
        "elevation": 33,
        "numero": "115-101",
        "tipo": "AA"
    },
    {
        "id": 112,
        "name": "JAGUA",
        "region": "PANAMA",
        "lat": 8.736944,
        "lon": -80.046944,
        "elevation": 546,
        "numero": "115-102",
        "tipo": "AA"
    },
    {
        "id": 113,
        "name": "VISTAMARES",
        "region": "COLON",
        "lat": 9.234167,
        "lon": -79.401389,
        "elevation": 969,
        "numero": "115-103",
        "tipo": "AA"
    },
    {
        "id": 114,
        "name": "FRIJOLITO",
        "region": "COLON",
        "lat": 9.218889,
        "lon": -79.715833,
        "elevation": 349,
        "numero": "115-104",
        "tipo": "CA"
    },
    {
        "id": 115,
        "name": "ESPERANZA",
        "region": "PANAMA",
        "lat": 9.409444,
        "lon": -79.351944,
        "elevation": 542,
        "numero": "115-105",
        "tipo": "CA"
    },
    {
        "id": 116,
        "name": "ARCA SONIA",
        "region": "PANAMA",
        "lat": 9.193056,
        "lon": -79.515,
        "elevation": 265,
        "numero": "115-106",
        "tipo": "AA"
    },
    {
        "id": 117,
        "name": "CHAMON",
        "region": "PANAMA",
        "lat": 9.341667,
        "lon": -79.318056,
        "elevation": 640,
        "numero": "115-107",
        "tipo": "CA"
    },
    {
        "id": 118,
        "name": "CERRO CAMA",
        "region": "PANAMA",
        "lat": 9.026667,
        "lon": -79.905556,
        "elevation": 120,
        "numero": "115-108",
        "tipo": "CA"
    },
    {
        "id": 119,
        "name": "DOS BOCAS",
        "region": "PANAMA",
        "lat": 9.4525,
        "lon": -79.430833,
        "elevation": 229,
        "numero": "115-109",
        "tipo": "AA"
    },
    {
        "id": 120,
        "name": "GASPARILLAL",
        "region": "PANAMA",
        "lat": 8.863056,
        "lon": -80.015556,
        "elevation": 346,
        "numero": "115-110",
        "tipo": "AA"
    },
    {
        "id": 121,
        "name": "CANO QUEBRADO",
        "region": "PANAMA",
        "lat": 9.004444,
        "lon": -79.825833,
        "elevation": 32,
        "numero": "115-111",
        "tipo": "CA"
    },
    {
        "id": 122,
        "name": "ZANGUENGA ACP",
        "region": "COLON",
        "lat": 8.954444,
        "lon": -79.866667,
        "elevation": 110,
        "numero": "115-112",
        "tipo": "CA"
    },
    {
        "id": 123,
        "name": "NUEVO SAN JUAN",
        "region": "COLON",
        "lat": 9.215556,
        "lon": -79.660278,
        "elevation": 0,
        "numero": "115-113",
        "tipo": "AA"
    },
    {
        "id": 124,
        "name": "AGUA BUENA",
        "region": "PANAMA",
        "lat": 9.128056,
        "lon": -79.591667,
        "elevation": 125,
        "numero": "115-114",
        "tipo": "CA"
    },
    {
        "id": 125,
        "name": "BARBACOA",
        "region": "COLON",
        "lat": 9.121667,
        "lon": -79.796667,
        "elevation": 53,
        "numero": "115-115",
        "tipo": "CA"
    },
    {
        "id": 126,
        "name": "PUNTA FRIJOLES",
        "region": "COLON",
        "lat": 9.160833,
        "lon": -79.805833,
        "elevation": 55,
        "numero": "115-116",
        "tipo": "CA"
    },
    {
        "id": 127,
        "name": "SANTA CLARA",
        "region": "PANAMA",
        "lat": 9.033056,
        "lon": -79.751667,
        "elevation": 102,
        "numero": "115-117",
        "tipo": "CA"
    },
    {
        "id": 128,
        "name": "PUNTA BOHIO",
        "region": "COLON",
        "lat": 9.184167,
        "lon": -79.855833,
        "elevation": 25,
        "numero": "115-118",
        "tipo": "CA"
    },
    {
        "id": 129,
        "name": "INDIO ESTE",
        "region": "PANAMA",
        "lat": 9.353056,
        "lon": -79.463333,
        "elevation": 101,
        "numero": "115-119",
        "tipo": "CA"
    },
    {
        "id": 130,
        "name": "AGUA SALUD",
        "region": "COLON",
        "lat": 9.224167,
        "lon": -79.760278,
        "elevation": 170,
        "numero": "115-120",
        "tipo": "AA"
    },
    {
        "id": 131,
        "name": "TRANQUILLA",
        "region": "PANAMA",
        "lat": 9.249167,
        "lon": -79.573889,
        "elevation": 64,
        "numero": "115-121",
        "tipo": "AA"
    },
    {
        "id": 132,
        "name": "GATUN VALLE CENTRAL",
        "region": "PANAMA",
        "lat": 9.375556,
        "lon": -79.638333,
        "elevation": 200,
        "numero": "115-122",
        "tipo": "CA"
    },
    {
        "id": 133,
        "name": "CHAGRECITO",
        "region": "PANAMA",
        "lat": 9.394444,
        "lon": -79.305556,
        "elevation": 479,
        "numero": "115-123",
        "tipo": "CA"
    },
    {
        "id": 134,
        "name": "GOLD HILL",
        "region": "PANAMA",
        "lat": 9.043056,
        "lon": -79.659167,
        "elevation": 180,
        "numero": "115-125",
        "tipo": "CA"
    },
    {
        "id": 135,
        "name": "ZANGUENGA",
        "region": "PANAMA OESTE",
        "lat": 8.951667,
        "lon": -79.852222,
        "elevation": 0,
        "numero": "115-127",
        "tipo": "AG"
    },
    {
        "id": 136,
        "name": "COIBA",
        "region": "VERAGUAS",
        "lat": 7.501667,
        "lon": -81.698056,
        "elevation": 10,
        "numero": "116-001",
        "tipo": "AA"
    },
    {
        "id": 137,
        "name": "CABISMALE",
        "region": "VERAGUAS",
        "lat": 7.886944,
        "lon": -81.473056,
        "elevation": 378,
        "numero": "116-003",
        "tipo": "CA"
    },
    {
        "id": 138,
        "name": "GUARUMAL",
        "region": "VERAGUAS",
        "lat": 7.801667,
        "lon": -81.254167,
        "elevation": 47,
        "numero": "116-004",
        "tipo": "AA"
    },
    {
        "id": 139,
        "name": "SAN PEDRO(REFINERIA)",
        "region": "COLON",
        "lat": 9.365833,
        "lon": -79.829167,
        "elevation": 9,
        "numero": "117-012",
        "tipo": "CM"
    },
    {
        "id": 140,
        "name": "SAN ANTONIO",
        "region": "COLON",
        "lat": 9.561667,
        "lon": -79.551111,
        "elevation": 47,
        "numero": "117-013",
        "tipo": "AG"
    },
    {
        "id": 141,
        "name": "EL PORVENIR 2",
        "region": "GUNA YALA",
        "lat": 9.556667,
        "lon": -78.948056,
        "elevation": 82,
        "numero": "117-014",
        "tipo": "CA"
    },
    {
        "id": 142,
        "name": "LIMON BAY",
        "region": "COLON",
        "lat": 9.355556,
        "lon": -79.914444,
        "elevation": 3,
        "numero": "117-015",
        "tipo": "AA"
    },
    {
        "id": 143,
        "name": "CHICO CABECERA",
        "region": "COLON",
        "lat": 9.349722,
        "lon": -79.463333,
        "elevation": 332,
        "numero": "117-016",
        "tipo": "CA"
    },
    {
        "id": 144,
        "name": "CUANGO",
        "region": "COLON",
        "lat": 9.544167,
        "lon": -79.303056,
        "elevation": 11,
        "numero": "117-017",
        "tipo": "AA"
    },
    {
        "id": 145,
        "name": "EL COBRIZO",
        "region": "VERAGUAS",
        "lat": 8.4525,
        "lon": -81.3875,
        "elevation": 400,
        "numero": "118-001",
        "tipo": "CM"
    },
    {
        "id": 146,
        "name": "CANAZAS",
        "region": "VERAGUAS",
        "lat": 8.314167,
        "lon": -81.208333,
        "elevation": 200,
        "numero": "118-002",
        "tipo": "BC"
    },
    {
        "id": 147,
        "name": "CATIVE",
        "region": "VERAGUAS",
        "lat": 7.9175,
        "lon": -81.378333,
        "elevation": 160,
        "numero": "118-009",
        "tipo": "CC"
    },
    {
        "id": 148,
        "name": "SANTIAGO",
        "region": "VERAGUAS",
        "lat": 8.086667,
        "lon": -80.944167,
        "elevation": 80,
        "numero": "120-002",
        "tipo": "AM"
    },
    {
        "id": 149,
        "name": "EL MARANON",
        "region": "VERAGUAS",
        "lat": 8.033056,
        "lon": -81.216667,
        "elevation": 50,
        "numero": "120-005",
        "tipo": "CC"
    },
    {
        "id": 150,
        "name": "LOS LLANOS DE OCU",
        "region": "HERRERA",
        "lat": 7.929444,
        "lon": -80.878889,
        "elevation": 0,
        "numero": "120-007",
        "tipo": "AG"
    },
    {
        "id": 151,
        "name": "MULATUPO",
        "region": "GUNA YALA",
        "lat": 8.943056,
        "lon": -77.754722,
        "elevation": 2,
        "numero": "121-006",
        "tipo": "AM"
    },
    {
        "id": 152,
        "name": "CARTI",
        "region": "GUNA YALA",
        "lat": 9.3,
        "lon": -78.983056,
        "elevation": 385,
        "numero": "121-007",
        "tipo": "CA"
    },
    {
        "id": 153,
        "name": "MARIATO",
        "region": "VERAGUAS",
        "lat": 7.65,
        "lon": -80.983056,
        "elevation": 23,
        "numero": "122-004",
        "tipo": "CM"
    },
    {
        "id": 154,
        "name": "CHEPO(ESC.GRANJA)",
        "region": "HERRERA",
        "lat": 7.7275,
        "lon": -80.821944,
        "elevation": 680,
        "numero": "122-006",
        "tipo": "BC"
    },
    {
        "id": 155,
        "name": "MARIATO 2",
        "region": "VERAGUAS",
        "lat": 7.646667,
        "lon": -80.997778,
        "elevation": 3,
        "numero": "122-008",
        "tipo": "AA"
    },
    {
        "id": 156,
        "name": "ARENAS DE QUEBRO 2",
        "region": "VERAGUAS",
        "lat": 7.375,
        "lon": -80.856667,
        "elevation": 21,
        "numero": "122-009",
        "tipo": "AG"
    },
    {
        "id": 157,
        "name": "LA LLANA",
        "region": "LOS SANTOS",
        "lat": 7.501667,
        "lon": -80.550556,
        "elevation": 60,
        "numero": "124-002",
        "tipo": "CC"
    },
    {
        "id": 158,
        "name": "ALTOS DE GÜERA",
        "region": "LOS SANTOS",
        "lat": 7.530833,
        "lon": -80.621667,
        "elevation": 212,
        "numero": "124-006",
        "tipo": "CA"
    },
    {
        "id": 159,
        "name": "CERRO QUEMA",
        "region": "LOS SANTOS",
        "lat": 7.5975,
        "lon": -80.473889,
        "elevation": 377,
        "numero": "124-007",
        "tipo": "AM"
    },
    {
        "id": 160,
        "name": "GUERA",
        "region": "LOS SANTOS",
        "lat": 9.485278,
        "lon": -80.551944,
        "elevation": 64,
        "numero": "124-008",
        "tipo": "CA"
    },
    {
        "id": 161,
        "name": "POCRI",
        "region": "LOS SANTOS",
        "lat": 7.661667,
        "lon": -80.118889,
        "elevation": 70,
        "numero": "126-002",
        "tipo": "CC"
    },
    {
        "id": 162,
        "name": "PEDASI",
        "region": "LOS SANTOS",
        "lat": 7.526667,
        "lon": -80.023333,
        "elevation": 47,
        "numero": "126-005",
        "tipo": "BC"
    },
    {
        "id": 163,
        "name": "VALLE RICO",
        "region": "LOS SANTOS",
        "lat": 7.623056,
        "lon": -80.353056,
        "elevation": 173,
        "numero": "126-010",
        "tipo": "BC"
    },
    {
        "id": 164,
        "name": "LA MIEL",
        "region": "LOS SANTOS",
        "lat": 7.549722,
        "lon": -80.333056,
        "elevation": 220,
        "numero": "126-012",
        "tipo": "CC"
    },
    {
        "id": 165,
        "name": "EL CANAFISTULO",
        "region": "LOS SANTOS",
        "lat": 7.620556,
        "lon": -80.231667,
        "elevation": 140,
        "numero": "126-013",
        "tipo": "CC"
    },
    {
        "id": 166,
        "name": "CANAS",
        "region": "LOS SANTOS",
        "lat": 7.448333,
        "lon": -80.262778,
        "elevation": 8,
        "numero": "126-015",
        "tipo": "CC"
    },
    {
        "id": 167,
        "name": "CACAO",
        "region": "LOS SANTOS",
        "lat": 7.440833,
        "lon": -80.409444,
        "elevation": 14,
        "numero": "126-019",
        "tipo": "AA"
    },
    {
        "id": 168,
        "name": "PEDASI 2",
        "region": "LOS SANTOS",
        "lat": 7.5325,
        "lon": -80.031389,
        "elevation": 15,
        "numero": "126-024",
        "tipo": "AA"
    },
    {
        "id": 169,
        "name": "LOS SANTOS",
        "region": "LOS SANTOS",
        "lat": 7.940556,
        "lon": -80.4175,
        "elevation": 16,
        "numero": "128-001",
        "tipo": "AM"
    },
    {
        "id": 170,
        "name": "PESE",
        "region": "HERRERA",
        "lat": 7.9,
        "lon": -80.616667,
        "elevation": 80,
        "numero": "128-010",
        "tipo": "CC"
    },
    {
        "id": 171,
        "name": "PAN DE AZUCAR",
        "region": "HERRERA",
        "lat": 7.733056,
        "lon": -80.7,
        "elevation": 250,
        "numero": "128-016",
        "tipo": "CC"
    },
    {
        "id": 172,
        "name": "MACARACAS 2",
        "region": "LOS SANTOS",
        "lat": 7.731111,
        "lon": -80.555833,
        "elevation": 95,
        "numero": "128-017",
        "tipo": "AA"
    },
    {
        "id": 173,
        "name": "ESTIBANA",
        "region": "LOS SANTOS",
        "lat": 7.838333,
        "lon": -80.523333,
        "elevation": 39,
        "numero": "128-018",
        "tipo": "AA"
    },
    {
        "id": 174,
        "name": "LLANO DE LA CRUZ",
        "region": "HERRERA",
        "lat": 7.956389,
        "lon": -80.64,
        "elevation": 60,
        "numero": "130-004",
        "tipo": "CC"
    },
    {
        "id": 175,
        "name": "VALLE RICO DE OCU",
        "region": "HERRERA",
        "lat": 7.95,
        "lon": -80.783056,
        "elevation": 53,
        "numero": "130-006",
        "tipo": "CC"
    },
    {
        "id": 176,
        "name": "VALLE RICO 2",
        "region": "HERRERA",
        "lat": 7.862222,
        "lon": -80.745833,
        "elevation": 141,
        "numero": "130-007",
        "tipo": "AA"
    },
    {
        "id": 177,
        "name": "EL PALMAR",
        "region": "VERAGUAS",
        "lat": 8.536944,
        "lon": -81.077778,
        "elevation": 1000,
        "numero": "132-001",
        "tipo": "CM"
    },
    {
        "id": 178,
        "name": "LOS VALLES",
        "region": "VERAGUAS",
        "lat": 8.444167,
        "lon": -81.194444,
        "elevation": 550,
        "numero": "132-003",
        "tipo": "CC"
    },
    {
        "id": 179,
        "name": "LAGUNA LA YEGUADA",
        "region": "VERAGUAS",
        "lat": 8.455833,
        "lon": -80.850833,
        "elevation": 640,
        "numero": "132-006",
        "tipo": "AG"
    },
    {
        "id": 180,
        "name": "CERRO VERDE",
        "region": "VERAGUAS",
        "lat": 8.504167,
        "lon": -80.841944,
        "elevation": 800,
        "numero": "132-008",
        "tipo": "CC"
    },
    {
        "id": 181,
        "name": "CALOBRE",
        "region": "VERAGUAS",
        "lat": 8.313889,
        "lon": -80.8375,
        "elevation": 120,
        "numero": "132-010",
        "tipo": "CM"
    },
    {
        "id": 182,
        "name": "DIVISA",
        "region": "HERRERA",
        "lat": 8.14,
        "lon": -80.704167,
        "elevation": 12,
        "numero": "132-012",
        "tipo": "AA"
    },
    {
        "id": 183,
        "name": "SANTA FE",
        "region": "VERAGUAS",
        "lat": 8.508056,
        "lon": -81.073056,
        "elevation": 463,
        "numero": "132-033",
        "tipo": "BC"
    },
    {
        "id": 184,
        "name": "GATU LA CRUZ",
        "region": "VERAGUAS",
        "lat": 8.5,
        "lon": -81.016667,
        "elevation": 0,
        "numero": "132-040",
        "tipo": "CA"
    },
    {
        "id": 185,
        "name": "SANTA FE",
        "region": "VERAGUAS",
        "lat": 8.510833,
        "lon": -81.075556,
        "elevation": 428,
        "numero": "132-041",
        "tipo": "AA"
    },
    {
        "id": 186,
        "name": "RIO GRANDE",
        "region": "COCLE",
        "lat": 8.416667,
        "lon": -80.483056,
        "elevation": 20,
        "numero": "134-003",
        "tipo": "CC"
    },
    {
        "id": 187,
        "name": "EL COPE",
        "region": "COCLE",
        "lat": 8.623889,
        "lon": -80.580556,
        "elevation": 400,
        "numero": "134-004",
        "tipo": "AM"
    },
    {
        "id": 188,
        "name": "SONADORA",
        "region": "COCLE",
        "lat": 8.55,
        "lon": -80.333056,
        "elevation": 168,
        "numero": "134-008",
        "tipo": "CC"
    },
    {
        "id": 189,
        "name": "LAS HUACAS DE QUIJE",
        "region": "COCLE",
        "lat": 8.466667,
        "lon": -80.75,
        "elevation": 440,
        "numero": "134-019",
        "tipo": "CC"
    },
    {
        "id": 190,
        "name": "RIO HONDO",
        "region": "COCLE",
        "lat": 8.366667,
        "lon": -80.366667,
        "elevation": 22,
        "numero": "134-020",
        "tipo": "CC"
    },
    {
        "id": 191,
        "name": "PUERTO POSADA",
        "region": "COCLE",
        "lat": 8.366667,
        "lon": -80.4,
        "elevation": 15,
        "numero": "134-022",
        "tipo": "CC"
    },
    {
        "id": 192,
        "name": "LAS SABANAS",
        "region": "COCLE",
        "lat": 8.566667,
        "lon": -80.683056,
        "elevation": 700,
        "numero": "134-023",
        "tipo": "CC"
    },
    {
        "id": 193,
        "name": "OLA",
        "region": "COCLE",
        "lat": 8.416667,
        "lon": -80.65,
        "elevation": 100,
        "numero": "134-024",
        "tipo": "CC"
    },
    {
        "id": 194,
        "name": "SANTA CRUZ DE PAJONAL",
        "region": "COCLE",
        "lat": 8.539167,
        "lon": -80.316389,
        "elevation": 319,
        "numero": "134-032",
        "tipo": "CC"
    },
    {
        "id": 195,
        "name": "EL VALLE DE ANTON",
        "region": "COCLE",
        "lat": 8.605,
        "lon": -80.123056,
        "elevation": 580,
        "numero": "136-001",
        "tipo": "AA"
    },
    {
        "id": 196,
        "name": "ANTON",
        "region": "COCLE",
        "lat": 8.383056,
        "lon": -80.266667,
        "elevation": 33,
        "numero": "136-002",
        "tipo": "AA"
    },
    {
        "id": 197,
        "name": "RIO HATO",
        "region": "COCLE",
        "lat": 8.373056,
        "lon": -80.163056,
        "elevation": 30,
        "numero": "138-004",
        "tipo": "CC"
    },
    {
        "id": 198,
        "name": "CHAME",
        "region": "PANAMA",
        "lat": 8.593056,
        "lon": -79.878056,
        "elevation": 30,
        "numero": "138-005",
        "tipo": "CC"
    },
    {
        "id": 199,
        "name": "SANTA RITA",
        "region": "COCLE",
        "lat": 8.498889,
        "lon": -80.188056,
        "elevation": 180,
        "numero": "138-008",
        "tipo": "CC"
    },
    {
        "id": 200,
        "name": "CERRO CAMPANA",
        "region": "PANAMA",
        "lat": 8.666944,
        "lon": -79.926389,
        "elevation": 750,
        "numero": "138-016",
        "tipo": "AG"
    },
    {
        "id": 201,
        "name": "CHAME2",
        "region": "PANAMA",
        "lat": 8.578056,
        "lon": -79.885,
        "elevation": 25,
        "numero": "138-017",
        "tipo": "CA"
    },
    {
        "id": 202,
        "name": "CAPIRA2",
        "region": "PANAMA",
        "lat": 8.754167,
        "lon": -79.878056,
        "elevation": 120,
        "numero": "138-018",
        "tipo": "CA"
    },
    {
        "id": 203,
        "name": "CAIMITO",
        "region": "PANAMA",
        "lat": 8.813333,
        "lon": -79.939167,
        "elevation": 180,
        "numero": "140-005",
        "tipo": "CC"
    },
    {
        "id": 204,
        "name": "SE CHORRERA",
        "region": "PANAMA",
        "lat": 8.907778,
        "lon": -79.778333,
        "elevation": 46,
        "numero": "140-006",
        "tipo": "AA"
    },
    {
        "id": 205,
        "name": "MASTRANTO",
        "region": "PANAMA",
        "lat": 8.908056,
        "lon": -79.7625,
        "elevation": 21,
        "numero": "140-008",
        "tipo": "CC"
    },
    {
        "id": 206,
        "name": "BALBOA HEIGHTS",
        "region": "PANAMA",
        "lat": 8.959167,
        "lon": -79.554167,
        "elevation": 30,
        "numero": "142-004",
        "tipo": "CA"
    },
    {
        "id": 207,
        "name": "PEDRO MIGUEL",
        "region": "PANAMA",
        "lat": 9.022778,
        "lon": -79.616944,
        "elevation": 31,
        "numero": "142-007",
        "tipo": "BA"
    },
    {
        "id": 208,
        "name": "CULEBRA",
        "region": "PANAMA",
        "lat": 9.053056,
        "lon": -79.650556,
        "elevation": 64,
        "numero": "142-013",
        "tipo": "AA"
    },
    {
        "id": 209,
        "name": "RIO COCOLI",
        "region": "PANAMA",
        "lat": 8.982222,
        "lon": -79.593333,
        "elevation": 37,
        "numero": "142-014",
        "tipo": "CA"
    },
    {
        "id": 210,
        "name": "MIRAFLORES",
        "region": "PANAMA",
        "lat": 9.014167,
        "lon": -79.609722,
        "elevation": 20,
        "numero": "142-015",
        "tipo": "CA"
    },
    {
        "id": 211,
        "name": "BALBOA (FAA)",
        "region": "PANAMA",
        "lat": 8.968889,
        "lon": -79.549167,
        "elevation": 10,
        "numero": "142-017",
        "tipo": "AA"
    },
    {
        "id": 212,
        "name": "DIABLO HEIGHTS",
        "region": "PANAMA",
        "lat": 8.965556,
        "lon": -79.573056,
        "elevation": 5,
        "numero": "142-018",
        "tipo": "CA"
    },
    {
        "id": 213,
        "name": "HATO PINTADO",
        "region": "PANAMA",
        "lat": 9.009167,
        "lon": -79.514167,
        "elevation": 45,
        "numero": "142-020",
        "tipo": "CA"
    },
    {
        "id": 214,
        "name": "CERRO PELON",
        "region": "PANAMA",
        "lat": 9.208889,
        "lon": -79.374444,
        "elevation": 770,
        "numero": "142-025",
        "tipo": "CA"
    },
    {
        "id": 215,
        "name": "SUN TOWER (EL DORADO)",
        "region": "PANAMA",
        "lat": 9.011667,
        "lon": -79.535278,
        "elevation": 80,
        "numero": "142-026",
        "tipo": "AA"
    },
    {
        "id": 216,
        "name": "AMADOR",
        "region": "PANAMA",
        "lat": 8.916667,
        "lon": -79.534444,
        "elevation": 2,
        "numero": "142-028",
        "tipo": "CA"
    },
    {
        "id": 217,
        "name": "COROZAL OESTE",
        "region": "PANAMA",
        "lat": 8.980556,
        "lon": -79.574444,
        "elevation": 7,
        "numero": "142-029",
        "tipo": "AA"
    },
    {
        "id": 218,
        "name": "CERRO COCOLI",
        "region": "PANAMA",
        "lat": 8.990278,
        "lon": -79.591667,
        "elevation": 72,
        "numero": "142-030",
        "tipo": "CA"
    },
    {
        "id": 219,
        "name": "SITIO VICTOR VALDES",
        "region": "PANAMA",
        "lat": 9.006667,
        "lon": -79.619167,
        "elevation": 0,
        "numero": "142-031",
        "tipo": "CA"
    },
    {
        "id": 220,
        "name": "ISLA BRUJA CHIQUITA",
        "region": "PANAMA",
        "lat": 9.210556,
        "lon": -79.916944,
        "elevation": 24,
        "numero": "142-032",
        "tipo": "CA"
    },
    {
        "id": 221,
        "name": "NUEVA BORINQUEN",
        "region": "PANAMA",
        "lat": 8.986389,
        "lon": -79.598056,
        "elevation": 0,
        "numero": "142-034",
        "tipo": "AA"
    },
    {
        "id": 222,
        "name": "COCOLI 326",
        "region": "PANAMA",
        "lat": 8.982222,
        "lon": -79.593333,
        "elevation": 40,
        "numero": "142-035",
        "tipo": "AA"
    },
    {
        "id": 223,
        "name": "PAITILLA",
        "region": "PANAMA",
        "lat": 8.9875,
        "lon": -79.499722,
        "elevation": 7,
        "numero": "142-036",
        "tipo": "BA"
    },
    {
        "id": 224,
        "name": "CURUNDU",
        "region": "PANAMA",
        "lat": 8.978333,
        "lon": -79.547222,
        "elevation": 26,
        "numero": "142-037",
        "tipo": "AA"
    },
    {
        "id": 225,
        "name": "CND",
        "region": "PANAMA",
        "lat": 9.036944,
        "lon": -79.525556,
        "elevation": 42,
        "numero": "142-042",
        "tipo": "CA"
    },
    {
        "id": 226,
        "name": "PARQUE OMAR",
        "region": "PANAMA",
        "lat": 9.000556,
        "lon": -79.507222,
        "elevation": 0,
        "numero": "142-043",
        "tipo": "BA"
    },
    {
        "id": 227,
        "name": "RANCHO CAFE",
        "region": "PANAMA",
        "lat": 9.133333,
        "lon": -79.382222,
        "elevation": 160,
        "numero": "144-005",
        "tipo": "AA"
    },
    {
        "id": 228,
        "name": "JUAN DIAZ LOS PUEBLOS",
        "region": "PANAMA",
        "lat": 9.048333,
        "lon": -79.448056,
        "elevation": 12,
        "numero": "144-007",
        "tipo": "CC"
    },
    {
        "id": 229,
        "name": "VILLA LUCRE",
        "region": "PANAMA",
        "lat": 9.073333,
        "lon": -79.48,
        "elevation": 65,
        "numero": "144-009",
        "tipo": "AA"
    },
    {
        "id": 230,
        "name": "TOCUMEN 2",
        "region": "PANAMA",
        "lat": 9.081944,
        "lon": -79.405556,
        "elevation": 38,
        "numero": "144-011",
        "tipo": "AA"
    },
    {
        "id": 231,
        "name": "JUAN DIAZ",
        "region": "PANAMA",
        "lat": 9.036667,
        "lon": -79.471667,
        "elevation": 16,
        "numero": "144-012",
        "tipo": "AA"
    },
    {
        "id": 232,
        "name": "LOMA BONITA",
        "region": "PANAMA",
        "lat": 9.171389,
        "lon": -79.260833,
        "elevation": 100,
        "numero": "146-002",
        "tipo": "CC"
    },
    {
        "id": 233,
        "name": "CHEPO",
        "region": "PANAMA",
        "lat": 9.166667,
        "lon": -79.083056,
        "elevation": 30,
        "numero": "148-001",
        "tipo": "CM"
    },
    {
        "id": 234,
        "name": "PIRIA (POBLADO)",
        "region": "PANAMA",
        "lat": 9.123889,
        "lon": -78.325278,
        "elevation": 80,
        "numero": "148-004",
        "tipo": "CM"
    },
    {
        "id": 235,
        "name": "RIO MAJE",
        "region": "PANAMA",
        "lat": 9.016667,
        "lon": -78.733056,
        "elevation": 70,
        "numero": "148-008",
        "tipo": "CC"
    },
    {
        "id": 236,
        "name": "BAYANO CAMPAMENTO",
        "region": "PANAMA",
        "lat": 9.183056,
        "lon": -78.886667,
        "elevation": 70,
        "numero": "148-011",
        "tipo": "CA"
    },
    {
        "id": 237,
        "name": "RIO DIABLO",
        "region": "PANAMA",
        "lat": 9.221389,
        "lon": -78.509167,
        "elevation": 146,
        "numero": "148-024",
        "tipo": "CA"
    },
    {
        "id": 238,
        "name": "IPETI",
        "region": "PANAMA",
        "lat": 8.976667,
        "lon": -78.505556,
        "elevation": 67,
        "numero": "148-036",
        "tipo": "CA"
    },
    {
        "id": 239,
        "name": "RIO INDIO MAJE",
        "region": "PANAMA",
        "lat": 8.969444,
        "lon": -78.696667,
        "elevation": 200,
        "numero": "148-039",
        "tipo": "AA"
    },
    {
        "id": 240,
        "name": "CHEPO 2",
        "region": "PANAMA",
        "lat": 9.169722,
        "lon": -79.104444,
        "elevation": 26,
        "numero": "148-048",
        "tipo": "AG"
    },
    {
        "id": 241,
        "name": "CHIMAN",
        "region": "PANAMA",
        "lat": 8.716667,
        "lon": -78.633056,
        "elevation": 30,
        "numero": "150-002",
        "tipo": "BC"
    },
    {
        "id": 242,
        "name": "ISLA CONTADORA",
        "region": "PANAMA",
        "lat": 8.628056,
        "lon": -79.036389,
        "elevation": 10,
        "numero": "150-004",
        "tipo": "CA"
    },
    {
        "id": 243,
        "name": "RIO CONGO",
        "region": "DARIEN",
        "lat": 8.4025,
        "lon": -78.369444,
        "elevation": 5,
        "numero": "152-005",
        "tipo": "CM"
    },
    {
        "id": 244,
        "name": "SANTA FE",
        "region": "DARIEN",
        "lat": 8.659167,
        "lon": -78.133333,
        "elevation": 36,
        "numero": "152-006",
        "tipo": "AA"
    },
    {
        "id": 245,
        "name": "AGUA FRIA",
        "region": "DARIEN",
        "lat": 8.813333,
        "lon": -78.186389,
        "elevation": 0,
        "numero": "152-008",
        "tipo": "AG"
    },
    {
        "id": 246,
        "name": "METETI",
        "region": "DARIEN",
        "lat": 8.495833,
        "lon": -77.978333,
        "elevation": 10,
        "numero": "154-018",
        "tipo": "CA"
    },
    {
        "id": 247,
        "name": "LA PULIDA",
        "region": "DARIEN",
        "lat": 8.303056,
        "lon": -77.619167,
        "elevation": 47,
        "numero": "154-021",
        "tipo": "AA"
    },
    {
        "id": 248,
        "name": "MORTI",
        "region": "DARIEN",
        "lat": 8.840833,
        "lon": -77.978333,
        "elevation": 49,
        "numero": "154-023",
        "tipo": "CA"
    },
    {
        "id": 249,
        "name": "BOCA DE CUPE 2",
        "region": "DARIEN",
        "lat": 8.032778,
        "lon": -77.585278,
        "elevation": 20,
        "numero": "156-004",
        "tipo": "AA"
    },
    {
        "id": 250,
        "name": "CAMOGANTI",
        "region": "DARIEN",
        "lat": 8.038611,
        "lon": -77.885278,
        "elevation": 17,
        "numero": "158-003",
        "tipo": "CM"
    },
    {
        "id": 251,
        "name": "GARACHINE",
        "region": "DARIEN",
        "lat": 8.065278,
        "lon": -78.366389,
        "elevation": 10,
        "numero": "162-001",
        "tipo": "BC"
    },
    {
        "id": 252,
        "name": "BOCA DE TRAMPA",
        "region": "DARIEN",
        "lat": 7.936944,
        "lon": -78.141944,
        "elevation": 100,
        "numero": "162-003",
        "tipo": "CM"
    },
    {
        "id": 253,
        "name": "JAQUE",
        "region": "DARIEN",
        "lat": 7.516667,
        "lon": -78.164444,
        "elevation": 10,
        "numero": "164-001",
        "tipo": "AA"
    },
]

# API configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

API_TIMEOUT = 30  # seconds
MAX_WORKERS = 4

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Data validation
MIN_REQUIRED_RECORDS = 100
MAX_MISSING_PERCENT = 0.3  # 30% missing allowed

# WebSocket
WS_HEARTBEAT_INTERVAL = 30  # seconds
WS_TIMEOUT = 60  # seconds

# Feature engineering
RAINFALL_THRESHOLD_FLOOD = 30  # mm
RAINFALL_THRESHOLD_DROUGHT = 5  # mm
CONSECUTIVE_DRY_DAYS_THRESHOLD = 15  # days
