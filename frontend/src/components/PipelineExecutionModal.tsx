import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { apiService } from '../services/api';

interface Pipeline {
  id: string;
  name: string;
  description: string;
}

interface LogMessage {
  type: 'pipeline_started' | 'pipeline_log' | 'pipeline_completed' | 'pipeline_error';
  pipeline: string;
  message?: string;
  error?: string;
  status?: 'success' | 'error';
  level?: 'info' | 'error';
  timestamp: string;
}

interface PipelineExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDataUpdated?: () => void; // Callback cuando se actualicen datos (para refrescar mapa)
}

export const PipelineExecutionModal: React.FC<PipelineExecutionModalProps> = ({
  isOpen,
  onClose,
  onDataUpdated,
}) => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [useRandomData, setUseRandomData] = useState(true); // Para generate_dummy
  const [generationProgress, setGenerationProgress] = useState<any>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onDataUpdatedRef = useRef(onDataUpdated);
  
  // Mantener la referencia actualizada sin causar re-renders
  useEffect(() => {
    onDataUpdatedRef.current = onDataUpdated;
  }, [onDataUpdated]);

  // Cargar pipelines disponibles
  useEffect(() => {
    const loadPipelines = async () => {
      try {
        const data = await apiService.getAvailablePipelines();
        
        // Ordenar pipelines: "all" primero, luego el resto
        const sortedPipelines = data.pipelines.sort((a: Pipeline, b: Pipeline) => {
          if (a.id === 'all') return -1;
          if (b.id === 'all') return 1;
          return 0;
        });
        
        setPipelines(sortedPipelines);
        
        // Seleccionar "all" por defecto si existe
        const allPipeline = sortedPipelines.find((p: Pipeline) => p.id === 'all');
        if (allPipeline) {
          setSelectedPipeline(allPipeline.id);
        } else if (sortedPipelines.length > 0) {
          setSelectedPipeline(sortedPipelines[0].id);
        }
      } catch (err) {
        setError('Error cargando pipelines');
        console.error(err);
      }
    };

    if (isOpen) {
      loadPipelines();
    }
  }, [isOpen]);

  // Conectar WebSocket cuando se abre el modal
  useEffect(() => {
    if (isOpen && !wsRef.current) {
      try {
        wsRef.current = apiService.connectPipelineWebSocket(
          (message: LogMessage) => {
            setLogs((prev) => [...prev, message]);
          },
          (error) => {
            console.error('WebSocket error:', error);
            setError('Error en conexión WebSocket');
          }
        );
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
      }
    }

    return () => {
      if (wsRef.current && !isExecuting) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isOpen, isExecuting]);

  // Auto-scroll al último log
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleRunPipeline = async () => {
    if (!selectedPipeline) return;

    setIsExecuting(true);
    setLogs([]);
    setError(null);
    setGenerationProgress(null);

    try {
      // Si es generate_dummy, conectar al stream de progreso ANTES de ejecutar
      if (selectedPipeline === 'generate_dummy') {
        eventSourceRef.current = apiService.streamGenerationProgress(
          (progress) => {
            // El servidor calcula y envía el percentage, usarlo directamente
            setGenerationProgress(progress);
            
            // Si el pipeline terminó, finalizar ejecución
            if (!progress.is_running && progress.percentage === 100) {
              setTimeout(() => setIsExecuting(false), 1000);
            }
          },
          () => {
            // Callback cuando el stream termina
            console.log('Progress stream completed');
            eventSourceRef.current = null;
          },
          (error) => {
            // Callback de error
            console.error('Progress stream error:', error);
            setError(`Error en stream de progreso: ${error.message}`);
            eventSourceRef.current = null;
            setIsExecuting(false);
          }
        );
        
        // Pequeña pausa para asegurar que el SSE esté conectado
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // Ahora sí, ejecutar el pipeline
      await apiService.runPipeline(selectedPipeline, useRandomData);
      
      // Para pipelines que no son generate_dummy
      if (selectedPipeline !== 'generate_dummy') {
        setTimeout(() => setIsExecuting(false), 2000);
      }
      
      // Los logs se reciben por WebSocket
    } catch (err) {
      setError(`Error ejecutando pipeline: ${err}`);
      setIsExecuting(false);
      
      // Cerrar SSE si hubo error
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }
  };

  const handleClose = () => {
    if (!isExecuting) {
      setLogs([]);
      setError(null);
      setGenerationProgress(null);
      setSelectedPipeline(pipelines.length > 0 ? pipelines[0].id : null);
      
      // Cerrar EventSource si está activo
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      onClose();
    }
  };

  // Determinar si el pipeline terminó
  const completedLog = logs.find((log) => log.type === 'pipeline_completed');
  
  // Para generate_dummy, también considerar completado cuando el progreso llega a 100%
  const isGenerateDummyCompleted = selectedPipeline === 'generate_dummy' && 
                                   generationProgress?.percentage === 100 && 
                                   !generationProgress?.is_running;
  
  const isCompleted = !!completedLog || isGenerateDummyCompleted;
  const isSuccess = completedLog?.status === 'success' || isGenerateDummyCompleted;

  // Actualizar estado cuando el pipeline termina
  useEffect(() => {
    if (isCompleted) {
      setIsExecuting(false);
      
      // Cerrar EventSource si está activo
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      // Si el pipeline completó exitosamente, invalidar caché y actualizar datos
      if (isSuccess) {
        // Invalidar caché de estaciones para forzar actualización
        apiService.invalidateStationsCache();
        
        // Pequeño delay para asegurar que la DB se haya actualizado
        setTimeout(() => {
          if (onDataUpdatedRef.current) {
            onDataUpdatedRef.current();
          }
          // Limpiar estado de progreso después de actualizar
          if (selectedPipeline === 'generate_dummy') {
            setGenerationProgress(null);
          }
        }, 1000);
      }
    }
  }, [isCompleted, isSuccess, selectedPipeline]); // Removido onDataUpdated de las dependencias

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 z-40"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
            onClick={handleClose}
          >
            <div
              className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="bg-slate-950/50 border-b border-slate-700 p-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    {isExecuting && !isCompleted && (
                      <Loader className="w-6 h-6 animate-spin text-blue-400" />
                    )}
                    {isCompleted && isSuccess && (
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    )}
                    {isCompleted && !isSuccess && (
                      <AlertCircle className="w-6 h-6 text-red-400" />
                    )}
                    {!isExecuting && !isCompleted && (
                      <Play className="w-6 h-6 text-blue-400" />
                    )}
                    Ejecutar Pipelines
                  </h2>
                  <p className="text-sm text-slate-400 mt-1">
                    Extrae y procesa datos climáticos
                  </p>
                </div>
                {!isExecuting && (
                  <button
                    onClick={handleClose}
                    className="text-slate-400 hover:text-white transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                )}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col">
                {/* Pipeline Selection */}
                {!isExecuting && logs.length === 0 && (
                  <div className="p-6 border-b border-slate-700">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                      Selecciona un pipeline:
                    </label>
                    <div className="grid gap-3">
                      {pipelines.map((pipeline) => {
                        const isAllPipeline = pipeline.id === 'all';
                        const isDummyPipeline = pipeline.id === 'generate_dummy';
                        return (
                          <div key={pipeline.id}>
                            <label
                              className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${
                                selectedPipeline === pipeline.id
                                  ? isAllPipeline
                                    ? 'border-green-500 bg-green-500/10'
                                    : 'border-blue-500 bg-blue-500/10'
                                  : isAllPipeline
                                  ? 'border-green-600/50 bg-green-500/5 hover:border-green-500'
                                  : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                              }`}
                            >
                              <input
                                type="radio"
                                name="pipeline"
                                value={pipeline.id}
                                checked={selectedPipeline === pipeline.id}
                                onChange={(e) => setSelectedPipeline(e.target.value)}
                                className="w-4 h-4"
                              />
                              <div className="ml-3 flex-1">
                                <p className={`font-medium ${isAllPipeline ? 'text-green-400' : 'text-white'}`}>
                                  {pipeline.name}
                                  {isAllPipeline && (
                                    <span className="ml-2 px-2 py-0.5 text-xs bg-green-500/20 text-green-300 rounded">
                                      Recomendado
                                    </span>
                                  )}
                                </p>
                                <p className="text-sm text-slate-400">{pipeline.description}</p>
                              </div>
                            </label>
                            
                            {/* Switch para generate_dummy */}
                            {isDummyPipeline && selectedPipeline === pipeline.id && (
                              <div className="mt-3 ml-8 p-3 bg-slate-800/50 rounded-lg border border-slate-600">
                                <label className="flex items-center justify-between cursor-pointer">
                                  <div>
                                    <p className="text-sm font-medium text-white">Modo de generación</p>
                                    <p className="text-xs text-slate-400 mt-0.5">
                                      {useRandomData 
                                        ? 'Datos completamente aleatorios (incluye escenarios de alto riesgo)'
                                        : 'Datos basados en patrones de la base de datos actual'}
                                    </p>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={() => setUseRandomData(!useRandomData)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                      useRandomData ? 'bg-blue-500' : 'bg-slate-600'
                                    }`}
                                  >
                                    <span
                                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                        useRandomData ? 'translate-x-6' : 'translate-x-1'
                                      }`}
                                    />
                                  </button>
                                </label>
                                <div className="mt-2 text-xs text-slate-500">
                                  <span className={useRandomData ? 'text-blue-400 font-medium' : ''}>
                                    Aleatorio
                                  </span>
                                  {' / '}
                                  <span className={!useRandomData ? 'text-blue-400 font-medium' : ''}>
                                    Basado en conocimiento
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Barra de Progreso para generate_dummy */}
                {isExecuting && selectedPipeline === 'generate_dummy' && (
                  <div className="p-6 bg-slate-950/30 border-b border-slate-700/50">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-slate-300">
                          {generationProgress?.station_name || 'Iniciando...'}
                        </span>
                        <span className="text-blue-400 font-medium">
                          {generationProgress?.current_station || 0} / {generationProgress?.total_stations || 0}
                        </span>
                      </div>
                      
                      {/* Barra de progreso */}
                      <div className="relative h-3 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                          initial={{ width: '0%' }}
                          animate={{ width: `${generationProgress?.percentage || 0}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      
                      <div className="flex justify-between items-center text-xs text-slate-400">
                        <span>{Math.round(generationProgress?.percentage || 0)}% completado</span>
                        <span>{(generationProgress?.records_generated || 0).toLocaleString()} registros</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Logs - Ocultar para generate_dummy (muestra barra de progreso en su lugar) */}
                {(isExecuting || logs.length > 0) && selectedPipeline !== 'generate_dummy' && (
                  <div className="flex-1 overflow-auto bg-slate-950/30 p-4">
                    <div className="font-mono text-sm space-y-2">
                      {logs.length === 0 && isExecuting && (
                        <div className="text-slate-400">Conectando...</div>
                      )}

                      {logs.map((log, idx) => {
                        const isError = log.type === 'pipeline_error' || 
                                       (log.type === 'pipeline_completed' && log.status === 'error') ||
                                       (log.type === 'pipeline_log' && log.level === 'error');
                        
                        const isSuccess = log.type === 'pipeline_completed' && log.status === 'success';
                        const isInfo = log.type === 'pipeline_log' && (log.level === 'info' || !log.level);
                        
                        // Extraer solo el mensaje sin timestamp, códigos ANSI, etc.
                        let displayMessage = log.message || '';
                        
                        // Remover códigos ANSI de colores: [90m, [92m, [0m, etc.
                        displayMessage = displayMessage.replace(/\[\d+m/g, '');
                        
                        // Parsear y extraer solo el mensaje limpio
                        // Formato: "22:06:16 - INFO - mensaje" o "2025-12-14 22:00:52,947 - __main__ - INFO - mensaje"
                        const patterns = [
                          /\d{2}:\d{2}:\d{2} - INFO - (.+)$/,  // Formato corto
                          /\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \S+ - INFO - (.+)$/,  // Formato largo
                          /\d{2}:\d{2}:\d{2} - ERROR - (.+)$/,
                          /\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \S+ - ERROR - (.+)$/
                        ];
                        
                        for (const pattern of patterns) {
                          const match = displayMessage.match(pattern);
                          if (match) {
                            displayMessage = match[1].trim();
                            break;
                          }
                        }
                        
                        // Obtener solo la hora del timestamp del WebSocket
                        const timeOnly = new Date(log.timestamp).toLocaleTimeString('es-ES', {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        });
                        
                        return (
                          <div
                            key={idx}
                            className={`py-1 px-2 rounded text-xs ${
                              log.type === 'pipeline_started'
                                ? 'text-blue-400 bg-blue-500/10'
                                : isError
                                ? 'text-red-400 bg-red-500/10'
                                : isSuccess
                                ? 'text-green-400 bg-green-500/10 font-semibold'
                                : isInfo
                                ? 'text-slate-400'  // Gris para INFO
                                : 'text-slate-300'
                            }`}
                          >
                            <span className="text-slate-500">
                              {timeOnly}
                            </span>
                            <span className="text-slate-600"> - </span>
                            <span className={isInfo ? 'text-slate-500' : isError ? 'text-red-500' : 'text-blue-500'}>
                              {isInfo ? 'INFO' : isError ? 'ERROR' : 'LOG'}
                            </span>
                            <span className="text-slate-600"> - </span>
                            <span>
                              {log.type === 'pipeline_started' && '▶ Pipeline iniciado'}
                              {log.type === 'pipeline_log' && displayMessage}
                              {log.type === 'pipeline_completed' &&
                                (log.status === 'success'
                                  ? '✓ Pipeline completado exitosamente'
                                  : `✗ Pipeline fallido: ${log.error}`)}
                              {log.type === 'pipeline_error' && `✗ Error: ${log.error}`}
                            </span>
                          </div>
                        );
                      })}
                      <div ref={logsEndRef} />
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  <div className="bg-red-500/10 border-t border-red-500/50 p-4">
                    <p className="text-red-400 text-sm flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      {error}
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="bg-slate-950/50 border-t border-slate-700 p-6 flex justify-between gap-4">
                {!isExecuting && !isCompleted ? (
                  <>
                    <button
                      onClick={handleClose}
                      className="px-6 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleRunPipeline}
                      disabled={!selectedPipeline}
                      className="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                      <Play className="w-4 h-4" />
                      Ejecutar Pipeline
                    </button>
                  </>
                ) : isExecuting && !isCompleted ? (
                  <button
                    disabled
                    className="w-full px-6 py-2 rounded-lg bg-slate-700 text-slate-400 cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Loader className="w-4 h-4 animate-spin" />
                    Ejecutando...
                  </button>
                ) : (
                  <button
                    onClick={handleClose}
                    className="w-full px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    Cerrar
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
