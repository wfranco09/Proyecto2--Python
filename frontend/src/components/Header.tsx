import { Droplets, Cpu, Sun, CloudRain, Database } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

interface HeaderProps {
  riskType: 'flood' | 'drought';
  onRiskTypeChange: (type: 'flood' | 'drought') => void;
  lastUpdate: Date;
  onOpenPipelines?: () => void;
}

export const Header = ({ riskType, onRiskTypeChange, lastUpdate, onOpenPipelines }: HeaderProps) => {
  return (
    <motion.header 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card px-6 py-4 flex items-center justify-between"
    >
      {/* Logo and Title */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <motion.div
            animate={{ y: [0, -3, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center glow-primary"
          >
            <Droplets className="w-7 h-7 text-primary-foreground" />
          </motion.div>
          <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-md bg-card border border-border flex items-center justify-center">
            <Cpu className="w-3 h-3 text-primary" />
          </div>
        </div>
        
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-gradient">rAIn</span>
            <span className="text-foreground">drop</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            Predicción Inteligente de Riesgos Climáticos en Panamá
          </p>
        </div>
      </div>

      {/* Risk Type Toggle */}
      <div className="flex items-center gap-6">
        <div className="glass-card px-4 py-2 flex items-center gap-4">
          <div className={`flex items-center gap-2 transition-opacity ${riskType === 'flood' ? 'opacity-100' : 'opacity-40'}`}>
            <CloudRain className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium">Inundaciones</span>
          </div>
          
          <Switch
            checked={riskType === 'drought'}
            onCheckedChange={(checked) => onRiskTypeChange(checked ? 'drought' : 'flood')}
            className="data-[state=checked]:bg-warning data-[state=unchecked]:bg-primary"
          />
          
          <div className={`flex items-center gap-2 transition-opacity ${riskType === 'drought' ? 'opacity-100' : 'opacity-40'}`}>
            <Sun className="w-5 h-5 text-warning" />
            <span className="text-sm font-medium">Sequías</span>
          </div>
        </div>

        {/* Status and Last Update */}
        <div className="flex items-center gap-4">
          <button
            onClick={onOpenPipelines}
            className="glass-card px-4 py-2 rounded-lg hover:bg-primary/10 transition-colors flex items-center gap-2 text-sm font-medium hover:text-primary"
            title="Ejecutar pipelines de extracción de datos"
          >
            <Database className="w-4 h-4" />
            Pipelines
          </button>

          <div className="text-right">
            <p className="text-xs text-muted-foreground">Última actualización</p>
            <p className="text-sm font-medium">
              {lastUpdate.toLocaleTimeString('es-PA', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              })}
            </p>
          </div>
          
          <Badge 
            variant="outline" 
            className="border-success/50 bg-success/10 text-success pulse-success px-3 py-1.5"
          >
            <span className="w-2 h-2 rounded-full bg-success mr-2 animate-pulse" />
            Sistema Activo
          </Badge>
        </div>
      </div>
    </motion.header>
  );
};
