# Utility Pole Risk Profiler

Full-stack demo application for utility pole and circuit-segment risk profiling. The backend aggregates proxy weather, imagery, vegetation, soil, and geo context where direct datasets are thin, then produces explainable risk scores. The frontend visualizes those scores in a map-based dashboard with filtering and prioritization.

## Stack

- Python + FastAPI backend
- React + Vite frontend
- Deterministic generated pole/circuit dataset for local exploration

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## API

- `GET /api/summary` - portfolio-level risk and data-quality totals
- `GET /api/poles` - pole risk profiles with optional filters
- `GET /api/circuits` - circuit segment risk rollups with optional filters
- `GET /api/poles/{pole_id}` - one pole with factor explanations
