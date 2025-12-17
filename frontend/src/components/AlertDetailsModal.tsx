import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Cloud,
  Droplets,
  Wind,
  Thermometer,
  MapPin,
  Clock,
  CheckCircle2,
  AlertCircle,
  X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Station } from '@/services/api';
import { apiService } from '@/services/api';

interface Alert {
  type: 'flood' | 'drought';
  probability: number;
  level: 'GREEN' | 'YELLOW' | 'RED';
  triggered_at: string;
  message: string;
  is_simulated?: boolean;
  recommended_actions: string[];
  current_conditions?: {
    temperature: number;
    humidity: number;
    rainfall: number;
    wind_speed: number;
    timestamp: string;
  };
}

interface AlertDetailsModalProps {
  station: Station | null;
  isOpen: boolean;
  onClose: () => void;
}

export const AlertDetailsModal: React.FC<AlertDetailsModalProps> = ({
  station,
  isOpen,
  onClose,
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && station) {
      fetchAlerts();
    }
  }, [isOpen, station]);

  const fetchAlerts = async () => {
    if (!station) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getStationAlerts(station.id);
      setAlerts(response.active_alerts || []);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('No se pudieron cargar los detalles de alertas');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'RED':
        return '#ef4444';
      case 'YELLOW':
        return '#f59e0b';
      case 'GREEN':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getRiskBgColor = (level: string) => {
    switch (level) {
      case 'RED':
        return 'bg-danger/10 border-danger/30';
      case 'YELLOW':
        return 'bg-warning/10 border-warning/30';
      case 'GREEN':
        return 'bg-success/10 border-success/30';
      default:
        return 'bg-muted/10 border-muted/30';
    }
  };

  const getRiskTextColor = (level: string) => {
    switch (level) {
      case 'RED':
        return 'text-danger';
      case 'YELLOW':
        return 'text-warning';
      case 'GREEN':
        return 'text-success';
      default:
        return 'text-muted-foreground';
    }
  };

  const getAlertIcon = (type: string) => {
    return type === 'flood' ? <Droplets className="w-5 h-5" /> : <Cloud className="w-5 h-5" />;
  };

  const formatDateTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  if (!isOpen || !station) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Overlay backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="absolute inset-0 bg-black/80"
          onClick={onClose}
        />

        {/* Modal - Centered */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          transition={{ duration: 0.3, type: 'spring', stiffness: 300, damping: 30 }}
          onClick={(e) => e.stopPropagation()}
          className="relative z-10 w-full max-w-2xl max-h-[90vh] rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700 shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="relative border-b border-slate-700 p-6 bg-gradient-to-r from-red-500/10 to-orange-500/10">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-danger/20">
                  <AlertTriangle className="w-6 h-6 text-danger" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-foreground">Detalles de Alertas</h2>
                  <p className="text-sm text-muted-foreground mt-1">{station.name}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      Lat: {station.lat.toFixed(4)}, Lon: {station.lon.toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="relative w-12 h-12 mb-4">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0"
                  >
                    <AlertTriangle className="w-12 h-12 text-primary" />
                  </motion.div>
                </div>
                <p className="text-muted-foreground">Cargando alertas...</p>
              </div>
            ) : error ? (
              <div className="bg-danger/20 border border-danger/50 rounded-lg p-4 text-danger">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-5 h-5" />
                  <span className="font-semibold">Error</span>
                </div>
                <p className="text-sm">{error}</p>
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle2 className="w-16 h-16 mx-auto text-success/50 mb-4" />
                <p className="text-foreground font-semibold text-lg">Sin Alertas Activas</p>
                <p className="text-muted-foreground text-sm mt-2">
                  Esta estación no tiene alertas en este momento
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`border-2 rounded-xl p-5 backdrop-blur-sm ${getRiskBgColor(alert.level)}`}
                  >
                    {/* Alert Title */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={`p-2 rounded-lg ${getRiskBgColor(alert.level)}`}>
                          <div className={getRiskTextColor(alert.level)}>{getAlertIcon(alert.type)}</div>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h3 className="font-bold text-foreground text-lg capitalize">
                              {alert.type === 'flood' ? 'Alerta de Inundación' : 'Alerta de Sequía'}
                            </h3>
                            {alert.is_simulated && (
                              <Badge className="text-xs bg-blue-500/30 border-blue-500/50 text-blue-300">
                                Datos Simulados
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{alert.message}</p>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className={`text-center ${getRiskBgColor(alert.level)} border-2 rounded-lg px-4 py-2`}>
                          <div className={`text-2xl font-bold ${getRiskTextColor(alert.level)}`}>
                            {(alert.probability * 100).toFixed(0)}%
                          </div>
                          <div className={`text-xs ${getRiskTextColor(alert.level)} font-semibold`}>
                            {alert.level}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="grid grid-cols-2 gap-3 mb-4 pb-4 border-b border-slate-700">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-muted-foreground" />
                        <span className="text-muted-foreground">{formatDateTime(alert.triggered_at)}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <AlertCircle className={`w-4 h-4 ${getRiskTextColor(alert.level)}`} />
                        <span className={`font-semibold ${getRiskTextColor(alert.level)}`}>
                          {alert.level === 'RED' ? 'Crítico' : alert.level === 'YELLOW' ? 'Moderado' : 'Bajo'}
                        </span>
                      </div>
                    </div>

                    {/* Current Conditions */}
                    {alert.current_conditions && (
                      <div className="mb-4">
                        <h4 className="font-semibold text-sm text-foreground mb-3 flex items-center gap-2">
                          <Cloud className="w-4 h-4" />
                          Condiciones Actuales
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
                            <Thermometer className="w-5 h-5 text-orange-500 mx-auto mb-2" />
                            <span className="text-xs text-muted-foreground block">Temperatura</span>
                            <span className="text-lg font-bold text-foreground">
                              {alert.current_conditions.temperature.toFixed(1)}°C
                            </span>
                          </div>
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
                            <Cloud className="w-5 h-5 text-blue-400 mx-auto mb-2" />
                            <span className="text-xs text-muted-foreground block">Humedad</span>
                            <span className="text-lg font-bold text-foreground">
                              {alert.current_conditions.humidity.toFixed(0)}%
                            </span>
                          </div>
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
                            <Droplets className="w-5 h-5 text-cyan-400 mx-auto mb-2" />
                            <span className="text-xs text-muted-foreground block">Lluvia</span>
                            <span className="text-lg font-bold text-foreground">
                              {alert.current_conditions.rainfall.toFixed(1)}mm
                            </span>
                          </div>
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
                            <Wind className="w-5 h-5 text-purple-400 mx-auto mb-2" />
                            <span className="text-xs text-muted-foreground block">Viento</span>
                            <span className="text-lg font-bold text-foreground">
                              {alert.current_conditions.wind_speed.toFixed(1)}km/h
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Recommended Actions */}
                    <div>
                      <h4 className="font-semibold text-sm text-foreground mb-3 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        Acciones Recomendadas
                      </h4>
                      <ul className="space-y-2">
                        {alert.recommended_actions.map((action, i) => (
                          <li key={i} className="flex items-start gap-3 text-sm">
                            <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${getRiskTextColor(alert.level)}`} />
                            <span className="text-muted-foreground">{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-slate-700 p-4 flex gap-3 justify-end bg-slate-800/50 backdrop-blur-sm">
            <Button 
              variant="outline" 
              onClick={onClose}
              className="border-slate-600 hover:bg-slate-700"
            >
              Cerrar
            </Button>
            <Button
              onClick={fetchAlerts}
              disabled={loading}
              className="bg-primary hover:bg-primary/90 text-white font-semibold"
            >
              {loading ? 'Actualizando...' : 'Actualizar'}
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
