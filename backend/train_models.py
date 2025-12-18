from backend.model_trainer import ModelTrainer

# Inicializar entrenador
trainer = ModelTrainer()

# Ejecutar pipeline completo: carga dataset, prepara datos, entrena y guarda modelos
metadata = trainer.train_pipeline()

print("==== METRICAS DEL ENTRENAMIENTO ====")
print(metadata)
