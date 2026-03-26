# ParcelIQ.ai

Parcel-level development feasibility intelligence for Charleston County, SC.

**What can I build on this parcel, what are the risks, and does it pencil?**

## Architecture

- **Frontend**: React 18 + Vite + Tailwind CSS + TypeScript
- **Backend**: Python 3.11 + FastAPI + Claude API
- **Infrastructure**: Docker Compose for local dev

## Quick Start

### With Docker Compose

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
docker compose up
```

Frontend: http://localhost:5173
Backend: http://localhost:8000

### Manual

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Parcel feasibility analysis |
