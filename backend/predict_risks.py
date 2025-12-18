from backend.model_trainer import ModelTrainer
import pandas as pd

trainer = ModelTrainer()
trainer.train_pipeline() 

sample_input = {
    "TEMP": 30.5,
    "HUMEDAD": 80.0,
    "VIENTO": 5.2,
    "elevation_m": 50,
    "LLUVIA": 12.0
}

X = pd.DataFrame([sample_input])
risks = {}
if "flood" in trainer.models:
    risks["flood"] = float(trainer.models["flood"].predict_proba(X)[:, 1][0])
if "drought" in trainer.models:
    risks["drought"] = float(trainer.models["drought"].predict_proba(X)[:, 1][0])

print(risks)
