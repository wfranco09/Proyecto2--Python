import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { MapPin, AlertTriangle, Droplets, Sun, X, Send, Navigation, Trash2, Eye, EyeOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/hooks/use-toast";

interface IncidentReportPanelProps {
  isSelectingLocation: boolean;
  onToggleLocationSelection: () => void;
  selectedLocation: { lat: number; lon: number } | null;
  onClearLocation: () => void;
  reloadTrigger?: number;
  activeIncidents?: any[];
  onIncidentCreated?: (incident: any) => void;
  onIncidentDeleted?: (incidentId: number) => void;
  showIncidentsOnMap?: boolean;
  onToggleShowIncidents?: (show: boolean) => void;
}

interface Incident {
  id: number;
  incident_type: 'flood' | 'drought';
  description: string;
  latitude: number;
  longitude: number;
  reported_at: string;
}

export const IncidentReportPanel = ({
  isSelectingLocation,
  onToggleLocationSelection,
  selectedLocation,
  onClearLocation,
  reloadTrigger,
  activeIncidents = [],
  onIncidentCreated,
  onIncidentDeleted,
  showIncidentsOnMap = true,
  onToggleShowIncidents
}: IncidentReportPanelProps) => {
  const [incidentType, setIncidentType] = useState<'flood' | 'drought'>('flood');
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high'>('medium');
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localIncidents, setLocalIncidents] = useState<any[]>([]);

  // Sincronizar incidentes locales con los del parent
  useEffect(() => {
    setLocalIncidents(activeIncidents);
  }, [activeIncidents]);

  const handleSubmit = async () => {
    if (!selectedLocation) {
      toast({
        title: "Ubicación requerida",
        description: "Por favor selecciona un punto en el mapa",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Crear incidente temporal para mostrar inmediatamente (optimistic update)
      const tempIncident = {
        id: Date.now(), // ID temporal
        incident_type: incidentType,
        description: description.trim(),
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lon,
        severity: severity,
        reported_by: 'web_user',
        reported_at: new Date().toISOString(),
        status: 'active'
      };

      // Actualizar UI inmediatamente (optimistic)
      setLocalIncidents(prev => [tempIncident, ...prev]);

      // Enviar al backend
      const response = await fetch('http://localhost:8000/api/incidents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          incident_type: incidentType,
          description: description.trim(),
          latitude: selectedLocation.lat,
          longitude: selectedLocation.lon,
          severity: severity,
          reported_by: 'web_user'
        }),
      });

      if (!response.ok) {
        // Revertir optimistic update si falla
        setLocalIncidents(prev => prev.filter(inc => inc.id !== tempIncident.id));
        
        // Intentar parsear el error del backend para mostrar detalles
        let errorMessage = 'Error al enviar el reporte';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            // Si es un array de errores de validación (422)
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((err: any) => 
                `${err.loc?.join('.') || 'Campo'}: ${err.msg}`
              ).join('; ');
            } else {
              errorMessage = errorData.detail;
            }
          }
        } catch (e) {
          // Si no se puede parsear el error, usar mensaje genérico
        }
        throw new Error(errorMessage);
      }

      // Parsear respuesta JSON del backend
      const result = await response.json();
      
      // Reemplazar incidente temporal con el real
      const realIncident = {
        ...tempIncident,
        id: result.id // Usar ID real del backend
      };
      
      setLocalIncidents(prev => 
        prev.map(inc => inc.id === tempIncident.id ? realIncident : inc)
      );

      // Notificar al parent component
      if (onIncidentCreated) {
        onIncidentCreated(realIncident);
      }
      
      setDescription("");
      onClearLocation();

      toast({
        title: "Incidencia reportada",
        description: `Reporte de ${incidentType === 'flood' ? 'inundación' : 'sequía'} enviado correctamente`,
      });
    } catch (error) {
      console.error('Error al enviar reporte:', error);
      const errorMessage = error instanceof Error ? error.message : "No se pudo enviar el reporte";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteIncident = async (incidentId: number) => {
    if (!confirm('¿Estás seguro de eliminar este reporte?')) {
      return;
    }

    // Guardar copia para revertir si falla
    const previousIncidents = [...localIncidents];

    try {
      // Actualizar UI inmediatamente (optimistic)
      setLocalIncidents(prev => prev.filter(inc => inc.id !== incidentId));

      const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        // Revertir si falla
        setLocalIncidents(previousIncidents);
        throw new Error('Error al eliminar');
      }

      // Notificar al parent component
      if (onIncidentDeleted) {
        onIncidentDeleted(incidentId);
      }
        
      toast({
        title: "Reporte eliminado",
        description: "El reporte ha sido eliminado exitosamente",
      });
    } catch (error) {
      console.error('Error eliminando reporte:', error);
      toast({
        title: "Error",
        description: "No se pudo eliminar el reporte",
        variant: "destructive",
      });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-card p-5 rounded-xl"
    >
      <div className="flex items-center gap-2 mb-5">
        <AlertTriangle className="w-5 h-5 text-warning" />
        <h3 className="font-semibold text-foreground">Reportar Anomalía</h3>
      </div>

      <div className="space-y-4">
        {/* Incident Type Selection */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Tipo de incidencia</label>
          <Select value={incidentType} onValueChange={(val: 'flood' | 'drought') => setIncidentType(val)}>
            <SelectTrigger className="w-full bg-secondary/50 border-border/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-card border-border z-50">
              <SelectItem value="flood">
                <div className="flex items-center gap-2">
                  <Droplets className="w-4 h-4 text-primary" />
                  <span>Inundación</span>
                </div>
              </SelectItem>
              <SelectItem value="drought">
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4 text-warning" />
                  <span>Sequía</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Severity Selection */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Severidad</label>
          <Select value={severity} onValueChange={(val: 'low' | 'medium' | 'high') => setSeverity(val)}>
            <SelectTrigger className="w-full bg-secondary/50 border-border/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-card border-border z-50">
              <SelectItem value="low">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Baja</span>
                </div>
              </SelectItem>
              <SelectItem value="medium">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <span>Media</span>
                </div>
              </SelectItem>
              <SelectItem value="high">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Alta</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Location Selection */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Ubicación en el mapa</label>
          <div className="flex gap-2">
            <Button
              onClick={onToggleLocationSelection}
              variant={isSelectingLocation ? "default" : "outline"}
              className={`flex-1 ${
                isSelectingLocation 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-secondary/50 border-border/50 text-foreground hover:bg-secondary"
              }`}
            >
              <Navigation className={`w-4 h-4 mr-2 ${isSelectingLocation ? 'animate-pulse' : ''}`} />
              {isSelectingLocation ? "Seleccionando..." : "Seleccionar punto"}
            </Button>
          </div>
          
          <AnimatePresence>
            {selectedLocation && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-2 flex items-center justify-between bg-success/10 border border-success/30 rounded-lg px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-success" />
                  <span className="text-xs text-success">
                    {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
                  </span>
                </div>
                <button 
                  onClick={onClearLocation}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Description */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Descripción</label>
          <Textarea
            placeholder="Describe la anomalía o incidencia observada..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="bg-secondary/50 border-border/50 text-foreground placeholder:text-muted-foreground min-h-[80px] resize-none"
          />
        </div>

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || !selectedLocation}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Send className={`w-4 h-4 mr-2 ${isSubmitting ? 'animate-pulse' : ''}`} />
          {isSubmitting ? "Enviando..." : "Enviar reporte"}
        </Button>

        {/* Recent Incidents */}
        {localIncidents.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-foreground">Reportes recientes</h4>
              <div className="flex items-center gap-2">
                {showIncidentsOnMap ? (
                  <Eye className="w-4 h-4 text-success" />
                ) : (
                  <EyeOff className="w-4 h-4 text-muted-foreground" />
                )}
                <Switch
                  checked={showIncidentsOnMap}
                  onCheckedChange={(checked) => onToggleShowIncidents?.(checked)}
                  className="data-[state=checked]:bg-success"
                />
              </div>
            </div>
            <div className="space-y-2 max-h-[150px] overflow-y-auto scrollbar-thin">
              {localIncidents.slice(0, 5).map((incident) => {
                const reportDate = new Date(incident.reported_at);
                return (
                  <motion.div
                    key={incident.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-start gap-2 bg-secondary/30 rounded-lg p-2 group"
                  >
                    {incident.incident_type === 'flood' ? (
                      <Droplets className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    ) : (
                      <Sun className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-foreground truncate">{incident.description}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {reportDate.toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteIncident(incident.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-danger flex-shrink-0"
                      title="Eliminar reporte"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};
