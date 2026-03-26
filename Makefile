.PHONY: dev dev-backend dev-frontend test build clean docker-up docker-down

# --- Local development ---

dev:
	@echo "Starting backend and frontend..."
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# --- Testing ---

test:
	cd backend && python3 -m pytest -v

test-quick:
	cd backend && python3 -m pytest -v -x --tb=short

# --- Build ---

build:
	cd frontend && npm run build

build-check: build
	cd backend && python3 -m pytest -v --tb=short

# --- Docker ---

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# --- Utilities ---

clean:
	rm -rf frontend/dist frontend/node_modules/.vite
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt
