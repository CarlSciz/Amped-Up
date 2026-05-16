from __future__ import annotations

import math
import random

from .models import PoleRiskProfile, RiskBand, Summary
from .scoring import rank_poles, rollup_segments, score_pole


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def build_raw_poles(count: int = 96) -> list[dict]:
    random.seed(42)
    center_lat, center_lon = 42.3314, -83.0458
    materials = ["wood", "steel", "composite"]
    contexts = ["urban alley", "suburban feeder", "wetland edge", "industrial corridor", "tree-lined road"]
    poles = []

    for idx in range(count):
        circuit_num = 1 + idx // 32
        segment_num = 1 + (idx % 32) // 8
        angle = idx * 0.64
        radius = 0.025 + (idx % 16) * 0.0024
        lat = center_lat + math.sin(angle) * radius + random.uniform(-0.006, 0.006)
        lon = center_lon + math.cos(angle) * radius * 1.35 + random.uniform(-0.006, 0.006)
        material = random.choices(materials, weights=[0.72, 0.18, 0.10])[0]
        context = random.choice(contexts)
        age = random.randint(8, 69) if material == "wood" else random.randint(4, 52)
        canopy = random.randint(4, 85)
        overhang = clamp(90 - canopy + random.randint(-15, 25))
        trim_age = random.randint(1, 54)
        wind = random.randint(43, 78) + (8 if context in {"wetland edge", "tree-lined road"} else 0)
        lightning = random.randint(18, 95)
        saturation = random.randint(22, 92) + (12 if context == "wetland edge" else 0)
        erosion = random.randint(12, 86)
        slope = random.randint(0, 15)
        visual = random.randint(8, 80) + (age * 0.35 if material == "wood" else age * 0.18)

        vegetation_score = clamp((100 - canopy) * 0.38 + overhang * 0.34 + trim_age * 0.72)
        weather_score = clamp((wind - 35) * 1.15 + lightning * 0.24 + random.randint(0, 12))
        soil_score = clamp(saturation * 0.42 + erosion * 0.36 + slope * 1.8)
        imagery_score = clamp(visual)
        material_risk = {"wood": 20, "steel": 8, "composite": 4}[material]
        asset_score = clamp(age * (1.12 if material == "wood" else 0.7) + material_risk)

        thin_data = idx % 7 == 0 or context == "industrial corridor"
        poles.append(
            {
                "id": f"P-{idx + 1:04d}",
                "circuit_id": f"CIR-{circuit_num}",
                "segment_id": f"CIR-{circuit_num}-S{segment_num}",
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "age_years": age,
                "material": material,
                "install_context": context,
                "weather_score": round(weather_score, 1),
                "vegetation_score": round(vegetation_score, 1),
                "soil_score": round(soil_score, 1),
                "imagery_score": round(imagery_score, 1),
                "asset_score": round(asset_score, 1),
                "wind_gust_mph": wind,
                "lightning_density": lightning,
                "storm_exposure": round(weather_score),
                "canopy_distance_ft": canopy,
                "overhang_pct": round(overhang),
                "trim_age_months": trim_age,
                "soil_saturation": round(clamp(saturation)),
                "erosion_index": erosion,
                "slope_pct": slope,
                "visual_defect_index": round(clamp(visual)),
                "weather_proxy": thin_data and idx % 2 == 0,
                "vegetation_proxy": thin_data,
                "soil_proxy": context in {"industrial corridor", "urban alley"} and idx % 3 == 0,
                "imagery_proxy": idx % 5 == 0,
            }
        )
    return poles


POLES: list[PoleRiskProfile] = rank_poles([score_pole(raw) for raw in build_raw_poles()])
SEGMENTS = rollup_segments(POLES)


def get_summary() -> Summary:
    proxy_flags = [factor.proxy for pole in POLES for factor in pole.factors]
    return Summary(
        pole_count=len(POLES),
        circuit_count=len({pole.circuit_id for pole in POLES}),
        segment_count=len(SEGMENTS),
        average_risk=round(sum(p.risk_score for p in POLES) / len(POLES), 1),
        critical_poles=sum(1 for p in POLES if p.risk_band == RiskBand.CRITICAL),
        high_or_above_poles=sum(1 for p in POLES if p.risk_band in {RiskBand.HIGH, RiskBand.CRITICAL}),
        average_confidence=round(sum(p.confidence for p in POLES) / len(POLES), 2),
        data_proxy_rate=round(sum(proxy_flags) / len(proxy_flags), 2),
    )
