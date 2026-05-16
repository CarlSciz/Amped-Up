from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .data import POLES, SEGMENTS, get_summary
from .models import CircuitSegment, PoleRiskProfile, RiskBand, Summary

app = FastAPI(title="Utility Pole Risk Profiler", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/summary", response_model=Summary)
def summary() -> Summary:
    return get_summary()


@app.get("/api/poles", response_model=list[PoleRiskProfile])
def poles(
    circuit: str | None = None,
    segment: str | None = None,
    min_score: float = Query(0, ge=0, le=100),
    band: RiskBand | None = None,
    driver: str | None = None,
) -> list[PoleRiskProfile]:
    results = POLES
    if circuit:
        results = [pole for pole in results if pole.circuit_id == circuit]
    if segment:
        results = [pole for pole in results if pole.segment_id == segment]
    if band:
        results = [pole for pole in results if pole.risk_band == band]
    if driver:
        results = [pole for pole in results if driver.lower() in pole.top_drivers]
    return sorted([pole for pole in results if pole.risk_score >= min_score], key=lambda p: p.priority_rank)


@app.get("/api/poles/{pole_id}", response_model=PoleRiskProfile)
def pole_detail(pole_id: str) -> PoleRiskProfile:
    for pole in POLES:
        if pole.id == pole_id:
            return pole
    raise HTTPException(status_code=404, detail="Pole not found")


@app.get("/api/circuits", response_model=list[CircuitSegment])
def circuits(
    circuit: str | None = None,
    min_score: float = Query(0, ge=0, le=100),
    band: RiskBand | None = None,
) -> list[CircuitSegment]:
    results = SEGMENTS
    if circuit:
        results = [segment for segment in results if segment.circuit_id == circuit]
    if band:
        results = [segment for segment in results if segment.risk_band == band]
    return [segment for segment in results if segment.risk_score >= min_score]
