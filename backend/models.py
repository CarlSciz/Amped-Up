from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RiskBand(StrEnum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class FactorScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    weight: float
    contribution: float
    evidence: str
    proxy: bool = False


class GeoPoint(BaseModel):
    lat: float
    lon: float


class PoleRiskProfile(BaseModel):
    id: str
    circuit_id: str
    segment_id: str
    location: GeoPoint
    age_years: int
    material: Literal["wood", "steel", "composite"]
    install_context: str
    risk_score: float = Field(ge=0, le=100)
    risk_band: RiskBand
    confidence: float = Field(ge=0, le=1)
    priority_rank: int
    data_quality: float = Field(ge=0, le=1)
    top_drivers: list[str]
    factors: list[FactorScore]
    recommended_action: str


class CircuitSegment(BaseModel):
    id: str
    circuit_id: str
    name: str
    pole_ids: list[str]
    centroid: GeoPoint
    risk_score: float
    risk_band: RiskBand
    confidence: float
    pole_count: int
    critical_poles: int
    top_drivers: list[str]
    recommended_action: str


class Summary(BaseModel):
    pole_count: int
    circuit_count: int
    segment_count: int
    average_risk: float
    critical_poles: int
    high_or_above_poles: int
    average_confidence: float
    data_proxy_rate: float
