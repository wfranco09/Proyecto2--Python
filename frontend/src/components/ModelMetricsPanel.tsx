import { useState } from "react";
import { ModelMetrics } from "@/data/mockStations";
import { Button } from "@/components/ui/button";
import { Cpu, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Progress } from "@/components/ui/progress";

interface ModelMetricsPanelProps {
  metrics: ModelMetrics;
}

export const ModelMetricsPanel = ({ metrics }: ModelMetricsPanelProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const featureEntries = Object.entries(metrics.feature_importances).sort((a, b) => b[1] - a[1]);
  
  const lastTrained = new Date(metrics.last_trained);
  const timeAgo = Math.floor((Date.now() - lastTrained.getTime()) / (1000 * 60 * 60));
  
  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card rounded-xl overflow-hidden"
    >
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 flex items-center justify-between hover:bg-secondary/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Performance del Modelo</h3>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-5 h-5 text-muted-foreground" />
        )}
      </button>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="px-5 pb-5"
          >
            {/* Accuracy and AUC */}
            <div className="grid grid-cols-2 gap-4 mb-5">
              <div className="text-center p-3 bg-secondary/30 rounded-lg">
                <div className="relative w-16 h-16 mx-auto mb-2">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      fill="none"
                      stroke="hsl(var(--secondary))"
                      strokeWidth="4"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      fill="none"
                      stroke="hsl(var(--success))"
                      strokeWidth="4"
                      strokeDasharray={`${metrics.accuracy * 176} 176`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-success">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Accuracy</p>
              </div>
              
              <div className="text-center p-3 bg-secondary/30 rounded-lg">
                <div className="relative w-16 h-16 mx-auto mb-2">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      fill="none"
                      stroke="hsl(var(--secondary))"
                      strokeWidth="4"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      fill="none"
                      stroke="hsl(var(--primary))"
                      strokeWidth="4"
                      strokeDasharray={`${metrics.auc * 176} 176`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-primary">
                    {metrics.auc.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">AUC-ROC</p>
              </div>
            </div>
            
            {/* Feature Importances */}
            <div className="mb-4">
              <h4 className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wide">
                Importancia de Variables
              </h4>
              <div className="space-y-3">
                {featureEntries.map(([feature, importance], index) => (
                  <motion.div 
                    key={feature}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-foreground">{feature}</span>
                      <span className="text-xs text-muted-foreground">
                        {(importance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 bg-secondary/50 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${importance * 100}%` }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                        className={`h-full rounded-full ${
                          index === 0 ? 'bg-primary' : 
                          index === 1 ? 'bg-success' : 
                          index === 2 ? 'bg-warning' : 'bg-muted-foreground'
                        }`}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
            
            {/* Model Info */}
            <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border/50">
              <span>Modelo: {metrics.model}</span>
              <span>Actualizado hace {timeAgo}h</span>
            </div>
            
            <Button 
              variant="ghost" 
              className="w-full mt-3 text-xs text-primary hover:bg-primary/10"
            >
              <ExternalLink className="w-3 h-3 mr-2" />
              Ver métricas detalladas
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
