from __future__ import annotations

from collections import Counter
from statistics import mean

from .models import CircuitSegment, FactorScore, PoleRiskProfile, RiskBand


WEIGHTS = {
    "weather": 0.24,
    "vegetation": 0.22,
    "soil": 0.16,
    "imagery": 0.18,
    "asset": 0.20,
}


def risk_band(score: float) -> RiskBand:
    if score >= 80:
        return RiskBand.CRITICAL
    if score >= 62:
        return RiskBand.HIGH
    if score >= 38:
        return RiskBand.MODERATE
    return RiskBand.LOW


def action_for(band: RiskBand, drivers: list[str], scope: str = "pole") -> str:
    driver = drivers[0].lower() if drivers else "field condition"
    if band == RiskBand.CRITICAL:
        return f"Dispatch inspection within 7 days; mitigate {driver} exposure."
    if band == RiskBand.HIGH:
        return f"Prioritize in next maintenance cycle; validate {driver} assumptions."
    if band == RiskBand.MODERATE:
        return f"Monitor and refresh datasets after next storm season for this {scope}."
    return f"Keep on routine patrol cadence for this {scope}."


def score_pole(raw: dict) -> PoleRiskProfile:
    factors = [
        FactorScore(
            name="weather",
            score=raw["weather_score"],
            weight=WEIGHTS["weather"],
            contribution=raw["weather_score"] * WEIGHTS["weather"],
            evidence=f"{raw['wind_gust_mph']} mph gust proxy, {raw['lightning_density']} lightning-density index, storm exposure {raw['storm_exposure']}/100.",
            proxy=raw["weather_proxy"],
        ),
        FactorScore(
            name="vegetation",
            score=raw["vegetation_score"],
            weight=WEIGHTS["vegetation"],
            contribution=raw["vegetation_score"] * WEIGHTS["vegetation"],
            evidence=f"Canopy proximity {raw['canopy_distance_ft']} ft, overhang {raw['overhang_pct']}%, trim recency {raw['trim_age_months']} months.",
            proxy=raw["vegetation_proxy"],
        ),
        FactorScore(
            name="soil",
            score=raw["soil_score"],
            weight=WEIGHTS["soil"],
            contribution=raw["soil_score"] * WEIGHTS["soil"],
            evidence=f"Soil saturation {raw['soil_saturation']}/100, erosion susceptibility {raw['erosion_index']}/100, slope {raw['slope_pct']}%.",
            proxy=raw["soil_proxy"],
        ),
        FactorScore(
            name="imagery",
            score=raw["imagery_score"],
            weight=WEIGHTS["imagery"],
            contribution=raw["imagery_score"] * WEIGHTS["imagery"],
            evidence=f"Leaning/visible-defect proxy {raw['visual_defect_index']}/100 from inspection imagery assumptions.",
            proxy=raw["imagery_proxy"],
        ),
        FactorScore(
            name="asset",
            score=raw["asset_score"],
            weight=WEIGHTS["asset"],
            contribution=raw["asset_score"] * WEIGHTS["asset"],
            evidence=f"{raw['material'].title()} pole age {raw['age_years']} years in {raw['install_context']} context.",
            proxy=False,
        ),
    ]
    score = round(sum(f.contribution for f in factors), 1)
    band = risk_band(score)
    proxy_count = sum(1 for f in factors if f.proxy)
    data_quality = round(1 - proxy_count / len(factors), 2)
    confidence = round(0.58 + (data_quality * 0.32) - min(0.08, abs(score - 60) / 1000), 2)
    top_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)[:3]
    top_drivers = [f.name for f in top_factors]

    return PoleRiskProfile(
        id=raw["id"],
        circuit_id=raw["circuit_id"],
        segment_id=raw["segment_id"],
        location={"lat": raw["lat"], "lon": raw["lon"]},
        age_years=raw["age_years"],
        material=raw["material"],
        install_context=raw["install_context"],
        risk_score=score,
        risk_band=band,
        confidence=max(0.35, min(confidence, 0.95)),
        priority_rank=0,
        data_quality=data_quality,
        top_drivers=top_drivers,
        factors=factors,
        recommended_action=action_for(band, top_drivers),
    )


def rank_poles(poles: list[PoleRiskProfile]) -> list[PoleRiskProfile]:
    ranked = sorted(poles, key=lambda p: (p.risk_score, p.confidence), reverse=True)
    for index, pole in enumerate(ranked, start=1):
        pole.priority_rank = index
    return sorted(ranked, key=lambda p: p.id)


def rollup_segments(poles: list[PoleRiskProfile]) -> list[CircuitSegment]:
    by_segment: dict[str, list[PoleRiskProfile]] = {}
    for pole in poles:
        by_segment.setdefault(pole.segment_id, []).append(pole)

    segments = []
    for segment_id, segment_poles in by_segment.items():
        sorted_poles = sorted(segment_poles, key=lambda p: p.risk_score, reverse=True)
        score = round((mean(p.risk_score for p in segment_poles) * 0.72) + (sorted_poles[0].risk_score * 0.28), 1)
        drivers = [driver for pole in sorted_poles[:5] for driver in pole.top_drivers]
        top_drivers = [name for name, _ in Counter(drivers).most_common(3)]
        segments.append(
            CircuitSegment(
                id=segment_id,
                circuit_id=segment_poles[0].circuit_id,
                name=f"{segment_poles[0].circuit_id} / Segment {segment_id.split('-')[-1]}",
                pole_ids=[p.id for p in sorted_poles],
                centroid={
                    "lat": round(mean(p.location.lat for p in segment_poles), 5),
                    "lon": round(mean(p.location.lon for p in segment_poles), 5),
                },
                risk_score=score,
                risk_band=risk_band(score),
                confidence=round(mean(p.confidence for p in segment_poles), 2),
                pole_count=len(segment_poles),
                critical_poles=sum(1 for p in segment_poles if p.risk_band == RiskBand.CRITICAL),
                top_drivers=top_drivers,
                recommended_action=action_for(risk_band(score), top_drivers, "segment"),
            )
        )
    return sorted(segments, key=lambda s: s.risk_score, reverse=True)
