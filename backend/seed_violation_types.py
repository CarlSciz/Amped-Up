from __future__ import annotations

from sqlalchemy import select

from . import orm_models as dbm
from .database import SessionLocal

NESC_SOURCE_URL = "https://standards.ieee.org/standard/C2-2023.html"

VIOLATION_TYPES = [
    {
        "id": "vt-overhead-clearance",
        "code": "overhead_clearance",
        "name": "Overhead clearance",
        "description": "Potential clearance issue involving overhead supply or communication facilities.",
        "default_severity": dbm.Severity.CRITICAL,
        "recommended_action": "Verify measured clearance against the licensed NESC edition and dispatch for correction if out of tolerance.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Clearances",
        "violation_family": "clearance",
        "measurement_kind": "clearance",
        "measurement_unit": "ft",
        "comparator": ">=",
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["roadway crossing", "building clearance", "communication attachment clearance"],
        },
        "evidence_required": "Measured clearance, voltage class, attachment type, location context, and photos.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Fill rule_number/table_number from your licensed NESC copy for each clearance scenario.",
        "sort_order": 10,
    },
    {
        "id": "vt-grounding-bonding",
        "code": "grounding_bonding",
        "name": "Grounding and bonding",
        "description": "Potential missing, damaged, disconnected, or noncompliant grounding or bonding condition.",
        "default_severity": dbm.Severity.HIGH,
        "recommended_action": "Inspect grounding path continuity and correct per utility standards and licensed NESC requirements.",
        "nesc_part": "Section 9 - Grounding Methods",
        "nesc_section": "Grounding",
        "violation_family": "grounding",
        "measurement_kind": "continuity",
        "measurement_unit": None,
        "comparator": None,
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["pole ground", "equipment bond", "neutral bond", "grounding electrode connection"],
        },
        "evidence_required": "Photos of grounding conductor/bonds, equipment present, continuity test if available.",
        "source_url": "https://standards.ieee.org/products-programs/nesc/program/",
        "notes": "IEEE public materials identify Section 9 as grounding methods; fill exact rule references from licensed NESC.",
        "sort_order": 20,
    },
    {
        "id": "vt-guying-anchor",
        "code": "guying_anchor",
        "name": "Guying and anchor condition",
        "description": "Potential guy wire, anchor, guard, tension, or accessibility issue.",
        "default_severity": dbm.Severity.HIGH,
        "recommended_action": "Inspect guy tension, anchor condition, visibility/guarding, and public exposure.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Guys and anchors",
        "violation_family": "structural_support",
        "measurement_kind": "condition",
        "measurement_unit": None,
        "comparator": None,
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["slack guy", "damaged anchor", "missing guy guard", "public contact exposure"],
        },
        "evidence_required": "Photos of anchor/guy assembly, tension observation, location context, pedestrian/traffic exposure.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Use utility construction standards plus licensed NESC references for exact conditions.",
        "sort_order": 30,
    },
    {
        "id": "vt-vegetation-contact",
        "code": "vegetation_contact",
        "name": "Vegetation contact or encroachment",
        "description": "Vegetation is contacting or encroaching on supply or communication facilities.",
        "default_severity": dbm.Severity.MEDIUM,
        "recommended_action": "Schedule trimming or urgent vegetation response based on conductor contact, voltage class, and outage/fire risk.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Clearances and maintenance",
        "violation_family": "vegetation",
        "measurement_kind": "clearance",
        "measurement_unit": "ft",
        "comparator": ">=",
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["tree contact", "branch encroachment", "right-of-way clearance concern"],
        },
        "evidence_required": "Photos, estimated clearance/contact, species or growth pattern if known, conductor type/voltage.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Exact trimming thresholds are often utility- and jurisdiction-specific; attach local standard references if applicable.",
        "sort_order": 40,
    },
    {
        "id": "vt-pole-condition",
        "code": "pole_condition",
        "name": "Pole structural condition",
        "description": "Pole damage, decay, lean, rot, impact damage, or other structural deterioration.",
        "default_severity": dbm.Severity.HIGH,
        "recommended_action": "Assess structural integrity and prioritize reinforcement or replacement based on severity.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Strength and loading",
        "violation_family": "structure",
        "measurement_kind": "condition",
        "measurement_unit": None,
        "comparator": None,
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["excessive lean", "wood decay", "crossarm rot", "impact damage", "split pole"],
        },
        "evidence_required": "Photos, pole class/material, lean measurement, age/install date, treatment/inspection history.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Use licensed NESC and utility inspection criteria to set exact failure thresholds.",
        "sort_order": 50,
    },
    {
        "id": "vt-equipment-leak",
        "code": "equipment_leak",
        "name": "Equipment leak or contamination",
        "description": "Observed oil leak, staining, damaged equipment housing, or potential environmental/safety issue.",
        "default_severity": dbm.Severity.CRITICAL,
        "recommended_action": "Dispatch qualified crew and environmental response where transformer oil or energized equipment risk is present.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Equipment installation and maintenance",
        "violation_family": "equipment",
        "measurement_kind": "condition",
        "measurement_unit": None,
        "comparator": None,
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["transformer leak", "oil staining", "damaged insulator", "damaged cutout"],
        },
        "evidence_required": "Photos, equipment type, leak/staining extent, proximity to public areas, energized status if known.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Environmental handling requirements may also come from utility policy and local/state regulation.",
        "sort_order": 60,
    },
    {
        "id": "vt-joint-use-attachment",
        "code": "joint_use_attachment",
        "name": "Joint-use attachment",
        "description": "Potential issue involving communication, fiber, cable, or third-party attachments on utility structures.",
        "default_severity": dbm.Severity.MEDIUM,
        "recommended_action": "Verify attachment height, separation, owner, permit status, and clearance from supply facilities.",
        "nesc_part": "Part 2 - Safety Rules for Overhead Lines",
        "nesc_section": "Supply and communication line clearances",
        "violation_family": "joint_use",
        "measurement_kind": "clearance",
        "measurement_unit": "ft",
        "comparator": ">=",
        "applicability": {
            "requires_licensed_rule_lookup": True,
            "examples": ["fiber attachment", "CATV attachment", "communication worker safety zone", "unauthorized attachment"],
        },
        "evidence_required": "Attachment owner/type, measured height, separation from supply conductors, permit/ticket reference.",
        "source_url": NESC_SOURCE_URL,
        "notes": "Use licensed NESC tables and local joint-use agreement requirements for exact values.",
        "sort_order": 70,
    },
    {
        "id": "vt-identification-marking",
        "code": "identification_marking",
        "name": "Identification and marking",
        "description": "Missing, faded, illegible, or noncompliant pole or equipment identification.",
        "default_severity": dbm.Severity.LOW,
        "recommended_action": "Replace or restore pole identification during the next maintenance cycle unless emergency response depends on the missing ID.",
        "nesc_part": "Utility and local operating standards",
        "nesc_section": "Identification and records",
        "violation_family": "identification",
        "measurement_kind": "condition",
        "measurement_unit": None,
        "comparator": None,
        "applicability": {
            "requires_licensed_rule_lookup": False,
            "examples": ["missing pole tag", "illegible pole number", "faded equipment marker"],
        },
        "evidence_required": "Photo of tag or stencil, pole location, and replacement identifier if known.",
        "source_url": None,
        "notes": "Often governed by utility operating standards and state inspection/record rules.",
        "sort_order": 80,
    },
]


def seed_violation_types() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set")

    with SessionLocal() as db:
        for values in VIOLATION_TYPES:
            row = db.scalars(select(dbm.ViolationType).where(dbm.ViolationType.code == values["code"])).first()
            if row is None:
                db.add(dbm.ViolationType(**values))
                continue

            for key, value in values.items():
                setattr(row, key, value)

        db.commit()


if __name__ == "__main__":
    seed_violation_types()
    print(f"Seeded {len(VIOLATION_TYPES)} violation types.")
