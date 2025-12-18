import { useState, useMemo, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { FilterPanel } from "@/components/FilterPanel";
import { AlertsPanel } from "@/components/AlertsPanel";
import { ModelMetricsPanel } from "@/components/ModelMetricsPanel";
import { StatsGrid } from "@/components/StatsGrid";
import { HistoricalModal } from "@/components/HistoricalModal";
import { AlertDetailsModal } from "@/components/AlertDetailsModal";
import { PipelineExecutionModal } from "@/components/PipelineExecutionModal";
import { ForecastDateSelector } from "@/components/ForecastDateSelector";
import { Footer } from "@/components/Footer";
import { RiskMap } from "@/components/RiskMap";
import { IncidentReportPanel } from "@/components/IncidentReportPanel";
import { mockModelMetrics } from "@/data/mockStations";
import { motion } from "framer-motion";
import { apiService, Station, type StationForecast, type ForecastDay } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Calendar, RefreshCw } from "lucide-react";

const Index = () => {
  const [riskType, setRiskType] = useState<'flood' | 'drought'>('flood');
  const [minRisk, setMinRisk] = useState(0);
  const [selectedProvince, setSelectedProvince] = useState("Todas");
  const [onlyAlerts, setOnlyAlerts] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAlertStation, setSelectedAlertStation] = useState<Station | null>(null);
  const [isAlertDetailsOpen, setIsAlertDetailsOpen] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  
  // Datos reales del backend
  const [stations, setStations] = useState<Station[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Estado de pronóstico
  const [viewMode, setViewMode] = useState<'current' | 'forecast'>('current');
  const [selectedForecastDate, setSelectedForecastDate] = useState<string | null>(null);
  const [forecastStations, setForecastStations] = useState<Station[]>([]);
  const [isLoadingForecast, setIsLoadingForecast] = useState(false);
  const [isGeneratingForecast, setIsGeneratingForecast] = useState(false);
  const [allForecastData, setAllForecastData] = useState<Record<number, StationForecast> | null>(null);
  
  // Estado de reporte de incidentes
  const [isSelectingLocation, setIsSelectingLocation] = useState(false);
  const [selectedIncidentLocation, setSelectedIncidentLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [incidentReloadTrigger, setIncidentReloadTrigger] = useState(0);
  const [activeIncidents, setActiveIncidents] = useState<any[]>([]);
  const [showIncidentsOnMap, setShowIncidentsOnMap] = useState(true);

  // Obtener estaciones al montar y cuando cambie el tipo de riesgo
  useEffect(() => {
    fetchStations();
    loadActiveIncidents(); // Cargar incidentes una sola vez
    
    // Auto-refresh opcional de estaciones cada 60 segundos (comentado por defecto para evitar sobrecarga)
    // Descomentar si se necesita auto-refresh de datos
    // const stationsInterval = setInterval(fetchStations, 60000);
    
    // Recargar incidentes cada 60 segundos (reducido de 30 para menor carga)
    const incidentsInterval = setInterval(loadActiveIncidents, 60000);
    
    return () => {
      // clearInterval(stationsInterval);
      clearInterval(incidentsInterval);
    };
  }, []);

  // Recargar incidentes cuando se dispare el trigger
  useEffect(() => {
    if (incidentReloadTrigger > 0) {
      loadActiveIncidents();
    }
  }, [incidentReloadTrigger]);

  // Cargar pronóstico de "hoy" cuando se cambia a modo forecast
  useEffect(() => {
    if (viewMode === 'forecast' && !selectedForecastDate && !allForecastData) {
      // Activar loading inmediatamente
      setIsLoadingForecast(true);
      // Obtener fecha de hoy
      const today = new Date().toISOString().split('T')[0];
      handleForecastDateSelect(today);
    }
  }, [viewMode]);

  const loadActiveIncidents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents/active');
      if (response.ok) {
        const data = await response.json();
        setActiveIncidents(data.reports || []);
      }
    } catch (error) {
      console.error('Error cargando incidentes activos:', error);
    }
  };

  const fetchStations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('[Index] Fetching stations...');
      const response = await apiService.getAllStations();
      setStations(response.data);
      setLastUpdate(new Date(response.timestamp));
      console.log('[Index] Stations fetched:', response.data.length);
    } catch (err) {
      console.error('Error fetching stations:', err);
      setError('Error al cargar datos del backend. Verifica que el servidor esté corriendo en http://localhost:8000');
    } finally {
      setIsLoading(false);
    }
  }, []); // Sin dependencias - las funciones setters de useState son estables

  const handleRefresh = () => {
    // Invalidar caché para forzar nueva petición
    apiService.invalidateStationsCache();
    fetchStations();
  };

  const handleStationSelect = (station: Station) => {
    setSelectedStation(station);
    setIsModalOpen(true);
  };

  const handleAlertStationSelect = (station: Station) => {
    setSelectedAlertStation(station);
    setIsAlertDetailsOpen(true);
  };

  const handleLocationSelect = (location: { lat: number; lon: number }) => {
    setSelectedIncidentLocation(location);
    setIsSelectingLocation(false);
  };

  const handleIncidentDeleted = () => {
    // Activar recarga en IncidentReportPanel
    setIncidentReloadTrigger(prev => prev + 1);
  };

  const handleForecastDateSelect = async (date: string) => {
    setSelectedForecastDate(date);
    setViewMode('forecast');
    
    // Si ya tenemos los datos cargados, solo filtrar
    if (allForecastData && Object.keys(allForecastData).length > 0) {
      filterForecastDataByDate(date);
    } else {
      // Si no hay datos, cargar
      await loadForecastForDate(date);
    }
  };

  const loadForecastForDate = async (date: string) => {
    setIsLoadingForecast(true);
    setIsGeneratingForecast(false);
    try {
      const allForecasts = await apiService.getAllForecasts(2);
      
      // Verificar si obtuvimos una respuesta vacía (pronósticos generándose)
      if (Object.keys(allForecasts).length === 0) {
        setIsGeneratingForecast(true);
        setIsLoadingForecast(false);
        return;
      }
      
      // Almacenar todos los datos de pronóstico para ambos días
      setAllForecastData(allForecasts);
      
      // Convertir datos de pronóstico a formato Station para la fecha seleccionada inmediatamente
      const forecastStationsData: Station[] = Object.values(allForecasts).map((stationForecast: StationForecast) => {
        const dayForecast = stationForecast.forecast.find((f: ForecastDay) => f.date === date);
        
        if (!dayForecast) {
          return {
            id: stationForecast.station_id,
            name: stationForecast.station_name,
            lat: stationForecast.location.lat,
            lon: stationForecast.location.lon,
            elevation: stationForecast.location.elevation,
            flood_risk: { probability: 0, level: 'GREEN' as const, alert: false },
            drought_risk: { probability: 0, level: 'GREEN' as const, alert: false }
          };
        }
        
        return {
          id: stationForecast.station_id,
          name: stationForecast.station_name,
          lat: stationForecast.location.lat,
          lon: stationForecast.location.lon,
          elevation: stationForecast.location.elevation,
          flood_risk: dayForecast.flood_risk,
          drought_risk: dayForecast.drought_risk
        };
      });
      
      setForecastStations(forecastStationsData);
      
      setError(null); // Limpiar errores previos
      setIsGeneratingForecast(false);
    } catch (err: any) {
      console.error('Error loading forecast:', err);
      
      // Verificar si es status 202 (generando pronósticos)
      if (err.message && err.message.includes('202')) {
        setIsGeneratingForecast(true);
      } else {
        setError('Error al cargar pronósticos. Intenta de nuevo en unos momentos.');
        setIsGeneratingForecast(false);
      }
    } finally {
      setIsLoadingForecast(false);
    }
  };

  const filterForecastDataByDate = (date: string) => {
    if (!allForecastData || Object.keys(allForecastData).length === 0) {
      // Si no hay datos cargados aún, no activar carga aquí (causa loop infinito)
      // Dejar que la función padre maneje la carga
      return;
    }

    // Convertir datos de pronóstico a formato Station para la fecha seleccionada
    const forecastStationsData: Station[] = Object.values(allForecastData).map((stationForecast: StationForecast) => {
      // Encontrar el pronóstico para la fecha seleccionada
      const dayForecast = stationForecast.forecast.find((f: ForecastDay) => f.date === date);
      
      if (!dayForecast) {
        // Retornar una estación por defecto sin riesgo si no se encuentra la fecha
        return {
          id: stationForecast.station_id,
          name: stationForecast.station_name,
          lat: stationForecast.location.lat,
          lon: stationForecast.location.lon,
          elevation: stationForecast.location.elevation,
          flood_risk: {
            probability: 0,
            level: 'GREEN' as const,
            alert: false
          },
          drought_risk: {
            probability: 0,
            level: 'GREEN' as const,
            alert: false
          }
        };
      }
      
      return {
        id: stationForecast.station_id,
        name: stationForecast.station_name,
        lat: stationForecast.location.lat,
        lon: stationForecast.location.lon,
        elevation: stationForecast.location.elevation,
        flood_risk: dayForecast.flood_risk,
        drought_risk: dayForecast.drought_risk
      };
    });
    
    setForecastStations(forecastStationsData);
  };

  const handleToggleViewMode = () => {
    if (viewMode === 'current') {
      setViewMode('forecast');
    } else {
      setViewMode('current');
      setSelectedForecastDate(null);
      setIsGeneratingForecast(false);
    }
  };

  // Determinar qué estaciones mostrar
  const displayStations = viewMode === 'forecast' ? forecastStations : stations;
  const isLoadingData = viewMode === 'forecast' ? isLoadingForecast : isLoading;

  // Filtrar estaciones según criterios de riesgo
  const filteredStations = useMemo(() => {
    return displayStations.filter(station => {
      const riskData = riskType === 'flood' ? station.flood_risk : station.drought_risk;
      const probability = riskData.probability;
      
      if (probability * 100 < minRisk) return false;
      if (onlyAlerts && !riskData.alert) return false;
      
      // Filtrar por provincia usando el atributo 'region' del backend (case-insensitive)
      if (selectedProvince !== "Todas" && station.region) {
        const normalizedRegion = station.region.toUpperCase();
        const normalizedSelected = selectedProvince.toUpperCase();
        if (normalizedRegion !== normalizedSelected) {
          return false;
        }
      }
      
      return true;
    });
  }, [displayStations, riskType, minRisk, onlyAlerts, selectedProvince]);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header 
        riskType={riskType} 
        onRiskTypeChange={setRiskType} 
        lastUpdate={lastUpdate}
        onOpenPipelines={() => setIsPipelineModalOpen(true)}
      />
      
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 text-sm text-center">
          ⚠️ {error}
        </div>
      )}
      
      {isGeneratingForecast && (
        <div className="bg-blue-500/10 border-b border-blue-500/20 px-4 py-3 text-sm text-center">
          <div className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
            <span className="text-blue-600 dark:text-blue-400 font-medium">
              Generando pronósticos en segundo plano... Este proceso puede tomar unos momentos.
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Los pronósticos se están extrayendo de la API. Puedes refrescar en unos segundos.
          </p>
        </div>
      )}
      
      <main className="flex-1 p-4 flex gap-4 overflow-hidden">
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex-[7] min-h-[calc(100vh-180px)]"
        >
          {displayStations.length > 0 ? (
            <RiskMap 
              stations={filteredStations} 
              riskType={riskType} 
              onStationSelect={handleStationSelect}
              isSelectingLocation={isSelectingLocation}
              onLocationSelect={handleLocationSelect}
              incidentMarker={selectedIncidentLocation}
              onIncidentDeleted={handleIncidentDeleted}
              activeIncidents={activeIncidents}
              showIncidentsOnMap={showIncidentsOnMap}
            />
          ) : (
            <div className="h-full flex items-center justify-center glass-card rounded-xl">
              <div className="text-center max-w-md mx-auto">
                {isLoadingData || isGeneratingForecast ? (
                  <>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground font-medium mb-2">
                      {isGeneratingForecast 
                        ? 'Extrayendo pronósticos de la API...' 
                        : viewMode === 'forecast' 
                          ? 'Cargando pronóstico...' 
                          : 'Cargando estaciones...'}
                    </p>
                    {isGeneratingForecast && (
                      <p className="text-sm text-muted-foreground">
                        Los datos de pronóstico se están generando. Por favor espera unos momentos.
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    {viewMode === 'current' ? (
                      <>
                        <p className="text-muted-foreground mb-2">
                          No hay datos disponibles
                        </p>
                        <button 
                          onClick={handleRefresh}
                          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                        >
                          Reintentar
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                        <p className="text-muted-foreground font-medium mb-2">
                          Cargando pronóstico de hoy...
                        </p>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </motion.div>
        
        <div className="flex-[3] flex flex-col gap-4 overflow-y-auto scrollbar-thin max-h-[calc(100vh-180px)]">
          <div className="glass-card p-4 rounded-xl">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold flex items-center gap-2">
                {viewMode === 'current' ? (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Vista Actual
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4" />
                    Vista Pronóstico
                  </>
                )}
              </h3>
              <Button
                variant={viewMode === 'forecast' ? 'default' : 'outline'}
                size="sm"
                onClick={handleToggleViewMode}
              >
                {viewMode === 'current' ? (
                  <>
                    <Calendar className="w-4 h-4 mr-2" />
                    Ver Pronóstico
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Ver Actual
                  </>
                )}
              </Button>
            </div>
            {viewMode === 'current' && (
              <p className="text-sm text-muted-foreground">
                Mostrando datos en tiempo real de las estaciones
              </p>
            )}
            {viewMode === 'forecast' && selectedForecastDate && (
              <p className="text-sm text-muted-foreground">
                Pronóstico para: {(() => {
                  const [year, month, day] = selectedForecastDate.split('-').map(Number);
                  const date = new Date(year, month - 1, day);
                  return date.toLocaleDateString('es-ES', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  });
                })()}
              </p>
            )}
          </div>
          
          {viewMode === 'forecast' && (
            <ForecastDateSelector
              selectedDate={selectedForecastDate}
              onDateSelect={handleForecastDateSelect}
            />
          )}
          
          <FilterPanel 
            minRisk={minRisk} 
            onMinRiskChange={setMinRisk} 
            selectedProvince={selectedProvince} 
            onProvinceChange={setSelectedProvince} 
            onlyAlerts={onlyAlerts} 
            onOnlyAlertsChange={setOnlyAlerts} 
            onRefresh={viewMode === 'current' ? handleRefresh : () => selectedForecastDate && loadForecastForDate(selectedForecastDate)} 
            isLoading={isLoadingData} 
          />
          
          {viewMode === 'current' && (
            <IncidentReportPanel 
              isSelectingLocation={isSelectingLocation}
              onToggleLocationSelection={() => setIsSelectingLocation(!isSelectingLocation)}
              selectedLocation={selectedIncidentLocation}
              onClearLocation={() => setSelectedIncidentLocation(null)}
              reloadTrigger={incidentReloadTrigger}
              activeIncidents={activeIncidents}
              onIncidentCreated={() => {
                // Recargar incidentes desde el backend
                loadActiveIncidents();
              }}
              onIncidentDeleted={() => {
                // Recargar incidentes desde el backend
                loadActiveIncidents();
              }}
              showIncidentsOnMap={showIncidentsOnMap}
              onToggleShowIncidents={setShowIncidentsOnMap}
            />
          )}
          
          <AlertsPanel stations={displayStations} riskType={riskType} onStationSelect={handleAlertStationSelect} />
          <ModelMetricsPanel metrics={mockModelMetrics} />
          <StatsGrid stations={filteredStations} riskType={riskType} lastUpdate={lastUpdate} />
        </div>
      </main>
      
      <Footer lastSync={lastUpdate} />
      <HistoricalModal station={selectedStation} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} riskType={riskType} />
      <AlertDetailsModal station={selectedAlertStation} isOpen={isAlertDetailsOpen} onClose={() => setIsAlertDetailsOpen(false)} />
      <PipelineExecutionModal 
        isOpen={isPipelineModalOpen} 
        onClose={() => setIsPipelineModalOpen(false)}
        onDataUpdated={fetchStations}
      />
    </div>
  );
};

export default Index;
