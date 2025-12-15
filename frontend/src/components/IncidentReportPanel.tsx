import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, AlertTriangle, Droplets, Sun, X, Send, Navigation, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/hooks/use-toast";

interface IncidentReportPanelProps {
  isSelectingLocation: boolean;
  onToggleLocationSelection: () => void;
  selectedLocation: { lat: number; lon: number } | null;
  onClearLocation: () => void;
  reloadTrigger?: number;
  activeIncidents?: any[];
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
  activeIncidents = []
}: IncidentReportPanelProps) => {
  const [incidentType, setIncidentType] = useState<'flood' | 'drought'>('flood');
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedLocation) {
      toast({
        title: "Ubicación requerida",
        description: "Por favor selecciona un punto en el mapa",
        variant: "destructive",
      });
      return;
    }

    if (!description.trim()) {
      toast({
        title: "Descripción requerida",
        description: "Por favor describe la anomalía o incidencia",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
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
          severity: 'medium',
          reported_by: 'web_user'
        }),
      });

      if (!response.ok) {
        throw new Error('Error al enviar el reporte');
      }

      // Recargar la lista de reportes activos
      await loadActiveIncidents();
      
      setDescription("");
      onClearLocation();

      toast({
        title: "Incidencia reportada",
        description: `Reporte de ${incidentType === 'flood' ? 'inundación' : 'sequía'} enviado correctamente`,
      });
    } catch (error) {
      console.error('Error al enviar reporte:', error);
      toast({
        title: "Error",
        description: "No se pudo enviar el reporte. Intenta nuevamente.",
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

    try {
      const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Actualizar la lista localmente
        setIncidents(prev => prev.filter(inc => inc.id !== incidentId));
        
        toast({
          title: "Reporte eliminado",
          description: "El reporte ha sido eliminado exitosamente",
        });
      } else {
        throw new Error('Error al eliminar');
      }
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
          disabled={isSubmitting || !selectedLocation || !description.trim()}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Send className={`w-4 h-4 mr-2 ${isSubmitting ? 'animate-pulse' : ''}`} />
          {isSubmitting ? "Enviando..." : "Enviar reporte"}
        </Button>

        {/* Recent Incidents */}
        {activeIncidents.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/50">
            <h4 className="text-sm font-medium text-foreground mb-3">Reportes recientes</h4>
            <div className="space-y-2 max-h-[150px] overflow-y-auto scrollbar-thin">
              {activeIncidents.slice(0, 5).map((incident) => {
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
