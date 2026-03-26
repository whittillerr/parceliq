# ParcelIQ.ai

Parcel-level development feasibility intelligence for Charleston County, SC.

**What can I build on this parcel, what are the risks, and does it pencil?**

ParcelIQ combines a deterministic constraint solver (zoning ordinance calculations) with Claude AI intelligence to produce a complete feasibility report: development envelope, three scenarios (by-right, optimized, with variance), risk map, process timeline, and cost framing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + Tailwind)          Vercel             │
│  AnalysisForm → api/client.ts → POST /api/analyze              │
│  AnalysisResults ← AnalysisResponse                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────────┐
│  Backend (FastAPI + Python 3.11)             Railway            │
│                                                                 │
│  POST /api/analyze                                              │
│    ├─ Jurisdiction Registry (12 jurisdictions, 3 tiers)         │
│    ├─ Constraint Solver (Charleston + Mt Pleasant engines)      │
│    │    └─ Zoning data: 43 districts, 22 height districts       │
│    ├─ Claude AI (claude-sonnet-4-20250514)                      │
│    │    ├─ System prompt (tier-branching feasibility engine)     │
│    │    └─ Jurisdiction context (overlays, boards, fees)         │
│    └─ Response: envelope + scenarios + risk + timeline + cost   │
│                                                                 │
│  GET /api/health                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Tier System

| Tier | Jurisdictions | Analysis Mode |
|------|--------------|---------------|
| 1 | Charleston, Mt Pleasant | Full solver + AI (highest confidence) |
| 2 | North Charleston, Unincorporated County | AI + verified research data |
| 3 | 8 island/suburban jurisdictions | AI-only with disclaimers |

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.9+
- An Anthropic API key

### Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

# 2. Install dependencies
make install

# 3. Start both services
make dev
```

Frontend: http://localhost:5173
Backend: http://localhost:8000
API docs: http://localhost:8000/docs

### With Docker Compose

```bash
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
make docker-up
```

### Running Tests

```bash
make test          # Full test suite (78 tests)
make test-quick    # Stop on first failure
```

Tests that call the Claude API require `ANTHROPIC_API_KEY` in the environment. Without it, those tests are automatically skipped.

## Environment Variables

| Variable | Required | Where | Description |
|----------|----------|-------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Backend | Claude API key from console.anthropic.com |
| `ALLOWED_ORIGINS` | Production | Backend | Comma-separated CORS origins (e.g. `https://parceliq.ai`) |
| `VITE_API_URL` | Production | Frontend | Backend URL (e.g. `https://api.parceliq.ai`). In dev, Vite proxies `/api` to localhost:8000 |

## Deployment

### Frontend → Vercel

```bash
cd frontend

# Install Vercel CLI if needed
npm i -g vercel

# Deploy
vercel

# Set environment variable
vercel env add VITE_API_URL
# Enter your Railway backend URL (e.g. https://parceliq-backend-production.up.railway.app)
```

The `vercel.json` in `/frontend` configures the build command, output directory, and SPA rewrites.

### Backend → Railway

1. Create a new Railway project at [railway.app](https://railway.app)
2. Connect your GitHub repo, set the root directory to `/backend`
3. Railway will detect the `Dockerfile` and `railway.toml` automatically
4. Add environment variables:
   - `ANTHROPIC_API_KEY` — your Claude API key
   - `ALLOWED_ORIGINS` — your Vercel frontend URL (e.g. `https://parceliq.ai`)
5. Railway assigns a public URL — use that as `VITE_API_URL` on Vercel

The backend includes a health check at `/api/health` that Railway monitors automatically.

### Post-Deploy Checklist

- [ ] Backend health check passes: `curl https://your-backend.railway.app/api/health`
- [ ] Frontend loads at Vercel URL
- [ ] CORS: frontend can reach backend (check browser console)
- [ ] Test a real analysis: Charleston, 123 King St, MU-2, 10000 SF

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check — returns `{"status": "ok", "product": "parceliq"}` |
| `POST` | `/api/analyze` | Parcel feasibility analysis |

### POST /api/analyze

**Request:**
```json
{
  "jurisdiction": "charleston",
  "address": "123 King Street",
  "zoning_district": "MU-2",
  "height_district": "4",
  "on_peninsula": true,
  "lot_size_sf": 10000,
  "use_types": ["residential"],
  "approximate_scale": "30-40 units"
}
```

**Response:** `AnalysisResponse` with `parcel`, `envelope`, `scenarios` (3), `risk_map`, `process_timeline`, `cost_framing`, `metadata`, `confidence_tier`, `executive_summary`.

## Make Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start backend + frontend for local development |
| `make test` | Run all backend tests |
| `make test-quick` | Run tests, stop on first failure |
| `make build` | Build frontend for production |
| `make docker-up` | Start with Docker Compose |
| `make docker-down` | Stop Docker Compose |
| `make install` | Install all dependencies |
| `make clean` | Remove build artifacts |

## Tech Stack

- **Frontend:** React 18, Vite 6, Tailwind CSS 3, TypeScript 5
- **Backend:** Python 3.11, FastAPI, Pydantic 2, Anthropic SDK
- **AI:** Claude claude-sonnet-4-20250514 (temp 0.3, 4096 tokens, 3 retries)
- **Hosting:** Vercel (frontend) + Railway (backend)
