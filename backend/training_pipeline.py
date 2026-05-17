"""
Training Data Pipeline
======================
Converts the SVG exemplar dataset into fine-tuning JSONL for watsonx.ai and
a structured few-shot examples JSON for runtime prompt injection.

Usage:
    python3 -m backend.training_pipeline

Output:
    dataset/training/watsonx_finetune.jsonl   — fine-tune pairs (input/output)
    dataset/training/few_shot_examples.json   — curated examples per severity
    dataset/training/pipeline_report.json     — extraction stats
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
SVG_DIR = PROJECT_ROOT / "dataset" / "svgs" / "out"
RENDER_DIR = PROJECT_ROOT / "dataset" / "3d models" / "annotations"
TRAINING_DIR = PROJECT_ROOT / "dataset" / "training"
TRAINING_DIR.mkdir(parents=True, exist_ok=True)

# ── OSHA → app severity ───────────────────────────────────────────────────────

OSHA_TO_APP = {
    "imminent_danger":    "critical",
    "serious":            "high",
    "other_than_serious": "medium",
    "de_minimis":         "low",
    "deminimis":          "low",
    "compliant":          "low",
}

# ── NESC rule heuristics (keyword → rule) ────────────────────────────────────

KEYWORD_NESC: list[tuple[str, str]] = [
    ("vegetation",  "NESC 218"),
    ("clearance",   "NESC 232"),
    ("insulator",   "NESC 277"),
    ("guy",         "NESC 261"),
    ("lean",        "NESC 261"),
    ("crossarm",    "NESC 261"),
    ("decay",       "ANSI O5.1"),
    ("oil",         "OSHA 1910.269"),
    ("transformer", "OSHA 1910.269"),
    ("ice",         "NESC 250"),
    ("service",     "NESC 230"),
    ("safety zone", "NESC 238"),
    ("tag",         "MPSC R 460.601"),
    ("id",          "MPSC R 460.601"),
    ("railroad",    "AAR M-1004"),
]

RECOMMENDATION_MAP: dict[str, str] = {
    "imminent_danger":    "Immediate isolation and emergency repair order required",
    "serious":            "Schedule corrective action within 30 days; restrict climbing",
    "other_than_serious": "Schedule corrective action within 90 days",
    "de_minimis":         "Document and address at next scheduled maintenance visit",
}


# ── SVG parser ────────────────────────────────────────────────────────────────

def _parse_svg(path: str) -> dict[str, Any] | None:
    """Extract annotation fields from a single SVG training scene."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    fname = os.path.basename(path)

    # Severity
    sev_m = re.search(r"severity:\s*([a-z_]+)", content)
    if not sev_m:
        return None
    osha_sev = sev_m.group(1).strip()

    # Skip bare "n" (compliant with no markings) and multi_defect scenes
    # (multi-defect scenes are handled separately via their defects array)
    if osha_sev in ("n", "none"):
        return None

    # Violations
    violations = re.findall(r"violation:\s*([a-z_]+)", content)
    violations = [v for v in violations if v not in ("none", "n")]

    # Pole type from filename
    pole_m = re.match(r"([a-z]+\d+[a-z]*\d*)", fname)
    pole_type = pole_m.group(1) if pole_m else "unknown"

    # Scene description from <desc>
    desc_m = re.search(r"<desc>(.*?)</desc>", content, re.DOTALL)
    desc = (desc_m.group(1).strip() if desc_m else "").replace("\n", " ")
    # Strip the boilerplate prefix so we keep only the useful part
    desc = re.sub(r"Pole compliance training scene\.\s*", "", desc).strip()

    # NESC rules cited in the SVG text
    nesc_cited = re.findall(r"NESC\s+[\d.]+[A-Za-z]*", content)
    nesc_cited = list(dict.fromkeys(nesc_cited))[:4]

    # If no cited rules, derive from violation keywords
    if not nesc_cited:
        for kw, rule in KEYWORD_NESC:
            if kw in " ".join(violations).lower() or kw in desc.lower():
                if rule not in nesc_cited:
                    nesc_cited.append(rule)

    # Weather condition from filename pattern
    weather = None
    if "_w_" in fname or "_wmd_" in fname:
        weather_m = re.search(r"_(ice|snow|storm|summer)", fname)
        weather = weather_m.group(1) if weather_m else None

    # Multi-defect details
    multi_defects: list[dict] = []
    worst_sev = osha_sev
    if osha_sev == "multi_defect":
        # Try to extract individual defect severity items
        defect_blocks = re.findall(
            r"violation:\s*([a-z_]+).*?severity:\s*([a-z_]+)", content, re.DOTALL
        )
        multi_defects = [{"violation": v, "severity": s} for v, s in defect_blocks]
        # Determine worst severity present
        sev_order = ["de_minimis", "other_than_serious", "serious", "imminent_danger"]
        for _, s in defect_blocks:
            if s in sev_order and sev_order.index(s) > sev_order.index(worst_sev):
                worst_sev = s

    # Map to app severity
    effective_osha = worst_sev if worst_sev != "multi_defect" else "serious"
    app_severity = OSHA_TO_APP.get(effective_osha, "medium")

    # AI score heuristic
    score_base = {
        "imminent_danger":    92,
        "serious":            78,
        "other_than_serious": 58,
        "de_minimis":         42,
        "multi_defect":       80,
    }
    ai_score = score_base.get(osha_sev, 65)
    if weather:
        ai_score = min(ai_score + 5, 99)
    if len(violations) > 2:
        ai_score = min(ai_score + 3, 99)

    recommendation = RECOMMENDATION_MAP.get(effective_osha, RECOMMENDATION_MAP["other_than_serious"])

    return {
        "source_file": fname,
        "pole_type": pole_type,
        "osha_severity": osha_sev,
        "app_severity": app_severity,
        "violations": violations or (["none"] if osha_sev == "de_minimis" else ["unknown"]),
        "nesc_rules": nesc_cited,
        "weather": weather,
        "multi_defects": multi_defects,
        "description": desc,
        "ai_score": ai_score,
        "recommendation": recommendation,
    }


# ── 3-D render parser ─────────────────────────────────────────────────────────

def _parse_render_annotation(path: str) -> dict[str, Any] | None:
    """Extract scene info from a 3-D model annotation JSON."""
    with open(path) as f:
        data = json.load(f)

    scene = data.get("scene", "")
    scene_sev = data.get("scene_severity", "compliant")
    annots = data.get("annotations", [])
    violations = [a["class"] for a in annots]

    osha_map = {
        "compliant":       "de_minimis",
        "imminent_danger": "imminent_danger",
        "ice_on_conductor": "serious",
        "vegcontact":      "imminent_danger",
        "broken_arm":      "serious",
    }
    osha_sev = osha_map.get(scene_sev, osha_map.get(scene, "other_than_serious"))
    app_severity = OSHA_TO_APP.get(osha_sev, "medium")

    if not violations and osha_sev == "de_minimis":
        return None  # compliant — skip for supervised training

    fname = os.path.basename(path)
    pole_type = "sp35c5"  # PoC only covers this pole type
    angle = data.get("angle", "front")
    lighting = data.get("lighting", "noon")

    return {
        "source_file": fname,
        "pole_type": pole_type,
        "osha_severity": osha_sev,
        "app_severity": app_severity,
        "violations": violations or ["unknown"],
        "nesc_rules": [],
        "weather": None,
        "multi_defects": [],
        "description": f"Rendered {angle} view, {lighting} lighting. Scene: {scene}.",
        "ai_score": 75,
        "recommendation": RECOMMENDATION_MAP.get(osha_sev, "Review and schedule corrective action"),
    }


# ── Prompt builder ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert utility pole inspection AI. Analyze the inspection description \
and return a JSON assessment with: severity (critical/high/medium/low), violations \
(array of identifiers), osha_class, nesc_rules, recommendation, ai_score (0-100), confidence."""


def _to_finetune_pair(record: dict[str, Any]) -> dict[str, str]:
    """Convert an extracted record to a watsonx.ai fine-tune prompt/completion pair."""
    user_msg = (
        f"Pole type: {record['pole_type']}\n"
        f"Description: {record['description']}\n"
        f"Photos captured: 2"
    )
    prompt = (
        f"<|system|>\n{SYSTEM_PROMPT}\n"
        f"<|user|>\n{user_msg}\n"
        f"<|assistant|>\n"
    )
    completion = json.dumps({
        "severity":       record["app_severity"],
        "violations":     record["violations"],
        "osha_class":     record["osha_severity"],
        "nesc_rules":     record["nesc_rules"],
        "recommendation": record["recommendation"],
        "ai_score":       record["ai_score"],
        "confidence":     "high" if record["ai_score"] >= 80 else "medium",
    })
    return {"input": prompt, "output": completion}


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run() -> None:
    print("=== Amped Up · Training Data Pipeline ===\n")

    records: list[dict[str, Any]] = []
    errors = 0

    # 1. Parse SVG dataset
    svg_paths = sorted(glob.glob(str(SVG_DIR / "*.svg")))
    print(f"SVG scenes found: {len(svg_paths)}")
    for path in svg_paths:
        try:
            rec = _parse_svg(path)
            if rec:
                records.append(rec)
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN {os.path.basename(path)}: {exc}")
            errors += 1

    # 2. Parse 3-D render annotations
    render_paths = sorted(glob.glob(str(RENDER_DIR / "*.json")))
    render_paths = [p for p in render_paths if "_index" not in p]
    print(f"3-D render annotations found: {len(render_paths)}")
    for path in render_paths:
        try:
            rec = _parse_render_annotation(path)
            if rec:
                records.append(rec)
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN {os.path.basename(path)}: {exc}")
            errors += 1

    print(f"\nTotal training records extracted: {len(records)}  (errors: {errors})")

    # ── Severity distribution ─────────────────────────────────────────────────
    sev_counts: dict[str, int] = {}
    for r in records:
        sev_counts[r["app_severity"]] = sev_counts.get(r["app_severity"], 0) + 1
    print("\nSeverity distribution:")
    for s in ("critical", "high", "medium", "low"):
        print(f"  {s:8s}: {sev_counts.get(s, 0)}")

    # ── Save fine-tune JSONL ──────────────────────────────────────────────────
    finetune_path = TRAINING_DIR / "watsonx_finetune.jsonl"
    with open(finetune_path, "w") as f:
        for rec in records:
            pair = _to_finetune_pair(rec)
            f.write(json.dumps(pair) + "\n")
    print(f"\nFine-tune JSONL saved: {finetune_path}  ({len(records)} rows)")

    # ── Save curated few-shot examples ────────────────────────────────────────
    few_shot: dict[str, dict] = {}
    preferred_viols = {
        "critical": "vegetation_contact_primary",
        "high":     "crossarm_split",
        "medium":   "vegetation_encroachment_primary",
        "low":      "id_tag_missing",
    }
    for rec in records:
        sev = rec["app_severity"]
        if sev in few_shot:
            continue
        pref = preferred_viols.get(sev, "")
        if pref in rec["violations"] or sev not in few_shot:
            few_shot[sev] = rec

    # Fallback: pick first record for any missing severity
    for rec in records:
        sev = rec["app_severity"]
        if sev not in few_shot:
            few_shot[sev] = rec

    few_shot_path = TRAINING_DIR / "few_shot_examples.json"
    with open(few_shot_path, "w") as f:
        json.dump(list(few_shot.values()), f, indent=2)
    print(f"Few-shot examples saved: {few_shot_path}  ({len(few_shot)} examples)")

    # ── Save pipeline report ──────────────────────────────────────────────────
    report = {
        "total_records": len(records),
        "svg_scenes": len(svg_paths),
        "render_annotations": len(render_paths),
        "errors": errors,
        "severity_distribution": sev_counts,
        "violation_types": sorted({v for r in records for v in r["violations"]}),
    }
    report_path = TRAINING_DIR / "pipeline_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Pipeline report saved: {report_path}")
    print("\nDone. Upload watsonx_finetune.jsonl to watsonx.ai → Tuning Studio to fine-tune Granite.")


if __name__ == "__main__":
    run()
