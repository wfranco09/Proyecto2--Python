import { useEffect, useRef } from 'react';
import { Station } from '@/services/api';
import { motion } from 'framer-motion';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface RiskMapProps {
  stations: Station[];
  riskType: 'flood' | 'drought';
  onStationSelect: (station: Station) => void;
  isSelectingLocation?: boolean;
  onLocationSelect?: (location: { lat: number; lon: number }) => void;
  incidentMarker?: { lat: number; lon: number } | null;
  onIncidentDeleted?: () => void;
  activeIncidents?: any[];
  showIncidentsOnMap?: boolean;
}

const MapLegend = () => (
  <div className="absolute bottom-6 left-6 z-[1000] glass-card p-4 rounded-xl pointer-events-auto">
    <h4 className="text-sm font-semibold mb-3 text-foreground">Nivel de Riesgo</h4>
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="w-3 h-3 rounded-full bg-success" />
        <span className="text-xs text-muted-foreground">Bajo (GREEN 0-30%)</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-warning" />
        <span className="text-xs text-muted-foreground">Moderado (YELLOW 30-80%)</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-danger" />
        <span className="text-xs text-muted-foreground">Alto (RED 80-100%)</span>
      </div>
    </div>
  </div>
);

const getMarkerColor = (level: string): string => {
  if (level === 'GREEN') return '#10b981';
  if (level === 'YELLOW') return '#f59e0b';
  return '#ef4444'; // ROJO
};

const getMarkerRadius = (probability: number): number => {
  if (probability < 0.3) return 8;
  if (probability < 0.8) return 10;
  return 12;
};

export const RiskMap = ({ 
  stations, 
  riskType, 
  onStationSelect,
  isSelectingLocation = false,
  onLocationSelect,
  incidentMarker,
  onIncidentDeleted,
  activeIncidents = [],
  showIncidentsOnMap = true
}: RiskMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);
  const incidentMarkerRef = useRef<L.Marker | null>(null);
  const activeIncidentsRef = useRef<L.Marker[]>([]);

  // Inicializar mapa
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [8.5, -80.0],
      zoom: 8,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Manejar clic en mapa para selección de ubicación
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const handleClick = (e: L.LeafletMouseEvent) => {
      if (isSelectingLocation && onLocationSelect) {
        onLocationSelect({ lat: e.latlng.lat, lon: e.latlng.lng });
      }
    };

    if (isSelectingLocation) {
      map.getContainer().style.cursor = 'crosshair';
      map.on('click', handleClick);
    } else {
      map.getContainer().style.cursor = '';
    }

    return () => {
      map.off('click', handleClick);
      if (map.getContainer()) {
        map.getContainer().style.cursor = '';
      }
    };
  }, [isSelectingLocation, onLocationSelect]);

  // Manejar marcador de incidente
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Eliminar marcador de incidente existente
    if (incidentMarkerRef.current) {
      incidentMarkerRef.current.remove();
      incidentMarkerRef.current = null;
    }

    // Agregar nuevo marcador de incidente si hay ubicación seleccionada
    if (incidentMarker) {
      const customIcon = L.divIcon({
        className: 'custom-incident-marker',
        html: `
          <div style="
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 3px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <span style="transform: rotate(45deg); font-size: 14px;">📍</span>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 30],
      });

      const marker = L.marker([incidentMarker.lat, incidentMarker.lon], { icon: customIcon });
      marker.addTo(map);
      incidentMarkerRef.current = marker;
    }
  }, [incidentMarker]);

  // Mostrar reportes de incidentes activos desde props
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !activeIncidents) return;

    // Limpiar marcadores anteriores
    activeIncidentsRef.current.forEach(marker => marker.remove());
    activeIncidentsRef.current = [];
    
    // Si no se deben mostrar incidentes, salir temprano
    if (!showIncidentsOnMap) return;
    
    // Agregar nuevos marcadores
    activeIncidents.forEach((report: any) => {
      // Crear ícono de triángulo de peligro
      const triangleIcon = L.divIcon({
        className: 'custom-incident-marker',
        html: `
          <div style="
            position: relative;
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-bottom: 26px solid ${report.incident_type === 'flood' ? '#3b82f6' : '#f59e0b'};
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
          ">
            <div style="
              position: absolute;
              top: 8px;
              left: -7px;
              font-size: 14px;
              color: white;
              font-weight: bold;
            ">⚠</div>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 30],
      });
      
      const marker = L.marker([report.latitude, report.longitude], { 
        icon: triangleIcon 
      });
      
      // Popup con información del reporte y botón de eliminar
      const reportDate = new Date(report.reported_at);
      const popupContent = document.createElement('div');
      popupContent.style.cssText = 'color: #fff; background: #1a1a1a; padding: 8px; border-radius: 8px; min-width: 200px;';
      
      popupContent.innerHTML = `
        <strong style="color: ${report.incident_type === 'flood' ? '#3b82f6' : '#f59e0b'};">
          ${report.incident_type === 'flood' ? '💧 Reporte de Inundación' : '☀️ Reporte de Sequía'}
        </strong>
        <p style="margin: 8px 0; font-size: 12px;">${report.description}</p>
        <p style="font-size: 10px; color: #888; margin-bottom: 8px;">
          ${reportDate.toLocaleString('es-PA')}
        </p>
        <button 
          id="delete-incident-${report.id}"
          style="
            width: 100%;
            padding: 6px 12px;
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: background 0.2s;
          "
          onmouseover="this.style.background='#dc2626'"
          onmouseout="this.style.background='#ef4444'"
        >
          🗑️ Eliminar reporte
        </button>
      `;
      
      // Agregar evento al botón de eliminar
      const deleteButton = popupContent.querySelector(`#delete-incident-${report.id}`);
      if (deleteButton) {
        deleteButton.addEventListener('click', async () => {
          if (confirm('¿Estás seguro de eliminar este reporte?')) {
            try {
              const response = await fetch(`http://localhost:8000/api/incidents/${report.id}`, {
                method: 'DELETE',
              });
              
              if (response.ok) {
                marker.remove();
                activeIncidentsRef.current = activeIncidentsRef.current.filter(m => m !== marker);
                
                // Notificar al componente padre para actualizar la lista
                if (onIncidentDeleted) {
                  onIncidentDeleted();
                }
                
                console.log('Reporte eliminado exitosamente');
              } else {
                alert('Error al eliminar el reporte');
              }
            } catch (error) {
              console.error('Error eliminando reporte:', error);
              alert('Error al eliminar el reporte');
            }
          }
        });
      }
      
      marker.bindPopup(popupContent);
      marker.addTo(map);
      activeIncidentsRef.current.push(marker);
    });
  }, [activeIncidents, showIncidentsOnMap]);

  // Actualizar marcadores cuando cambian estaciones o tipo de riesgo
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Limpiar marcadores existentes
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Agregar nuevos marcadores
    stations.forEach((station) => {
      const riskData = riskType === 'flood' ? station.flood_risk : station.drought_risk;
      const probability = riskData.probability;
      const level = riskData.level;
      const color = getMarkerColor(level);
      const radius = getMarkerRadius(probability);

      const marker = L.circleMarker([station.lat, station.lon], {
        radius,
        fillColor: color,
        fillOpacity: 0.8,
        color: 'rgba(255,255,255,0.3)',
        weight: 2,
      });

      const popupContent = `
        <div style="min-width: 250px; font-family: 'Inter', sans-serif;">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div>
              <h3 style="font-weight: bold; font-size: 14px; margin: 0; color: #e2e8f0;">${station.name}</h3>
              <p style="font-size: 11px; color: #94a3b8; margin: 4px 0 0 0;">ID: ${station.id}</p>
            </div>
            <span style="
              padding: 4px 8px; 
              border-radius: 6px; 
              font-size: 11px; 
              font-weight: bold;
              background: ${level === 'RED' ? '#fef2f2' : level === 'YELLOW' ? '#fffbeb' : '#ecfdf5'};
              color: ${level === 'RED' ? '#dc2626' : level === 'YELLOW' ? '#d97706' : '#059669'};
            ">${(probability * 100).toFixed(0)}%</span>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; font-size: 12px; color: #475569;">
            <div>📍 ${station.lat.toFixed(2)}, ${station.lon.toFixed(2)}</div>
            <div>⛰️ ${station.elevation} m</div>
          </div>
          
          <div style="font-size: 11px; color: #64748b; margin-bottom: 12px;">
            🎯 Nivel: ${level}<br>
            ${riskData.alert ? '⚠️ Alerta Activa' : '✅ Sin alertas'}
          </div>
          
          
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.bindTooltip(`${station.name}<br>${(probability * 100).toFixed(0)}% riesgo`, {
        direction: 'top',
        offset: [0, -5],
        opacity: 0.95,
      });

      marker.addTo(map);
      markersRef.current.push(marker);
    });

    // Setup global handler for popup button clicks
    (window as any).handleStationHistory = (stationId: number) => {
      const station = stations.find(s => s.id === stationId);
      if (station) {
        onStationSelect(station);
      }
    };

    return () => {
      delete (window as any).handleStationHistory;
    };
  }, [stations, riskType, onStationSelect]);

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className={`relative h-full w-full rounded-xl overflow-hidden glass-card ${isSelectingLocation ? 'ring-2 ring-warning ring-offset-2 ring-offset-background' : ''}`}
    >
      {isSelectingLocation && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-warning/90 text-warning-foreground px-4 py-2 rounded-full text-sm font-medium shadow-lg">
          Haz clic en el mapa para seleccionar ubicación
        </div>
      )}
      <div ref={mapRef} className="h-full w-full z-0" />
      <MapLegend />
    </motion.div>
  );
};
