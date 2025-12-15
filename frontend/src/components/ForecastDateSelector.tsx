import React, { useState, useEffect } from 'react';
import { Calendar, CloudRain, Droplets, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiService, type ForecastSummary } from '@/services/api';

interface ForecastDateSelectorProps {
  selectedDate: string | null;
  onDateSelect: (date: string) => void;
}

export const ForecastDateSelector: React.FC<ForecastDateSelectorProps> = ({
  selectedDate,
  onDateSelect,
}) => {
  const [forecastSummary, setForecastSummary] = useState<ForecastSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadForecastSummary();
  }, []);

  const loadForecastSummary = async () => {
    setLoading(true);
    try {
      const summary = await apiService.getForecastSummary(2);
      setForecastSummary(summary);
      
      // Auto-select today if available
      if (summary.daily_summary && summary.daily_summary.length > 0 && !selectedDate) {
        onDateSelect(summary.daily_summary[0].date);
      }
    } catch (error: any) {
      console.error('Error loading forecast summary:', error);
      // No mostrar error, solo establecer pronóstico vacío
      setForecastSummary({ forecast_days: 0, total_stations: 0, daily_summary: [] });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    // Parsear fecha como hora local para evitar problemas de zona horaria
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const dateOnly = new Date(date);
    dateOnly.setHours(0, 0, 0, 0);
    
    const isToday = dateOnly.getTime() === today.getTime();
    const isTomorrow = dateOnly.getTime() === tomorrow.getTime();
    
    if (isToday) return 'Hoy';
    if (isTomorrow) return 'Mañana';
    
    return date.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' });
  };

  const getRiskBadge = (floodAlerts: number, droughtAlerts: number, totalStations: number) => {
    const floodPercentage = (floodAlerts / totalStations) * 100;
    const droughtPercentage = (droughtAlerts / totalStations) * 100;
    
    if (floodPercentage > 50 || droughtPercentage > 50) {
      return { color: 'bg-red-100 text-red-800', icon: <AlertTriangle className="w-3 h-3" /> };
    } else if (floodPercentage > 20 || droughtPercentage > 20) {
      return { color: 'bg-yellow-100 text-yellow-800', icon: <AlertTriangle className="w-3 h-3" /> };
    }
    return { color: 'bg-green-100 text-green-800', icon: null };
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Pronóstico
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500">Cargando pronósticos...</div>
        </CardContent>
      </Card>
    );
  }

  if (!forecastSummary || forecastSummary.forecast_days === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Pronóstico
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500 space-y-2">
            <p>No hay pronósticos disponibles</p>
            <p className="text-xs">
              Los pronósticos se generan automáticamente cuando seleccionas una fecha.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Pronóstico {forecastSummary.forecast_days} días
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {forecastSummary.daily_summary.map((day) => {
            const badge = getRiskBadge(day.flood_alerts, day.drought_alerts, forecastSummary.total_stations);
            const isSelected = selectedDate === day.date;
            
            return (
              <Button
                key={day.date}
                variant={isSelected ? 'default' : 'outline'}
                className={`w-full justify-start ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
                onClick={() => onDateSelect(day.date)}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    <Calendar className="w-4 h-4" />
                    <span className="font-medium">{formatDate(day.date)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {day.flood_alerts > 0 && (
                      <div className="flex items-center gap-1 text-xs">
                        <CloudRain className="w-3 h-3 text-blue-600" />
                        <span>{day.flood_alerts}</span>
                      </div>
                    )}
                    {day.drought_alerts > 0 && (
                      <div className="flex items-center gap-1 text-xs">
                        <Droplets className="w-3 h-3 text-orange-600" />
                        <span>{day.drought_alerts}</span>
                      </div>
                    )}
                    {badge.icon && (
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
                        {badge.icon}
                      </div>
                    )}
                  </div>
                </div>
              </Button>
            );
          })}
        </div>
        
        <div className="mt-4 pt-4 border-t text-xs text-gray-500 space-y-1">
          <div className="flex items-center gap-2">
            <CloudRain className="w-3 h-3 text-blue-600" />
            <span>Alertas de inundación</span>
          </div>
          <div className="flex items-center gap-2">
            <Droplets className="w-3 h-3 text-orange-600" />
            <span>Alertas de sequía</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
