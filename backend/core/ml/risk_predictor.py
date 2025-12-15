"""
Módulo de Machine Learning para predicción de riesgo climático
Entrena un modelo RandomForest usando datos históricos
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from core.database.raindrop_db import get_data_by_date_range
from core.analysis.risk_analyzer import RiskAnalyzer, RiskLevel

logger = logging.getLogger(__name__)

# Directorio para guardar modelos
MODELS_DIR = Path(__file__).parent.parent.parent / "ml_models"
MODELS_DIR.mkdir(exist_ok=True)


class RiskPredictor:
    """Predictor de riesgo climático usando RandomForest"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Inicializa el predictor.
        
        Args:
            model_path: Ruta al modelo guardado (opcional)
        """
        self.model = None
        self.feature_names = [
            'temperature', 'humidity', 'precipitation_total',
            'wind_speed', 'pressure',
            'temp_change', 'humidity_change', 'precip_change',
            'wind_change', 'pressure_change'
        ]
        self.label_mapping = {
            'bajo': 0,
            'moderado': 1,
            'alto': 2,
            'critico': 3
        }
        self.reverse_mapping = {v: k for k, v in self.label_mapping.items()}
        
        if model_path and model_path.exists():
            self.load_model(model_path)
    
    def prepare_training_data(
        self, 
        days_back: int = 7,
        min_samples: int = 100
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara datos de entrenamiento desde la base de datos.
        
        Args:
            days_back: Días hacia atrás para obtener datos
            min_samples: Mínimo de muestras requeridas
            
        Returns:
            Tupla (X, y) con features y labels
        """
        logger.info(f" Preparando datos de entrenamiento (últimos {days_back} días)...")
        
        # Obtener datos históricos de todas las estaciones
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        all_data = []
        analyzer = RiskAnalyzer()
        
        # Recopilar datos de las +250 estaciones
        for station_id in range(1, 16):
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
                
                # Calcular nivel de riesgo para cada registro
                # Simulamos el análisis de riesgo para datos históricos
                for idx, row in df.iterrows():
                    # Crear análisis temporal con datos simulados
                    risk_level = self._calculate_historical_risk(row)
                    df.at[idx, 'risk_level'] = risk_level
                
                all_data.append(df)
                
            except Exception as e:
                logger.warning(f"Error obteniendo datos de estación {station_id}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No hay datos suficientes para entrenamiento")
        
        # Combinar todos los datos
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Eliminarr filas con valores nulos en features críticos
        combined_df = combined_df.dropna(subset=self.feature_names)
        
        if len(combined_df) < min_samples:
            raise ValueError(f"Solo se encontraron {len(combined_df)} muestras, se necesitan al menos {min_samples}")
        
        # Separar features y labels
        X = combined_df[self.feature_names]
        y = combined_df['risk_level'].map(self.label_mapping)
        
        logger.info(f" Datos preparados: {len(X)} muestras, {len(X.columns)} features")
        logger.info(f" Distribución de clases:")
        for level, count in combined_df['risk_level'].value_counts().items():
            logger.info(f"   {level}: {count} ({count/len(combined_df)*100:.1f}%)")
        
        return X, y
    
    def _calculate_historical_risk(self, row: pd.Series) -> str:
        """
        Calcula nivel de riesgo para un registro histórico usando umbrales.
        
        Args:
            row: Fila de datos
            
        Returns:
            Nivel de riesgo como string
        """
        scores = []
        
        # Temperatura
        temp = row.get('temperature', 0)
        if temp >= 38:
            scores.append(90)
        elif temp >= 35:
            scores.append(70)
        elif temp >= 32:
            scores.append(40)
        else:
            scores.append(0)
        
        # Humedad
        humidity = row.get('humidity', 0)
        if humidity >= 95:
            scores.append(80)
        elif humidity >= 90:
            scores.append(60)
        elif humidity < 60:
            scores.append(30)
        else:
            scores.append(0)
        
        # Precipitación
        precip = row.get('precipitation_total', 0)
        if precip >= 30:
            scores.append(95)
        elif precip >= 15:
            scores.append(75)
        elif precip >= 5:
            scores.append(50)
        elif precip > 0:
            scores.append(20)
        else:
            scores.append(0)
        
        # Viento
        wind = row.get('wind_speed', 0)
        if wind >= 60:
            scores.append(85)
        elif wind >= 40:
            scores.append(65)
        elif wind >= 20:
            scores.append(40)
        else:
            scores.append(0)
        
        # Presión
        pressure = row.get('pressure', 1013)
        if pressure <= 1005:
            scores.append(80)
        elif pressure <= 1010:
            scores.append(55)
        elif pressure < 1013:
            scores.append(30)
        else:
            scores.append(0)
        
        # Calcular score final
        max_score = max(scores) if scores else 0
        
        # Mapear a nivel de riesgo
        if max_score >= 80:
            return 'critico'
        elif max_score >= 60:
            return 'alto'
        elif max_score >= 30:
            return 'moderado'
        else:
            return 'bajo'
    
    def train(
        self, 
        days_back: int = 7,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Entrena el modelo RandomForest.
        
        Args:
            days_back: Días de datos históricos para entrenamiento
            test_size: Proporción de datos para testing
            random_state: Semilla para reproducibilidad
            
        Returns:
            Métricas de entrenamiento
        """
        logger.info(" Iniciando entrenamiento del modelo...")
        start_time = datetime.now()
        
        # Preparar datos
        X, y = self.prepare_training_data(days_back=days_back)
        
        # Dividir entrenamiento/prueba
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f" Train: {len(X_train)} muestras | Test: {len(X_test)} muestras")
        
        # Crear y entrenar modelo
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
            class_weight='balanced'  # Importante para clases desbalanceadas
        )
        
        logger.info(" Entrenando RandomForest...")
        self.model.fit(X_train, y_train)
        
        # Evaluar
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Importancia de características
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Calcular tiempo de entrenamiento
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Log de resultados
        logger.info(f" Entrenamiento completado en {training_time:.2f}s")
        logger.info(f" Accuracy: {accuracy:.2%}")
        logger.info(f" Top 5 características importantes:")
        for feature, importance in sorted_features[:5]:
            logger.info(f"   {feature}: {importance:.3f}")
        
        # Reporte detallado
        report = classification_report(
            y_test, y_pred,
            target_names=['bajo', 'moderado', 'alto', 'critico'],
            output_dict=True
        )
        
        metrics = {
            'accuracy': accuracy,
            'training_time': training_time,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_importance': feature_importance,
            'classification_report': report,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Guardar modelo
        self.save_model()
        
        return metrics
    
    def predict(self, features: Dict) -> Tuple[str, float]:
        """
        Predice el nivel de riesgo para nuevas features.
        
        Args:
            features: Diccionario con features
            
        Returns:
            Tupla (nivel_riesgo, confianza)
        """
        if self.model is None:
            raise ValueError("Modelo no entrenado. Llama a train() primero.")
        
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
        
        # Predecir
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = float(probabilities[prediction])
        
        risk_level = self.reverse_mapping[prediction]
        
        return risk_level, confidence
    
    def predict_from_forecast(self, forecast_data: Dict) -> Dict:
        """
        Predice riesgo de inundación y sequía desde datos de pronóstico.
        Usa el modelo ML entrenado para generar predicciones precisas.
        
        Args:
            forecast_data: Datos del pronóstico con temp_avg, humidity, precipitation_total, etc.
            
        Returns:
            Diccionario con predicciones de inundación y sequía
        """
        if self.model is None:
            # Intentar cargar el modelo guardado
            model_path = MODELS_DIR / "risk_model.joblib"
            if model_path.exists():
                self.load_model(model_path)
            else:
                raise ValueError("Modelo no disponible. Entrena el modelo primero.")
        
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
        
        # Predecir
        risk_level, confidence = self.predict(features)
        
        # Convertir nivel de riesgo a probabilidad y clasificación flood/drought
        # El modelo da nivel general, ahora clasificamos por tipo
        probability = confidence
        
        # Determinar si es riesgo de inundación o sequía
        # Inundación: alta precipitación y/o humedad
        flood_indicator = (precip / 50.0) * 0.7 + (humidity / 100.0) * 0.3
        # Sequía: baja precipitación y humedad
        drought_indicator = (1 - precip / 50.0) * 0.7 + (1 - humidity / 100.0) * 0.3
        
        # Calcular probabilidades específicas
        if risk_level in ['alto', 'critico']:
            flood_prob = min(0.95, flood_indicator * probability)
            drought_prob = min(0.95, drought_indicator * probability)
        elif risk_level == 'moderado':
            flood_prob = min(0.70, flood_indicator * probability)
            drought_prob = min(0.70, drought_indicator * probability)
        else:  # bajo
            flood_prob = min(0.40, flood_indicator * probability)
            drought_prob = min(0.40, drought_indicator * probability)
        
        # Determinar niveles
        flood_level = self._get_risk_level_from_prob(flood_prob)
        drought_level = self._get_risk_level_from_prob(drought_prob)
        
        return {
            "flood_risk": {
                "probability": round(flood_prob, 3),
                "level": flood_level,
                "alert": flood_prob >= 0.5,
                "confidence": round(confidence, 3)
            },
            "drought_risk": {
                "probability": round(drought_prob, 3),
                "level": drought_level,
                "alert": drought_prob >= 0.5,
                "confidence": round(confidence, 3)
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
        """Guarda el modelo entrenado"""
        if self.model is None:
            raise ValueError("No hay modelo para guardar")
        
        model_path = MODELS_DIR / filename
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'label_mapping': self.label_mapping,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f" Modelo guardado en: {model_path}")
    
    def load_model(self, model_path: Path):
        """Carga un modelo guardado"""
        try:
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.label_mapping = model_data['label_mapping']
            self.reverse_mapping = {v: k for k, v in self.label_mapping.items()}
            logger.info(f" Modelo cargado desde: {model_path}")
        except Exception as e:
            logger.error(f" Error cargando modelo: {e}")
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
    
    print(" Entrenando modelo de predicción de riesgo climático\n")
    
    try:
        predictor = RiskPredictor()
        metrics = predictor.train(days_back=7)
        
        print(f"\n Entrenamiento exitoso!")
        print(f"Accuracy: {metrics['accuracy']:.2%}")
        print(f"Tiempo: {metrics['training_time']:.2f}s")
        print(f"Modelo guardado en: {MODELS_DIR}/risk_model.joblib")
        
    except Exception as e:
        print(f"\n Error durante entrenamiento: {e}")
        import traceback
        traceback.print_exc()
