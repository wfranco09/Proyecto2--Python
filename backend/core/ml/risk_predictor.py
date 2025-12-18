"""
Módulo de Machine Learning para predicción de riesgo climático
Entrena DOS modelos RandomForestRegressor (inundación y sequía) usando datos históricos
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from core.database.raindrop_db import get_data_by_date_range
from core.analysis.risk_analyzer import RiskAnalyzer, RiskLevel

logger = logging.getLogger(__name__)

# Directorio para guardar modelos
MODELS_DIR = Path(__file__).parent.parent.parent / "ml_models"
MODELS_DIR.mkdir(exist_ok=True)


class RiskPredictor:
    """
    Predictor de riesgo climático usando RandomForest.
    Entrena DOS modelos separados:
    - Modelo de riesgo de inundación (flood_risk: 0.0-1.0)
    - Modelo de riesgo de sequía (drought_risk: 0.0-1.0)
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Inicializa el predictor.
        
        Args:
            model_path: Ruta al modelo guardado (opcional)
        """
        self.flood_model = None
        self.drought_model = None
        self.feature_names = [
            'temperature', 'humidity', 'precipitation_total',
            'wind_speed', 'pressure',
            'temp_change', 'humidity_change', 'precip_change',
            'wind_change', 'pressure_change'
        ]
        self.reverse_mapping = {v: k for k, v in self.label_mapping.items()}
        
        if model_path and model_path.exists():
            self.load_model(model_path)
    
    def prepare_training_data(
        self, 
        min_samples: int = 1000
    ) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepara datos de entrenamiento desde TODA la base de datos histórica (5 años).
        Calcula riesgo de inundación y sequía como valores float (0.0-1.0).
        
        Args:
            min_samples: Mínimo de muestras requeridas
            
        Returns:
            Tuple con features (X), flood_risk (y_flood), drought_risk (y_drought)
        """
        logger.info(f"📚 Preparando datos de entrenamiento (TODOS los datos históricos)...")
        
        # NO usar days_back - obtener TODOS los datos históricos disponibles
        end_date = datetime.now(timezone.utc)
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)  # Desde inicio de datos
        
        all_data = []
        analyzer = RiskAnalyzer()
        
        # Obtener todas las estaciones desde la DB
        from core.database.raindrop_db import get_all_stations
        stations = get_all_stations()
        logger.info(f"📊 Entrenando con datos de {len(stations)} estaciones")
        
        # Recopilar datos de todas las estaciones
        for station in stations:
            station_id = station['id']
            try:
                station_data = get_data_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    station_id=station_id
                )
                
                if len(station_data) < 3:  # Necesitamos al menos 3 registros para calcular cambios
                    continue
                
                # Convertirir a DataFrame para facilitar cálculos
                df = pd.DataFrame(station_data)
                
                # Limpiar valores None antes de calcular cambios
                # Reemplazar None con el valor anterior o con 0 si no hay valor anterior
                numeric_columns = ['temperature', 'humidity', 'precipitation_total', 'wind_speed', 'pressure']
                for col in numeric_columns:
                    if col in df.columns:
                        # Convertir a numeric primero para evitar warnings de downcasting
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        # Forward fill primero (usar valor anterior), luego backward fill, finalmente 0
                        df[col] = df[col].ffill().bfill().fillna(0)
                
                # Calcular cambios (tendencias)
                df['temp_change'] = df['temperature'].diff().fillna(0)
                df['humidity_change'] = df['humidity'].diff().fillna(0)
                df['precip_change'] = df['precipitation_total'].diff().fillna(0)
                df['wind_change'] = df['wind_speed'].diff().fillna(0)
                df['pressure_change'] = df['pressure'].diff().fillna(0)
                
                # Calcular riesgos de inundación y sequía para cada registro
                for idx, row in df.iterrows():
                    flood_risk, drought_risk = self._calculate_historical_risks(row)
                    df.at[idx, 'flood_risk'] = flood_risk
                    df.at[idx, 'drought_risk'] = drought_risk
                
                all_data.append(df)
                
            except Exception as e:
                logger.warning(f"Error obteniendo datos de estación {station_id}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No hay datos suficientes para entrenamiento")
        
        # Combinar todos los datos
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Eliminar filas con valores nulos en features críticos
        combined_df = combined_df.dropna(subset=self.feature_names + ['flood_risk', 'drought_risk'])
        
        if len(combined_df) < min_samples:
            raise ValueError(f"Solo se encontraron {len(combined_df)} muestras, se necesitan al menos {min_samples}")
        
        # Separar features y labels (dos targets: flood y drought)
        X = combined_df[self.feature_names]
        y_flood = combined_df['flood_risk']
        y_drought = combined_df['drought_risk']
        
        logger.info(f"✅ Datos preparados: {len(X):,} muestras, {len(X.columns)} features")
        logger.info(f"📊 Rango flood_risk: {y_flood.min():.3f} - {y_flood.max():.3f} (media: {y_flood.mean():.3f})")
        logger.info(f"📊 Rango drought_risk: {y_drought.min():.3f} - {y_drought.max():.3f} (media: {y_drought.mean():.3f})")
        
        return X, y_flood, y_drought
    
    def _calculate_historical_risks(self, row: pd.Series) -> Tuple[float, float]:
        """
        Calcula los niveles de riesgo de inundación y sequía basado en condiciones meteorológicas.
        
        Args:
            row: Serie de pandas con los datos meteorológicos
            
        Returns:
            Tuple[float, float]: (flood_risk, drought_risk) en rango [0.0, 1.0]
        """
        # ===== FLOOD RISK CALCULATION =====
        flood_score = 0.0
        
        # Precipitación (peso: 40%)
        precip = row.get('precipitation_total', 0)
        if precip > 50:
            flood_score += 0.40
        elif precip > 25:
            flood_score += 0.30
        elif precip > 10:
            flood_score += 0.15
        elif precip > 5:
            flood_score += 0.05
        
        # Humedad alta (peso: 20%)
        humidity = row.get('humidity', 0)
        if humidity > 90:
            flood_score += 0.20
        elif humidity > 85:
            flood_score += 0.15
        elif humidity > 75:
            flood_score += 0.10
        
        # Presión baja indica tormentas (peso: 20%)
        pressure = row.get('pressure', 1013)
        if pressure < 1000:
            flood_score += 0.20
        elif pressure < 1005:
            flood_score += 0.15
        elif pressure < 1010:
            flood_score += 0.08
        
        # Viento fuerte (peso: 10%)
        wind = row.get('wind_speed', 0)
        if wind > 50:
            flood_score += 0.10
        elif wind > 30:
            flood_score += 0.05
        
        # Temperatura (peso: 10% - tormentas tropicales)
        temp = row.get('temperature', 0)
        if 25 <= temp <= 35:
            flood_score += 0.10
        elif 20 <= temp < 25:
            flood_score += 0.05
        
        # Limitar a [0.0, 1.0]
        flood_risk = min(flood_score, 1.0)
        
        # ===== DROUGHT RISK CALCULATION =====
        drought_score = 0.0
        
        # Precipitación baja (peso: 40%)
        if precip < 1:
            drought_score += 0.40
        elif precip < 2:
            drought_score += 0.30
        elif precip < 5:
            drought_score += 0.15
        
        # Humedad baja (peso: 25%)
        if humidity < 30:
            drought_score += 0.25
        elif humidity < 40:
            drought_score += 0.20
        elif humidity < 50:
            drought_score += 0.10
        
        # Temperatura alta (peso: 20%)
        if temp > 38:
            drought_score += 0.20
        elif temp > 35:
            drought_score += 0.15
        elif temp > 32:
            drought_score += 0.10
        
        # Presión alta (peso: 15% - sistema anticiclónico)
        if pressure > 1020:
            drought_score += 0.15
        elif pressure > 1015:
            drought_score += 0.10
        elif pressure > 1013:
            drought_score += 0.05
        
        # Limitar a [0.0, 1.0]
        drought_risk = min(drought_score, 1.0)
        
        return flood_risk, drought_risk
    
    def train(
        self, 
        days_back: int = 7,
        test_size: float = 0.2,
        random_state: int = 42,
        use_incidents: bool = True
    ) -> Dict:
        """
        Entrena los dos modelos de regresión (flood y drought).
        
        Args:
            days_back: Días de datos históricos (ignorado si use_incidents=True)
            test_size: Proporción de datos para testing
            random_state: Semilla para reproducibilidad
            use_incidents: Si True, usa datos REALES de incident_reports (prioridad)
            
        Returns:
            Métricas de entrenamiento para ambos modelos
        """
        logger.info("🚀 Iniciando entrenamiento de DUAL MODELS (flood + drought)...")
        start_time = datetime.now()
        
        # Preparar datos: PRIORIDAD a incidentes reales
        if use_incidents:
            try:
                from core.ml.incident_correlation import get_combined_training_data
                X, y_flood, y_drought = get_combined_training_data(use_incidents=True)
                logger.info("✅ Usando datos de incidentes REALES reportados por usuarios")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando incidentes, usando datos sintéticos: {e}")
                X, y_flood, y_drought = self.prepare_training_data(days_back=days_back)
        else:
            # Método sintético original
            X, y_flood, y_drought = self.prepare_training_data(days_back=days_back)
        
        # Dividir entrenamiento/prueba
        X_train, X_test, y_flood_train, y_flood_test, y_drought_train, y_drought_test = train_test_split(
            X, y_flood, y_drought, test_size=test_size, random_state=random_state
        )
        
        logger.info(f"📊 Train: {len(X_train):,} muestras | Test: {len(X_test):,} muestras")
        
        # ===== ENTRENAR MODELO DE FLOOD =====
        logger.info("🌊 Entrenando modelo de FLOOD...")
        self.flood_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )
        self.flood_model.fit(X_train, y_flood_train)
        
        # Evaluar flood model
        y_flood_pred = self.flood_model.predict(X_test)
        flood_mse = mean_squared_error(y_flood_test, y_flood_pred)
        flood_mae = mean_absolute_error(y_flood_test, y_flood_pred)
        flood_r2 = r2_score(y_flood_test, y_flood_pred)
        
        # ===== ENTRENAR MODELO DE DROUGHT =====
        logger.info("☀️ Entrenando modelo de DROUGHT...")
        self.drought_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )
        self.drought_model.fit(X_train, y_drought_train)
        
        # Evaluar drought model
        y_drought_pred = self.drought_model.predict(X_test)
        drought_mse = mean_squared_error(y_drought_test, y_drought_pred)
        drought_mae = mean_absolute_error(y_drought_test, y_drought_pred)
        drought_r2 = r2_score(y_drought_test, y_drought_pred)
        
        # Importancia de características para cada modelo
        flood_importance = dict(zip(self.feature_names, self.flood_model.feature_importances_))
        drought_importance = dict(zip(self.feature_names, self.drought_model.feature_importances_))
        
        sorted_flood = sorted(flood_importance.items(), key=lambda x: x[1], reverse=True)
        sorted_drought = sorted(drought_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Calcular tiempo de entrenamiento
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Log de resultados
        logger.info(f"✅ Entrenamiento completado en {training_time:.2f}s")
        logger.info(f"\n🌊 FLOOD MODEL:")
        logger.info(f"   MSE: {flood_mse:.4f} | MAE: {flood_mae:.4f} | R²: {flood_r2:.4f}")
        logger.info(f"   Top 3 features:")
        for feature, importance in sorted_flood[:3]:
            logger.info(f"     {feature}: {importance:.3f}")
        
        logger.info(f"\n☀️ DROUGHT MODEL:")
        logger.info(f"   MSE: {drought_mse:.4f} | MAE: {drought_mae:.4f} | R²: {drought_r2:.4f}")
        logger.info(f"   Top 3 features:")
        for feature, importance in sorted_drought[:3]:
            logger.info(f"     {feature}: {importance:.3f}")
        
        # Detectar si usamos datos reales o sintéticos
        data_source = "real_incidents" if use_incidents and len(X) > 0 else "synthetic"
        
        metrics = {
            'training_time': training_time,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'data_source': data_source,
            'flood_model': {
                'mse': flood_mse,
                'mae': flood_mae,
                'r2': flood_r2,
                'feature_importance': flood_importance
            },
            'drought_model': {
                'mse': drought_mse,
                'mae': drought_mae,
                'r2': drought_r2,
                'feature_importance': drought_importance
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Guardar modelo
        self.save_model()
        
        return metrics
    
    def predict(self, features: Dict) -> Dict:
        """
        Predice los niveles de riesgo de inundación y sequía para nuevas features.
        
        Args:
            features: Diccionario con features meteorológicas
            
        Returns:
            Dict con flood_risk y drought_risk (floats 0.0-1.0)
        """
        if self.flood_model is None or self.drought_model is None:
            raise ValueError("Modelos no entrenados. Llama a train() primero.")
        
        # Preparar features como DataFrame con nombres de columnas (igual que en el entrenamiento)
        X = pd.DataFrame([{
            'temperature': features.get('temperature', 0),
            'humidity': features.get('humidity', 0),
            'precipitation_total': features.get('precipitation_total', 0),
            'wind_speed': features.get('wind_speed', 0),
            'pressure': features.get('pressure', 1013),
            'temp_change': features.get('temp_change', 0),
            'humidity_change': features.get('humidity_change', 0),
            'precip_change': features.get('precip_change', 0),
            'wind_change': features.get('wind_change', 0),
            'pressure_change': features.get('pressure_change', 0)
        }], columns=self.feature_names)
        
        # Predecir con ambos modelos
        flood_risk = float(self.flood_model.predict(X)[0])
        drought_risk = float(self.drought_model.predict(X)[0])
        
        # Asegurar que estén en el rango [0.0, 1.0]
        flood_risk = max(0.0, min(1.0, flood_risk))
        drought_risk = max(0.0, min(1.0, drought_risk))
        
        return {
            'flood_risk': flood_risk,
            'drought_risk': drought_risk
        }
    
    def predict_from_forecast(self, forecast_data: Dict) -> Dict:
        """
        Predice riesgo de inundación y sequía desde datos de pronóstico.
        Usa los modelos ML entrenados para generar predicciones precisas.
        
        Args:
            forecast_data: Datos del pronóstico con temp_avg, humidity, precipitation_total, etc.
            
        Returns:
            Diccionario con predicciones de inundación y sequía
        """
        if self.flood_model is None or self.drought_model is None:
            # Intentar cargar el modelo guardado
            model_path = MODELS_DIR / "risk_model.joblib"
            if model_path.exists():
                self.load_model(model_path)
            else:
                raise ValueError("Modelos no disponibles. Entrena los modelos primero.")
        
        # Extraer datos del pronóstico
        temp = float(forecast_data.get("temp_avg") or forecast_data.get("temperature") or 25.0)
        humidity = float(forecast_data.get("humidity") or 70.0)
        precip = float(forecast_data.get("precipitation_total") or 0.0)
        wind = float(forecast_data.get("wind_speed_max") or forecast_data.get("wind_speed") or 0.0)
        pressure = float(forecast_data.get("pressure") or 1013.0)
        
        # Para pronóstico, los cambios los estimamos comparando con promedios típicos
        temp_change = temp - 27.0  # Promedio típico de Panamá
        humidity_change = humidity - 75.0
        precip_change = precip - 5.0
        wind_change = wind - 10.0
        pressure_change = pressure - 1013.0
        
        # Preparar features
        features = {
            'temperature': temp,
            'humidity': humidity,
            'precipitation_total': precip,
            'wind_speed': wind,
            'pressure': pressure,
            'temp_change': temp_change,
            'humidity_change': humidity_change,
            'precip_change': precip_change,
            'wind_change': wind_change,
            'pressure_change': pressure_change
        }
        
        # Predecir con ambos modelos
        predictions = self.predict(features)
        flood_risk = predictions['flood_risk']
        drought_risk = predictions['drought_risk']
        
        # Determinar niveles categóricos para compatibilidad
        flood_level = self._get_risk_level_from_prob(flood_risk)
        drought_level = self._get_risk_level_from_prob(drought_risk)
        
        return {
            "flood_risk": {
                "probability": round(flood_risk, 3),
                "level": flood_level,
                "alert": flood_risk >= 0.5,
                "confidence": round(flood_risk, 3)  # En regresión, la predicción es la confianza
            },
            "drought_risk": {
                "probability": round(drought_risk, 3),
                "level": drought_level,
                "alert": drought_risk >= 0.5,
                "confidence": round(drought_risk, 3)
            },
            "conditions": {
                "temperature": temp,
                "humidity": humidity,
                "rainfall": precip,
                "wind_speed": wind,
                "pressure": pressure
            },
            "ml_prediction": {
                "risk_level": risk_level,
                "confidence": round(confidence, 3)
            }
        }
    
    def _get_risk_level_from_prob(self, probability: float) -> str:
        """Convierte probabilidad a nivel de riesgo (GREEN/YELLOW/RED)"""
        if probability >= 0.7:
            return "RED"
        elif probability >= 0.5:
            return "YELLOW"
        else:
            return "GREEN"
    
    def save_model(self, filename: str = "risk_model.joblib"):
        """Guarda los modelos entrenados (flood + drought)"""
        if self.flood_model is None or self.drought_model is None:
            raise ValueError("No hay modelos para guardar")
        
        model_path = MODELS_DIR / filename
        
        model_data = {
            'flood_model': self.flood_model,
            'drought_model': self.drought_model,
            'feature_names': self.feature_names,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"💾 Modelos guardados en: {model_path}")
    
    def load_model(self, model_path: Path):
        """Carga los modelos guardados"""
        try:
            model_data = joblib.load(model_path)
            self.flood_model = model_data['flood_model']
            self.drought_model = model_data['drought_model']
            self.feature_names = model_data['feature_names']
            logger.info(f"📦 Modelos cargados desde: {model_path}")
        except Exception as e:
            logger.error(f"❌ Error cargando modelos: {e}")
            raise


def train_model_from_history(days_back: int = 7) -> Dict:
    """
    Función auxiliar para entrenar modelo desde datos históricos.
    
    Args:
        days_back: Días de histórico para entrenamiento
        
    Returns:
        Métricas de entrenamiento
    """
    predictor = RiskPredictor()
    metrics = predictor.train(days_back=days_back)
    return metrics


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🌧️  Entrenando modelos de predicción de riesgo climático (FLOOD + DROUGHT)\n")
    
    try:
        predictor = RiskPredictor()
        metrics = predictor.train(days_back=7)  # Ignora days_back, usa todos los datos
        
        print(f"\n✅ Entrenamiento exitoso!")
        print(f"⏱️  Tiempo: {metrics['training_time']:.2f}s")
        print(f"📊 Muestras entrenamiento: {metrics['train_samples']:,}")
        print(f"\n🌊 FLOOD MODEL:")
        print(f"   R²: {metrics['flood_model']['r2']:.4f}")
        print(f"   MAE: {metrics['flood_model']['mae']:.4f}")
        print(f"\n☀️ DROUGHT MODEL:")
        print(f"   R²: {metrics['drought_model']['r2']:.4f}")
        print(f"   MAE: {metrics['drought_model']['mae']:.4f}")
        print(f"\n💾 Modelos guardados en: {MODELS_DIR}/risk_model.joblib")
        
    except Exception as e:
        print(f"\n❌ Error durante entrenamiento: {e}")
        import traceback
        traceback.print_exc()
