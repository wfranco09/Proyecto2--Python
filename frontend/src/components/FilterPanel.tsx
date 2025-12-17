import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { RefreshCw, Filter, AlertTriangle } from "lucide-react";
import { provinces } from "@/data/mockStations";
import { motion } from "framer-motion";
import { useState } from "react";

interface FilterPanelProps {
  minRisk: number;
  onMinRiskChange: (value: number) => void;
  selectedProvince: string;
  onProvinceChange: (value: string) => void;
  onlyAlerts: boolean;
  onOnlyAlertsChange: (value: boolean) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const FilterPanel = ({
  minRisk,
  onMinRiskChange,
  selectedProvince,
  onProvinceChange,
  onlyAlerts,
  onOnlyAlertsChange,
  onRefresh,
  isLoading
}: FilterPanelProps) => {
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.1 }}
      className="glass-card p-5 rounded-xl"
    >
      <div className="flex items-center gap-2 mb-5">
        <Filter className="w-5 h-5 text-primary" />
        <h3 className="font-semibold text-foreground">Filtros y Controles</h3>
      </div>
      
      <div className="space-y-5">
        {/* Min Risk Slider */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-muted-foreground">Riesgo mínimo</label>
            <span className="text-sm font-medium text-primary">{minRisk}%</span>
          </div>
          <Slider
            value={[minRisk]}
            onValueChange={([value]) => onMinRiskChange(value)}
            max={100}
            step={5}
            className="w-full"
          />
        </div>
        
        {/* Province Dropdown */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Filtrar por provincia</label>
          <Select value={selectedProvince} onValueChange={onProvinceChange}>
            <SelectTrigger className="w-full bg-secondary/50 border-border/50">
              <SelectValue placeholder="Seleccionar provincia" />
            </SelectTrigger>
            <SelectContent className="bg-card border-border z-50">
              {provinces.map((province) => (
                <SelectItem key={province} value={province}>
                  {province}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Only Alerts Toggle */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" />
            <span className="text-sm text-muted-foreground">Solo alertas activas (&gt;70%)</span>
          </div>
          <Switch
            checked={onlyAlerts}
            onCheckedChange={onOnlyAlertsChange}
            className="data-[state=checked]:bg-warning"
          />
        </div>
        
        {/* Refresh Button */}
        <Button 
          onClick={onRefresh}
          disabled={isLoading}
          className="w-full bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30"
          variant="outline"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Actualizando...' : 'Actualizar datos'}
        </Button>
      </div>
    </motion.div>
  );
};
