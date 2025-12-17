import { Station } from "@/services/api";
import { MapPin, AlertTriangle, TrendingUp, Clock } from "lucide-react";
import { motion } from "framer-motion";

interface StatsGridProps {
  stations: Station[];
  riskType: 'flood' | 'drought';
  lastUpdate: Date;
}

export const StatsGrid = ({ stations, riskType, lastUpdate }: StatsGridProps) => {
  const highRiskCount = stations.filter(s => {
    const riskData = riskType === 'flood' ? s.flood_risk : s.drought_risk;
    return riskData.probability >= 0.7;
  }).length;
  
  const alertCount = stations.filter(s => {
    const riskData = riskType === 'flood' ? s.flood_risk : s.drought_risk;
    return riskData.probability >= 0.5;
  }).length;
  
  const timeSinceUpdate = () => {
    const diff = Math.floor((Date.now() - lastUpdate.getTime()) / (1000 * 60));
    return `Hace ${diff < 1 ? 1 : diff} min`;
  };

  const stats = [
    {
      label: "Total Estaciones",
      value: stations.length,
      icon: MapPin,
      color: "text-primary",
      bgColor: "bg-primary/10"
    },
    {
      label: "Alertas Activas",
      value: alertCount,
      icon: AlertTriangle,
      color: "text-warning",
      bgColor: "bg-warning/10"
    },
    {
      label: "Riesgo Alto",
      value: highRiskCount,
      icon: TrendingUp,
      color: "text-danger",
      bgColor: "bg-danger/10"
    },
    {
      label: "Última Predicción",
      value: timeSinceUpdate(),
      icon: Clock,
      color: "text-success",
      bgColor: "bg-success/10",
      isText: true
    }
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.4 }}
      className="glass-card p-5 rounded-xl"
    >
      <h3 className="font-semibold text-foreground mb-4">Estadísticas Globales</h3>
      
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="p-3 bg-secondary/30 rounded-lg text-center"
          >
            <div className={`w-8 h-8 ${stat.bgColor} rounded-lg flex items-center justify-center mx-auto mb-2`}>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className={`text-xl font-bold ${stat.isText ? 'text-sm' : ''} text-foreground mb-1`}>
              {stat.value}
            </div>
            <div className="text-xs text-muted-foreground">{stat.label}</div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};
