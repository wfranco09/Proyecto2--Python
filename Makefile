.PHONY: help install install-backend install-frontend dev backend frontend clean

help:
	@echo "rAIndrop - Predicción de Riesgos Climáticos en Panamá"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make install           - Instalar dependencias (backend + frontend)"
	@echo "  make install-backend   - Instalar solo dependencias del backend (uv)"
	@echo "  make install-frontend  - Instalar solo dependencias del frontend (npm)"
	@echo "  make backend           - Ejecutar backend con uv (FastAPI en puerto 8000)"
	@echo "  make frontend          - Ejecutar frontend con npm (Vite en puerto 3000)"
	@echo "  make dev               - Ejecutar backend + frontend en paralelo"
	@echo "  make clean             - Limpiar caché y archivos temporales"
	@echo ""

install: install-backend install-frontend
	@echo "✅ Todas las dependencias instaladas"

install-backend:
	@echo "📦 Instalando backend..."
	cd backend && uv sync

install-frontend:
	@echo "📦 Instalando frontend..."
	cd frontend && pnpm install

backend:
	@echo "🚀 Iniciando Backend (FastAPI)..."
	uv run -w backend python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "🚀 Iniciando Frontend (Vite)..."
	cd frontend && pnpm run dev

dev:
	@echo "🚀 Iniciando Frontend + Backend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@(cd frontend && npm run dev) & \
	uv run -w backend python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf node_modules dist .next 2>/dev/null || true
	@echo "✅ Limpieza completada"
