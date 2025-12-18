from backend.model_trainer import ModelTrainer
import pandas as pd

# Inicializar el modelo (carga los modelos entrenados)
trainer = ModelTrainer()
trainer.train_pipeline()  # opcional si aún no entrenaste; si ya entrenaste, puedes omitir

# Función para predecir riesgos
def predict_risks(sample):
    """
    sample: dict con keys = FEATURE_COLUMNS
    retorna dict con riesgos de flood y drought
    """
    X = pd.DataFrame([sample])
    risks = {}
    
    if "flood" in trainer.models:
        risks["flood"] = float(trainer.models["flood"].predict_proba(X)[:, 1][0])
    if "drought" in trainer.models:
        risks["drought"] = float(trainer.models["drought"].predict_proba(X)[:, 1][0])
    
    return risks

# Ejemplo de uso
sample_input = {
    "TEMP": 30.5,
    "HUMEDAD": 80.0,
    "VIENTO": 5.2,
    "elevation_m": 50,
    "LLUVIA": 12.0
}

risks = predict_risks(sample_input)
print("==== RIESGOS ====")
print(risks)
