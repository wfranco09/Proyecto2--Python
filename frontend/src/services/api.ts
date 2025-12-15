/**
 * API Service for rAIndrop Backend
 * Connects frontend with FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Station {
  id: number;
  name: string;
  lat: number;
  lon: number;
  elevation: number;
  flood_risk: {
    probability: number;
    level: 'GREEN' | 'YELLOW' | 'RED';
    alert: boolean;
    triggered_at?: string | null;
  };
  drought_risk: {
    probability: number;
    level: 'GREEN' | 'YELLOW' | 'RED';
    alert: boolean;
    triggered_at?: string | null;
  };
}

export interface StationDetail extends Station {
  region: string;
  current_conditions: {
    temperature: number;
    humidity: number;
    rainfall: number;
    wind_speed: number;
    timestamp: string;
  };
  risk_assessment: {
    flood: {
      probability: number;
      level: string;
      alert: boolean;
      message: string;
    };
    drought: {
      probability: number;
      level: string;
      alert: boolean;
      message: string;
    };
  };
  trend: {
    flood_trend: string;
    drought_trend: string;
  };
}

export interface StationHistory {
  station_id: number;
  station_name: string;
  days: number;
  data: Array<{
    date: string;
    temperature: number;
    humidity: number;
    rainfall: number;
    wind_speed: number;
  }>;
}

export interface ModelMetrics {
  flood?: {
    accuracy: string;
    precision: string;
    recall: string;
    f1: string;
    auc_roc: string;
    n_samples: number;
    n_features: number;
    feature_importances: Record<string, string>;
  };
  drought?: {
    accuracy: string;
    precision: string;
    recall: string;
    f1: string;
    auc_roc: string;
    n_samples: number;
    n_features: number;
    feature_importances: Record<string, string>;
  };
}

export interface Prediction {
  risk_type: string;
  count: number;
  data: Array<{
    station_id: number;
    station_name: string;
    lat: number;
    lon: number;
    probability: number;
    risk_level: string;
    confidence: number;
    timestamp: string;
  }>;
}

export interface ForecastDay {
  date: string;
  day_of_week: string;
  flood_risk: {
    probability: number;
    level: 'GREEN' | 'YELLOW' | 'RED';
    alert: boolean;
  };
  drought_risk: {
    probability: number;
    level: 'GREEN' | 'YELLOW' | 'RED';
    alert: boolean;
  };
  conditions: {
    temperature: number;
    humidity: number;
    rainfall: number;
    wind_speed: number;
  };
  summary: string;
  icon: string;
  precipitation_probability: number;
}

export interface StationForecast {
  station_id: number;
  station_name: string;
  location: {
    lat: number;
    lon: number;
    elevation: number;
  };
  forecast_days: number;
  forecast: ForecastDay[];
}

export interface ForecastSummary {
  forecast_days: number;
  total_stations: number;
  daily_summary: Array<{
    date: string;
    flood_alerts: number;
    drought_alerts: number;
    high_flood_risk: number;
    high_drought_risk: number;
  }>;
}

class ApiService {
  private baseUrl: string;
  private stationsCache: { data: any; timestamp: number } | null = null;
  private readonly CACHE_DURATION = 5000; // 5 segundos de caché
  private pendingStationsRequest: Promise<any> | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  /**
   * GET /api/stations
   * Get all stations with current risk levels
   * Implementa caché y deduplicación de requests para evitar sobrecarga del servidor
   */
  async getAllStations(): Promise<{ total_stations: number; timestamp: string; data: Station[] }> {
    try {
      // Si hay un request pendiente, retornar ese mismo promise (deduplicación)
      if (this.pendingStationsRequest) {
        console.log('[API] Request en progreso, reutilizando...');
        return this.pendingStationsRequest;
      }

      // Verificar caché
      const now = Date.now();
      if (this.stationsCache && (now - this.stationsCache.timestamp) < this.CACHE_DURATION) {
        console.log('[API] Retornando datos del caché');
        return this.stationsCache.data;
      }

      // Crear nuevo request
      console.log('[API] Haciendo nueva petición a /api/stations');
      this.pendingStationsRequest = fetch(`${this.baseUrl}/api/stations`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          // Guardar en caché
          this.stationsCache = {
            data,
            timestamp: Date.now()
          };
          return data;
        })
        .finally(() => {
          // Limpiar request pendiente
          this.pendingStationsRequest = null;
        });

      return this.pendingStationsRequest;
    } catch (error) {
      console.error('Error fetching stations:', error);
      this.pendingStationsRequest = null;
      throw error;
    }
  }

  /**
   * Invalidar caché de estaciones para forzar nueva petición
   */
  invalidateStationsCache(): void {
    console.log('[API] Invalidando caché de estaciones');
    this.stationsCache = null;
    this.pendingStationsRequest = null;
  }

  /**
   * GET /api/stations/{station_id}
   * Get detailed information for a specific station
   */
  async getStationDetail(stationId: number): Promise<StationDetail> {
    try {
      const response = await fetch(`${this.baseUrl}/api/stations/${stationId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching station ${stationId}:`, error);
      throw error;
    }
  }

  /**
   * GET /api/stations/{station_id}/history
   * Get historical data for a station
   */
  async getStationHistory(stationId: number, days: number = 30): Promise<StationHistory> {
    try {
      const response = await fetch(`${this.baseUrl}/api/stations/${stationId}/history?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching history for station ${stationId}:`, error);
      throw error;
    }
  }

  /**
   * GET /api/stations/{station_id}/alerts
   * Get active alerts for a station
   */
  async getStationAlerts(stationId: number): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/stations/${stationId}/alerts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching alerts for station ${stationId}:`, error);
      throw error;
    }
  }

  /**
   * GET /api/predictions/current
   * Get latest predictions for all stations
   */
  async getCurrentPredictions(riskType?: 'flood' | 'drought'): Promise<any> {
    try {
      const url = riskType 
        ? `${this.baseUrl}/api/predictions/current?risk_type=${riskType}`
        : `${this.baseUrl}/api/predictions/current`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching current predictions:', error);
      throw error;
    }
  }

  /**
   * GET /api/predictions/{risk_type}
   * Get predictions for specific risk type
   */
  async getPredictions(riskType: 'flood' | 'drought', minProbability?: number): Promise<Prediction> {
    try {
      const url = minProbability
        ? `${this.baseUrl}/api/predictions/${riskType}?min_probability=${minProbability}`
        : `${this.baseUrl}/api/predictions/${riskType}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching ${riskType} predictions:`, error);
      throw error;
    }
  }

  /**
   * GET /api/predictions/{risk_type}/top
   * Get top N stations by risk
   */
  async getTopRiskStations(riskType: 'flood' | 'drought', top: number = 5): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/predictions/${riskType}/top?top=${top}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching top ${riskType} risk stations:`, error);
      throw error;
    }
  }

  /**
   * GET /api/models/metrics
   * Get model performance metrics
   */
  async getModelMetrics(model?: 'flood' | 'drought' | 'both'): Promise<ModelMetrics> {
    try {
      const url = model && model !== 'both'
        ? `${this.baseUrl}/api/models/metrics?model=${model}`
        : `${this.baseUrl}/api/models/metrics`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching model metrics:', error);
      throw error;
    }
  }

  /**
   * GET /api/health/status
   * Check backend health
   */
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health/status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }

  /**
   * WebSocket connection for real-time updates
   */
  connectWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/stream';
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return ws;
  }

  /**
   * Get available pipelines
   */
  async getAvailablePipelines() {
    const response = await fetch(`${this.baseUrl}/api/pipelines/available`);
    if (!response.ok) throw new Error('Failed to fetch pipelines');
    return response.json();
  }

  /**
   * Run a specific pipeline
   */
  async runPipeline(pipelineName: string, useRandom: boolean = true) {
    const url = `${this.baseUrl}/api/pipelines/run/${pipelineName}?use_random=${useRandom}`;
    const response = await fetch(url, {
      method: 'POST',
    });
    if (!response.ok) throw new Error(`Failed to run pipeline: ${pipelineName}`);
    return response.json();
  }

  /**
   * Stream generation progress for dummy data pipeline using Server-Sent Events
   */
  streamGenerationProgress(
    onProgress: (progress: any) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): EventSource {
    const eventSource = new EventSource(`${this.baseUrl}/api/pipelines/progress/generate_dummy`);

    eventSource.onmessage = (event) => {
      try {
        const progress = JSON.parse(event.data);
        onProgress(progress);
        
        // Si el proceso terminó, cerrar la conexión
        if (!progress.is_running) {
          eventSource.close();
          if (onComplete) onComplete();
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
        if (onError) onError(err as Error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
      if (onError) onError(new Error('Connection to progress stream failed'));
    };

    return eventSource;
  }

  /**
   * Connect to pipeline logs WebSocket
   */
  connectPipelineWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws') + '/api/pipelines/ws/logs';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Pipeline WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing pipeline WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Pipeline WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log('Pipeline WebSocket connection closed');
    };

    return ws;
  }

  /**
   * GET /api/forecast/{station_id}
   * Get forecast for specific station
   */
  async getStationForecast(stationId: number, days: number = 7): Promise<StationForecast> {
    try {
      const response = await fetch(`${this.baseUrl}/api/forecast/${stationId}?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching forecast for station ${stationId}:`, error);
      throw error;
    }
  }

  /**
   * GET /api/forecast
   * Get all forecasts
   */
  async getAllForecasts(days: number = 7): Promise<Record<number, StationForecast>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/forecast?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching all forecasts:', error);
      throw error;
    }
  }

  /**
   * GET /api/forecast/summary
   * Get forecast summary
   */
  async getForecastSummary(days: number = 7): Promise<ForecastSummary> {
    try {
      const response = await fetch(`${this.baseUrl}/api/forecast/summary?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching forecast summary:', error);
      throw error;
    }
  }
}

// Exportar instancia singleton
export const apiService = new ApiService();
export default apiService;
