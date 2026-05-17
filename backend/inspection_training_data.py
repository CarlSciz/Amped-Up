from __future__ import annotations

import ast
import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .seed_violation_types import VIOLATION_TYPES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVG_DATASET_ROOT = PROJECT_ROOT / "dataset" / "svgs"
SVG_OUT_DIR = SVG_DATASET_ROOT / "out"
SVG_PREVIEW_DIR = SVG_DATASET_ROOT / "preview"
SVG_METADATA_PATH = SVG_OUT_DIR / "metadata.json"

SYSTEM_PROMPT = (
    "You are an electric utility pole inspection assistant. Analyze field imagery and "
    "return only structured JSON that can be used by the Amped Up dashboard. Cite the "
    "visible evidence, applicable regulatory references, severity, recommended action, "
    "and any measurement/specification that must be confirmed in the field."
)

OSHA_TO_DASHBOARD_SEVERITY = {
    "imminent_danger": "critical",
    "serious": "high",
    "other_than_serious": "medium",
    "deminimis": "low",
    "de_minimis": "low",
    "multi_defect": "critical",
    "compliant": "low",
    "n/a": "low",
    "none": "low",
}

VIOLATION_ALIAS_TO_TYPE_ID = {
    "anchor_exposed": "vt-guying-anchor",
    "anchorexpose": "vt-guying-anchor",
    "anchorexposure": "vt-guying-anchor",
    "anchor_rod_exposed": "vt-guying-anchor",
    "bird_nest_on_crossarm": "vt-equipment-leak",
    "bird_nest_on_equipment": "vt-equipment-leak",
    "bird_nest_on_recloser": "vt-equipment-leak",
    "broken_arm": "vt-pole-condition",
    "buildinglow": "vt-overhead-clearance",
    "clearance_building": "vt-overhead-clearance",
    "clearance_ground": "vt-overhead-clearance",
    "clearance_road": "vt-overhead-clearance",
    "clampslipped": "vt-equipment-leak",
    "control_cable_damaged": "vt-equipment-leak",
    "conductorlow": "vt-overhead-clearance",
    "crackedbushing": "vt-equipment-leak",
    "crackedinsulator": "vt-equipment-leak",
    "crossarm_decay": "vt-pole-condition",
    "crossarm_split": "vt-pole-condition",
    "cutout_hanging": "vt-equipment-leak",
    "cutout_fuse_hanging": "vt-equipment-leak",
    "cutout_fuse_hanging_open": "vt-equipment-leak",
    "dead_end_clamp_slipped": "vt-equipment-leak",
    "dead_end_insulator_damaged": "vt-equipment-leak",
    "downed_conductor": "vt-overhead-clearance",
    "downed_conductor_dead_end_failure": "vt-overhead-clearance",
    "downedconductor": "vt-overhead-clearance",
    "exposed_conductor": "vt-overhead-clearance",
    "exposed_underground_cable": "vt-grounding-bonding",
    "ground_missing": "vt-grounding-bonding",
    "groundmissing": "vt-grounding-bonding",
    "guy_corrosion": "vt-guying-anchor",
    "guy_guard_damaged": "vt-guying-anchor",
    "guy_strand_corroded": "vt-guying-anchor",
    "guy_strand_corrosion": "vt-guying-anchor",
    "guycorr": "vt-guying-anchor",
    "guyguard": "vt-guying-anchor",
    "insulator_cracked": "vt-equipment-leak",
    "insulator_damaged": "vt-equipment-leak",
    "insulator_arc_tracking": "vt-equipment-leak",
    "insulator_weather_stain": "vt-equipment-leak",
    "insulatorarc": "vt-equipment-leak",
    "jumperdamaged": "vt-equipment-leak",
    "jumper_damaged": "vt-equipment-leak",
    "jumperlow": "vt-overhead-clearance",
    "loose_hardware": "vt-equipment-leak",
    "loosehardware": "vt-equipment-leak",
    "missingground": "vt-grounding-bonding",
    "missing_equipment_ground": "vt-grounding-bonding",
    "neutraldrop": "vt-grounding-bonding",
    "oilleak": "vt-equipment-leak",
    "openneutral": "vt-grounding-bonding",
    "open_neutral": "vt-grounding-bonding",
    "phase_sep": "vt-overhead-clearance",
    "phase_separation": "vt-overhead-clearance",
    "pole_condition": "vt-pole-condition",
    "pole_decay": "vt-pole-condition",
    "pole_groundline_decay": "vt-pole-condition",
    "pole_groundline_rot": "vt-pole-condition",
    "pole_id_faded": "vt-identification-marking",
    "pole_id_paint_faded": "vt-identification-marking",
    "pole_lean": "vt-pole-condition",
    "pole_tag_missing": "vt-identification-marking",
    "poledecay": "vt-pole-condition",
    "polelean": "vt-pole-condition",
    "pipedamaged": "vt-equipment-leak",
    "primary_conductor_ground_clearance": "vt-overhead-clearance",
    "rebarexposed": "vt-pole-condition",
    "riserdamage": "vt-grounding-bonding",
    "riser_conduit_damaged": "vt-grounding-bonding",
    "riser_insulation_burned": "vt-grounding-bonding",
    "riser_pipe_damaged": "vt-grounding-bonding",
    "safety_zone_breach": "vt-joint-use-attachment",
    "servicelow": "vt-overhead-clearance",
    "service_drop_low": "vt-overhead-clearance",
    "service_drop_ground_clearance": "vt-overhead-clearance",
    "service_drop_sag_low": "vt-overhead-clearance",
    "service_attachment_building_low": "vt-overhead-clearance",
    "straininsulator": "vt-equipment-leak",
    "strain_insulator_shattered": "vt-equipment-leak",
    "structure_id_plate_faded": "vt-identification-marking",
    "thermal_sag_violation": "vt-overhead-clearance",
    "transformer_oil_leak": "vt-equipment-leak",
    "unauthorized": "vt-joint-use-attachment",
    "veg_contact": "vt-vegetation-contact",
    "veg_encroachment": "vt-vegetation-contact",
    "vegcontact": "vt-vegetation-contact",
    "vegetation_contact_primary": "vt-vegetation-contact",
    "vegetation_contact_phase_a": "vt-vegetation-contact",
    "vegetation_contact_transmission": "vt-vegetation-contact",
    "vegetation_encroachment": "vt-vegetation-contact",
    "weatherhead": "vt-equipment-leak",
    "weather_head_damaged": "vt-equipment-leak",
    "weather_head_missing": "vt-equipment-leak",
}

_VIOLATION_TYPES_BY_ID = {item["id"]: item for item in VIOLATION_TYPES}


@dataclass(frozen=True)
class TrainingDefect:
    violation: str
    severity: str
    dashboard_severity: str
    violation_type_id: str | None


@dataclass(frozen=True)
class TrainingRecord:
    record_id: str
    source_svg: str
    source_preview: str | None
    scene_id: str
    pole_type_id: str
    pole_type: dict[str, Any]
    scene_type: str
    weather_condition: str | None
    framing: str | None
    defects: list[TrainingDefect]
    overall_severity: str
    dashboard_severity: str
    violation_type_id: str | None
    violation_family: str | None
    regulations: list[str]
    evidence: list[str]
    dashboard_output: dict[str, Any]
    ibm_messages: list[dict[str, str]]

    def to_json(self) -> str:
        payload = asdict(self)
        payload["defects"] = [asdict(defect) for defect in self.defects]
        return json.dumps(payload, sort_keys=True)


def load_svg_metadata() -> dict[str, Any]:
    with SVG_METADATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _text_nodes(svg_path: Path) -> list[str]:
    try:
        root = ET.parse(svg_path).getroot()
        values = [
            "".join(node.itertext()).strip()
            for node in root.iter()
            if str(node.tag).lower().endswith("text") and node.text
        ]
    except ET.ParseError:
        raw = svg_path.read_text(encoding="utf-8")
        values = re.findall(r"<text\b[^>]*>(.*?)</text>", raw, flags=re.DOTALL)
    return [html.unescape(value.strip()) for value in values if value and value.strip()]


def _parse_annotation_lines(lines: list[str]) -> dict[str, Any]:
    annotations: dict[str, Any] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if key == "defects":
            try:
                annotations[key] = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                annotations[key] = value
        elif key in {"violation", "severity", "scene_type", "weather_condition", "framing", "overall_severity", "worst_severity_present"}:
            annotations[key] = value
        elif key == "defect_count":
            try:
                annotations[key] = int(value)
            except ValueError:
                annotations[key] = value
    return annotations


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().lower().replace("-", "_")


def _dashboard_severity(value: str | None) -> str:
    return OSHA_TO_DASHBOARD_SEVERITY.get(_normalize_token(value), "medium")


def _violation_type_id(violation: str | None) -> str | None:
    token = _normalize_token(violation)
    if token in VIOLATION_ALIAS_TO_TYPE_ID:
        return VIOLATION_ALIAS_TO_TYPE_ID[token]

    for alias, type_id in VIOLATION_ALIAS_TO_TYPE_ID.items():
        if alias in token or token in alias:
            return type_id
    keyword_map = [
        (("vegetation", "veg_", "branch", "tree"), "vt-vegetation-contact"),
        (("clearance", "sag", "low", "downed_conductor", "phase_sep"), "vt-overhead-clearance"),
        (("ground", "neutral", "riser", "bond", "conduit", "cable"), "vt-grounding-bonding"),
        (("guy", "anchor"), "vt-guying-anchor"),
        (("pole", "crossarm", "arm", "decay", "rot", "lean", "crack", "corrosion_pitting"), "vt-pole-condition"),
        (("insulator", "transformer", "cutout", "jumper", "hardware", "bushing", "recloser", "meter", "weather_head"), "vt-equipment-leak"),
        (("tag", "id_", "marker", "marking", "paint_faded", "plate_faded"), "vt-identification-marking"),
        (("joint", "attachment", "safety_zone", "unauthorized", "catv", "fiber"), "vt-joint-use-attachment"),
    ]
    for keywords, type_id in keyword_map:
        if any(keyword in token for keyword in keywords):
            return type_id
    return None


def _scene_tokens(scene_id: str) -> list[str]:
    return [token for token in scene_id.split("_") if token]


def _infer_violation_from_scene(scene_id: str) -> str:
    tokens = _scene_tokens(scene_id)
    if "baseline" in tokens or "compliant" in tokens:
        return "compliant"
    if "wmd" in tokens:
        return "_".join(tokens[2:])
    if "w" in tokens:
        return "_".join(tokens[3:])
    if any(token.startswith("md") for token in tokens):
        md_index = next(index for index, token in enumerate(tokens) if token.startswith("md"))
        return "_".join(tokens[md_index + 1 :])
    return "_".join(tokens[2:]) if len(tokens) > 2 else scene_id


def _infer_scene_type(scene_id: str, annotations: dict[str, Any]) -> str:
    if annotations.get("scene_type"):
        return str(annotations["scene_type"])
    tokens = _scene_tokens(scene_id)
    if "wmd" in tokens or any(token.startswith("md") for token in tokens):
        return "multi_defect"
    if "w" in tokens:
        return "weather_context" if "compliant" in tokens else "weather_violation"
    return "baseline" if "baseline" in tokens else "single_defect"


def _infer_weather(scene_id: str, annotations: dict[str, Any]) -> str | None:
    if annotations.get("weather_condition"):
        return str(annotations["weather_condition"])
    tokens = _scene_tokens(scene_id)
    if "ice" in tokens:
        return "ice_loading"
    if "snow" in tokens:
        return "snow_accumulation"
    if "storm" in tokens:
        return "post_storm"
    if "summer" in tokens:
        return "summer_thermal"
    return None


def _collect_regulations(lines: list[str]) -> list[str]:
    refs = []
    for line in lines:
        if any(prefix in line for prefix in ("NESC", "OSHA", "MIOSHA", "MPSC", "IEEE", "ANSI", "ASTM", "NERC", "USACE", "AAR")):
            refs.append(line)
    return list(dict.fromkeys(refs))


def _build_defects(scene_id: str, annotations: dict[str, Any]) -> list[TrainingDefect]:
    raw_defects = annotations.get("defects")
    defects: list[TrainingDefect] = []
    if isinstance(raw_defects, list):
        for item in raw_defects:
            if not isinstance(item, dict):
                continue
            violation = str(item.get("violation") or _infer_violation_from_scene(scene_id))
            severity = str(item.get("severity") or annotations.get("worst_severity_present") or annotations.get("severity") or "other_than_serious")
            defects.append(
                TrainingDefect(
                    violation=violation,
                    severity=severity,
                    dashboard_severity=_dashboard_severity(severity),
                    violation_type_id=_violation_type_id(violation),
                )
            )
    if defects:
        return defects

    violation = str(annotations.get("violation") or _infer_violation_from_scene(scene_id))
    if _normalize_token(violation) in {"none", "n/a", "baseline", "compliant"}:
        violation = "compliant"
    severity = str(annotations.get("severity") or ("compliant" if violation == "compliant" else "other_than_serious"))
    if violation == "compliant" and _normalize_token(severity) in {"n/a", "none"}:
        severity = "compliant"
    return [
        TrainingDefect(
            violation=violation,
            severity=severity,
            dashboard_severity=_dashboard_severity(severity),
            violation_type_id=_violation_type_id(violation),
        )
    ]


def _primary_defect(defects: list[TrainingDefect]) -> TrainingDefect:
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(defects, key=lambda item: severity_rank.get(item.dashboard_severity, 2))[0]


def _dashboard_output(
    *,
    scene_id: str,
    pole_type: dict[str, Any],
    defects: list[TrainingDefect],
    regulations: list[str],
    evidence: list[str],
    weather_condition: str | None,
) -> dict[str, Any]:
    primary = _primary_defect(defects)
    violation_type = _VIOLATION_TYPES_BY_ID.get(primary.violation_type_id or "")
    violation_name = violation_type["name"] if violation_type else primary.violation.replace("_", " ").title()
    pole_name = str(pole_type.get("name") or "Unknown pole type")
    finding = f"{violation_name} observed on {pole_name}."
    if primary.violation == "compliant":
        violation_name = "Compliant reference"
        finding = f"No visible non-compliant condition in {pole_name} training scene."

    specs = {
        "pole_height_ft": pole_type.get("height_ft"),
        "ansi_class": pole_type.get("ansi_class"),
        "embedment_ft": pole_type.get("embedment_ft"),
        "voltage_kv": pole_type.get("voltage_kv"),
        "voltage_v": pole_type.get("voltage_v"),
        "material": pole_type.get("material") or pole_type.get("species") or "unknown",
        "weather_condition": weather_condition,
    }

    return {
        "dashboard_title": f"{violation_name} - {scene_id}",
        "severity": primary.dashboard_severity,
        "finding": finding,
        "violation_type_id": primary.violation_type_id,
        "violation_family": violation_type.get("violation_family") if violation_type else None,
        "nesc": "; ".join(ref for ref in regulations if "NESC" in ref) or "NESC field review",
        "regulations": regulations,
        "recommended_action": (
            violation_type.get("recommended_action")
            if violation_type
            else "Review the uploaded images, confirm the violation type, and assign a work priority."
        ),
        "evidence_required": violation_type.get("evidence_required") if violation_type else "Photos and field notes.",
        "visible_evidence": evidence,
        "specifications": specs,
        "defects": [asdict(defect) for defect in defects],
    }


def build_training_record(scene: dict[str, str], metadata: dict[str, Any]) -> TrainingRecord:
    scene_id = scene["scene_id"]
    svg_path = SVG_OUT_DIR / scene["file"]
    preview_path = SVG_PREVIEW_DIR / scene["file"].replace(".svg", ".png")
    pole_type_id = scene_id.split("_", 1)[0]
    pole_type = metadata.get("pole_types", {}).get(pole_type_id, {})
    lines = _text_nodes(svg_path)
    annotations = _parse_annotation_lines(lines)
    defects = _build_defects(scene_id, annotations)
    primary = _primary_defect(defects)
    regulations = _collect_regulations(lines)
    evidence = [
        line
        for line in lines
        if line not in regulations
        and line.lower() not in {"annotation metadata", "regulation citations"}
        and not re.match(r"^[a-z_ ]+:", line.lower())
    ][:12]
    scene_type = _infer_scene_type(scene_id, annotations)
    weather_condition = _infer_weather(scene_id, annotations)
    dashboard_output = _dashboard_output(
        scene_id=scene_id,
        pole_type=pole_type,
        defects=defects,
        regulations=regulations,
        evidence=evidence,
        weather_condition=weather_condition,
    )
    user_prompt = (
        f"Analyze the field image for scene {scene_id}. Pole context: "
        f"{json.dumps(pole_type, sort_keys=True)}. Return the Amped Up dashboard JSON."
    )

    return TrainingRecord(
        record_id=f"svg-v0.7-{scene_id}",
        source_svg=str(svg_path.relative_to(PROJECT_ROOT)),
        source_preview=str(preview_path.relative_to(PROJECT_ROOT)) if preview_path.exists() else None,
        scene_id=scene_id,
        pole_type_id=pole_type_id,
        pole_type=pole_type,
        scene_type=scene_type,
        weather_condition=weather_condition,
        framing=annotations.get("framing"),
        defects=defects,
        overall_severity=str(annotations.get("overall_severity") or annotations.get("severity") or primary.severity),
        dashboard_severity=primary.dashboard_severity,
        violation_type_id=primary.violation_type_id,
        violation_family=dashboard_output["violation_family"],
        regulations=regulations,
        evidence=evidence,
        dashboard_output=dashboard_output,
        ibm_messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": json.dumps(dashboard_output, sort_keys=True)},
        ],
    )


def build_training_records() -> list[TrainingRecord]:
    metadata = load_svg_metadata()
    return [build_training_record(scene, metadata) for scene in metadata.get("scenes", [])]
