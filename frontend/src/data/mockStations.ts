export interface Station {
  station_id: string;
  station_name: string;
  lat: number;
  lon: number;
  flood_proba: number;
  drought_proba: number;
  elevation_m: number;
  terrain_class: string;
  province: string;
  temp: number;
  humidity: number;
  rainfall: number;
  wind_speed: number;
  timestamp: string;
  status: 'low' | 'moderate' | 'high';
}

export interface ModelMetrics {
  model: string;
  accuracy: number;
  auc: number;
  feature_importances: Record<string, number>;
  threshold: number;
  last_trained: string;
}

export interface HistoricalData {
  timestamp: string;
  temp: number;
  humidity: number;
  rainfall: number;
  wind_speed: number;
  flood_proba: number;
}

export const mockStations: Station[] = [
  {
    station_id: "93-002",
    station_name: "AEROPUERTO DE BOCAS",
    lat: 9.3403,
    lon: -82.245,
    flood_proba: 0.85,
    drought_proba: 0.12,
    elevation_m: 5.0,
    terrain_class: "Lomerío suave",
    province: "Bocas del Toro",
    temp: 28.5,
    humidity: 93,
    rainfall: 45,
    wind_speed: 12,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "144-006",
    station_name: "SE PANAMA2",
    lat: 9.0892,
    lon: -79.368,
    flood_proba: 0.92,
    drought_proba: 0.05,
    elevation_m: 15.0,
    terrain_class: "Planicie",
    province: "Panamá",
    temp: 30.2,
    humidity: 88,
    rainfall: 62,
    wind_speed: 8,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "108-004",
    station_name: "GATUN",
    lat: 9.2667,
    lon: -79.9167,
    flood_proba: 0.78,
    drought_proba: 0.08,
    elevation_m: 26.0,
    terrain_class: "Valle",
    province: "Colón",
    temp: 29.1,
    humidity: 91,
    rainfall: 38,
    wind_speed: 10,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "115-003",
    station_name: "DAVID",
    lat: 8.4333,
    lon: -82.4333,
    flood_proba: 0.45,
    drought_proba: 0.22,
    elevation_m: 27.0,
    terrain_class: "Lomerío suave",
    province: "Chiriquí",
    temp: 31.0,
    humidity: 75,
    rainfall: 18,
    wind_speed: 15,
    timestamp: new Date().toISOString(),
    status: 'moderate'
  },
  {
    station_id: "120-008",
    station_name: "TOCUMEN",
    lat: 9.0833,
    lon: -79.3833,
    flood_proba: 0.68,
    drought_proba: 0.15,
    elevation_m: 12.0,
    terrain_class: "Planicie costera",
    province: "Panamá",
    temp: 29.8,
    humidity: 85,
    rainfall: 35,
    wind_speed: 11,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "125-012",
    station_name: "SANTIAGO",
    lat: 8.1000,
    lon: -80.9833,
    flood_proba: 0.32,
    drought_proba: 0.35,
    elevation_m: 85.0,
    terrain_class: "Lomerío moderado",
    province: "Veraguas",
    temp: 28.3,
    humidity: 72,
    rainfall: 12,
    wind_speed: 9,
    timestamp: new Date().toISOString(),
    status: 'moderate'
  },
  {
    station_id: "130-015",
    station_name: "CHITRÉ",
    lat: 7.9667,
    lon: -80.4333,
    flood_proba: 0.18,
    drought_proba: 0.55,
    elevation_m: 25.0,
    terrain_class: "Planicie seca",
    province: "Herrera",
    temp: 33.5,
    humidity: 58,
    rainfall: 3,
    wind_speed: 18,
    timestamp: new Date().toISOString(),
    status: 'low'
  },
  {
    station_id: "135-018",
    station_name: "LAS TABLAS",
    lat: 7.7667,
    lon: -80.2667,
    flood_proba: 0.12,
    drought_proba: 0.62,
    elevation_m: 28.0,
    terrain_class: "Planicie seca",
    province: "Los Santos",
    temp: 34.1,
    humidity: 52,
    rainfall: 1,
    wind_speed: 20,
    timestamp: new Date().toISOString(),
    status: 'low'
  },
  {
    station_id: "140-021",
    station_name: "PENONOMÉ",
    lat: 8.5167,
    lon: -80.3500,
    flood_proba: 0.42,
    drought_proba: 0.28,
    elevation_m: 55.0,
    terrain_class: "Lomerío suave",
    province: "Coclé",
    temp: 29.5,
    humidity: 78,
    rainfall: 22,
    wind_speed: 12,
    timestamp: new Date().toISOString(),
    status: 'moderate'
  },
  {
    station_id: "145-024",
    station_name: "COLÓN",
    lat: 9.3500,
    lon: -79.9000,
    flood_proba: 0.72,
    drought_proba: 0.08,
    elevation_m: 8.0,
    terrain_class: "Planicie costera",
    province: "Colón",
    temp: 29.0,
    humidity: 92,
    rainfall: 42,
    wind_speed: 14,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "150-027",
    station_name: "CHEPO",
    lat: 9.1667,
    lon: -79.1000,
    flood_proba: 0.55,
    drought_proba: 0.18,
    elevation_m: 35.0,
    terrain_class: "Valle",
    province: "Panamá",
    temp: 28.8,
    humidity: 82,
    rainfall: 28,
    wind_speed: 8,
    timestamp: new Date().toISOString(),
    status: 'moderate'
  },
  {
    station_id: "155-030",
    station_name: "VOLCÁN",
    lat: 8.7667,
    lon: -82.6333,
    flood_proba: 0.25,
    drought_proba: 0.42,
    elevation_m: 1450.0,
    terrain_class: "Montaña",
    province: "Chiriquí",
    temp: 18.5,
    humidity: 88,
    rainfall: 15,
    wind_speed: 22,
    timestamp: new Date().toISOString(),
    status: 'moderate'
  },
  {
    station_id: "160-033",
    station_name: "CHANGUINOLA",
    lat: 9.4333,
    lon: -82.5167,
    flood_proba: 0.88,
    drought_proba: 0.05,
    elevation_m: 12.0,
    terrain_class: "Planicie costera",
    province: "Bocas del Toro",
    temp: 28.2,
    humidity: 95,
    rainfall: 55,
    wind_speed: 6,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "165-036",
    station_name: "YAVIZA",
    lat: 8.1500,
    lon: -77.7000,
    flood_proba: 0.65,
    drought_proba: 0.12,
    elevation_m: 18.0,
    terrain_class: "Selva tropical",
    province: "Darién",
    temp: 27.8,
    humidity: 94,
    rainfall: 48,
    wind_speed: 5,
    timestamp: new Date().toISOString(),
    status: 'high'
  },
  {
    station_id: "170-039",
    station_name: "AGUADULCE",
    lat: 8.2500,
    lon: -80.5500,
    flood_proba: 0.15,
    drought_proba: 0.58,
    elevation_m: 15.0,
    terrain_class: "Planicie seca",
    province: "Coclé",
    temp: 32.8,
    humidity: 55,
    rainfall: 2,
    wind_speed: 16,
    timestamp: new Date().toISOString(),
    status: 'low'
  }
];

export const mockModelMetrics: ModelMetrics = {
  model: "RandomForest",
  accuracy: 0.985,
  auc: 0.99,
  feature_importances: {
    "LLUVIA": 0.89,
    "TEMP": 0.06,
    "VIENTO": 0.03,
    "HUMEDAD": 0.02
  },
  threshold: 0.7,
  last_trained: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
};

export const generateHistoricalData = (days: number = 7): HistoricalData[] => {
  const data: HistoricalData[] = [];
  const now = new Date();
  
  for (let i = days * 24; i >= 0; i -= 6) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      timestamp: timestamp.toISOString(),
      temp: 25 + Math.random() * 10,
      humidity: 60 + Math.random() * 35,
      rainfall: Math.random() * 60,
      wind_speed: 5 + Math.random() * 20,
      flood_proba: 0.3 + Math.random() * 0.6
    });
  }
  
  return data;
};

export const provinces = [
  "Todas",
  "BOCAS DEL TORO",
  "CHIRIQUI",
  "COCLE",
  "COLON",
  "DARIEN",
  "GNABE BUGLE",
  "GUNA YALA",
  "HERRERA",
  "LOS SANTOS",
  "PANAMA",
  "PANAMA OESTE",
  "VERAGUAS"
];
