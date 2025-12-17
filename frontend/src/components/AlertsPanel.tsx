import { Station } from "@/services/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, MapPin, Clock, Eye, Bell } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useMemo } from "react";

interface AlertsPanelProps {
  stations: Station[];
  riskType: 'flood' | 'drought';
  onStationSelect: (station: Station) => void;
}

export const AlertsPanel = ({ stations, riskType, onStationSelect }: AlertsPanelProps) => {

  const alertStations = useMemo(() => {
    return stations
      .filter(s => {
        const riskData = riskType === 'flood' ? s.flood_risk : s.drought_risk;
        return riskData.probability >= 0.5;
      })
      .sort((a, b) => {
        const probA = (riskType === 'flood' ? a.flood_risk : a.drought_risk).probability;
        const probB = (riskType === 'flood' ? b.flood_risk : b.drought_risk).probability;
        return probB - probA;
      });
  }, [stations, riskType]);

  // Función para calcular tiempo transcurrido
  const getTimeAgo = (triggeredAt: string | null | undefined): string => {
    if (!triggeredAt) return "Hace pocos momentos";
    
    try {
      const now = new Date();
      const alertTime = new Date(triggeredAt);
      const diffMs = now.getTime() - alertTime.getTime();
      const diffMinutes = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMinutes / 60);
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffDays > 0) {
        return `Hace ${diffDays} día${diffDays > 1 ? 's' : ''}`;
      } else if (diffHours > 0) {
        return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
      } else if (diffMinutes > 0) {
        return `Hace ${diffMinutes} minuto${diffMinutes > 1 ? 's' : ''}`;
      } else {
        return "Hace pocos momentos";
      }
    } catch (e) {
      return "Hace pocos momentos";
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-card p-5 rounded-xl"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-danger" />
          <h3 className="font-semibold text-foreground">Alertas Activas</h3>
        </div>
        <Badge 
          variant="outline" 
          className="bg-danger/10 border-danger/30 text-danger font-bold"
        >
          {alertStations.length}
        </Badge>
      </div>
      
      <ScrollArea className="h-[300px] pr-2 scrollbar-thin">
        <AnimatePresence>
          {alertStations.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No hay alertas activas</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alertStations.map((station, index) => {
                const riskData = riskType === 'flood' ? station.flood_risk : station.drought_risk;
                const probability = riskData.probability;
                const isHighRisk = probability > 0.8;
                const timeAgo = getTimeAgo(riskData.triggered_at);
                
                return (
                  <motion.div
                    key={station.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`glass-card-hover p-4 rounded-lg cursor-pointer ${
                      isHighRisk ? 'border-danger/50' : 'border-warning/50'
                    }`}
                    onClick={() => onStationSelect(station)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className={`flex items-center gap-2 text-xs font-bold uppercase ${
                        isHighRisk ? 'text-danger' : 'text-warning'
                      }`}>
                        {isHighRisk && (
                          <span className="w-2 h-2 rounded-full bg-danger pulse-danger" />
                        )}
                        {isHighRisk ? 'RIESGO ALTO' : 'RIESGO MODERADO'}
                      </div>
                      <Badge 
                        variant="outline"
                        className={`font-bold ${
                          isHighRisk 
                            ? 'bg-danger/20 border-danger/50 text-danger' 
                            : 'bg-warning/20 border-warning/50 text-warning'
                        }`}
                      >
                        {(probability * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    
                    <h4 className="font-medium text-foreground mb-1 text-sm">
                      {station.name}
                    </h4>
                    <p className="text-xs text-muted-foreground mb-2">
                      ID: {station.id}
                    </p>
                    
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {station.lat.toFixed(2)}, {station.lon.toFixed(2)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {timeAgo}
                      </span>
                    </div>
                    
                    <p className="text-xs text-muted-foreground italic">
                      Click para ver detalles
                    </p>
                  </motion.div>
                );
              })}
            </div>
          )}
        </AnimatePresence>
      </ScrollArea>
    </motion.div>
  );
};
