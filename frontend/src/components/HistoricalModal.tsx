import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { generateHistoricalData, HistoricalData } from "@/data/mockStations";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { useMemo } from "react";
import { TrendingUp, Table, MapPin } from "lucide-react";
import { Station } from "@/services/api";

interface HistoricalModalProps {
  station: Station | null;
  isOpen: boolean;
  onClose: () => void;
  riskType: 'flood' | 'drought';
}

export const HistoricalModal = ({ station, isOpen, onClose, riskType }: HistoricalModalProps) => {
  const historicalData = useMemo(() => {
    if (!station) return [];
    return generateHistoricalData(7);
  }, [station]);
  
  const chartData = historicalData.map(d => ({
    ...d,
    time: new Date(d.timestamp).toLocaleDateString('es-PA', { 
      day: '2-digit', 
      month: 'short',
      hour: '2-digit'
    }),
    risk: d.flood_proba * 100
  }));
  
  const stats = useMemo(() => {
    if (historicalData.length === 0) return null;
    
    const temps = historicalData.map(d => d.temp);
    const humidities = historicalData.map(d => d.humidity);
    const rainfalls = historicalData.map(d => d.rainfall);
    
    return {
      temp: {
        min: Math.min(...temps).toFixed(1),
        max: Math.max(...temps).toFixed(1),
        avg: (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1)
      },
      humidity: {
        min: Math.min(...humidities).toFixed(0),
        max: Math.max(...humidities).toFixed(0),
        avg: (humidities.reduce((a, b) => a + b, 0) / humidities.length).toFixed(0)
      },
      rainfall: {
        min: Math.min(...rainfalls).toFixed(1),
        max: Math.max(...rainfalls).toFixed(1),
        avg: (rainfalls.reduce((a, b) => a + b, 0) / rainfalls.length).toFixed(1)
      }
    };
  }, [historicalData]);

  if (!station) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl glass-card border-border/50 text-foreground">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-xl">{station.name}</span>
            <span className="text-sm text-muted-foreground">({station.id})</span>
          </DialogTitle>
        </DialogHeader>
        
        <Tabs defaultValue="chart" className="w-full">
          <TabsList className="w-full bg-secondary/30 mb-4">
            <TabsTrigger value="chart" className="flex-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <TrendingUp className="w-4 h-4 mr-2" />
              Serie Temporal
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <Table className="w-4 h-4 mr-2" />
              Estadísticas
            </TabsTrigger>
            <TabsTrigger value="context" className="flex-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              <MapPin className="w-4 h-4 mr-2" />
              Contexto
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="chart" className="space-y-4">
            <div className="h-[200px] bg-secondary/20 rounded-lg p-4">
              <h4 className="text-sm font-medium mb-2 text-muted-foreground">Probabilidad de Riesgo (últimos 7 días)</h4>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(199 89% 48%)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(199 89% 48%)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 25%)" />
                  <XAxis dataKey="time" tick={{ fill: 'hsl(215 20% 65%)', fontSize: 10 }} />
                  <YAxis tick={{ fill: 'hsl(215 20% 65%)', fontSize: 10 }} domain={[0, 100]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(217 33% 17%)', 
                      border: '1px solid hsl(217 33% 25%)',
                      borderRadius: '8px',
                      color: 'hsl(210 40% 98%)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="risk" 
                    stroke="hsl(199 89% 48%)" 
                    fill="url(#riskGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            
            <div className="h-[200px] bg-secondary/20 rounded-lg p-4">
              <h4 className="text-sm font-medium mb-2 text-muted-foreground">Variables Climáticas</h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 25%)" />
                  <XAxis dataKey="time" tick={{ fill: 'hsl(215 20% 65%)', fontSize: 10 }} />
                  <YAxis yAxisId="left" tick={{ fill: 'hsl(215 20% 65%)', fontSize: 10 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: 'hsl(215 20% 65%)', fontSize: 10 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(217 33% 17%)', 
                      border: '1px solid hsl(217 33% 25%)',
                      borderRadius: '8px',
                      color: 'hsl(210 40% 98%)'
                    }}
                  />
                  <Line yAxisId="left" type="monotone" dataKey="temp" stroke="hsl(0 84% 60%)" strokeWidth={2} dot={false} name="Temp (°C)" />
                  <Line yAxisId="right" type="monotone" dataKey="rainfall" stroke="hsl(160 84% 39%)" strokeWidth={2} dot={false} name="Lluvia (mm)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>
          
          <TabsContent value="stats">
            {stats && (
              <div className="bg-secondary/20 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left p-3 text-muted-foreground">Variable</th>
                      <th className="text-center p-3 text-muted-foreground">Mínimo</th>
                      <th className="text-center p-3 text-muted-foreground">Máximo</th>
                      <th className="text-center p-3 text-muted-foreground">Promedio</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-border/30">
                      <td className="p-3 font-medium">Temperatura (°C)</td>
                      <td className="text-center p-3 text-success">{stats.temp.min}</td>
                      <td className="text-center p-3 text-danger">{stats.temp.max}</td>
                      <td className="text-center p-3">{stats.temp.avg}</td>
                    </tr>
                    <tr className="border-b border-border/30">
                      <td className="p-3 font-medium">Humedad (%)</td>
                      <td className="text-center p-3 text-success">{stats.humidity.min}</td>
                      <td className="text-center p-3 text-danger">{stats.humidity.max}</td>
                      <td className="text-center p-3">{stats.humidity.avg}</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium">Lluvia (mm)</td>
                      <td className="text-center p-3 text-success">{stats.rainfall.min}</td>
                      <td className="text-center p-3 text-danger">{stats.rainfall.max}</td>
                      <td className="text-center p-3">{stats.rainfall.avg}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="context">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-secondary/20 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-3 text-muted-foreground">Ubicación</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="text-muted-foreground">Latitud:</span> {station.lat.toFixed(4)}</p>
                  <p><span className="text-muted-foreground">Longitud:</span> {station.lon.toFixed(4)}</p>
                  <p><span className="text-muted-foreground">Elevación:</span> {station.elevation} m</p>
                </div>
              </div>
              <div className="bg-secondary/20 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-3 text-muted-foreground">Estado de Riesgo</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="text-muted-foreground">Inundación:</span> {(station.flood_risk.probability * 100).toFixed(1)}% ({station.flood_risk.level})</p>
                  <p><span className="text-muted-foreground">Sequía:</span> {(station.drought_risk.probability * 100).toFixed(1)}% ({station.drought_risk.level})</p>
                  <p><span className="text-muted-foreground">Alertas:</span> {station.flood_risk.alert || station.drought_risk.alert ? 'Activas' : 'Ninguna'}</p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
