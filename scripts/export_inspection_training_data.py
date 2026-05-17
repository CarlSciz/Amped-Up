from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inspection_training_data import PROJECT_ROOT, build_training_records


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dataset" / "inspection_training"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export SVG pole inspection examples as model-ready JSONL."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    records = build_training_records()
    full_records = []
    message_records = []
    dashboard_contracts = []

    for record in records:
        payload = json.loads(record.to_json())
        full_records.append(payload)
        message_records.append(
            {
                "id": record.record_id,
                "messages": record.ibm_messages,
                "image": record.source_preview or record.source_svg,
                "metadata": {
                    "scene_id": record.scene_id,
                    "pole_type_id": record.pole_type_id,
                    "scene_type": record.scene_type,
                    "weather_condition": record.weather_condition,
                    "violation_type_id": record.violation_type_id,
                    "dashboard_severity": record.dashboard_severity,
                },
            }
        )
        dashboard_contracts.append(
            {
                "id": record.record_id,
                "input": {
                    "image": record.source_preview or record.source_svg,
                    "pole_type": record.pole_type,
                    "scene_id": record.scene_id,
                },
                "expected_output": record.dashboard_output,
            }
        )

    write_jsonl(args.output_dir / "inspection_records.jsonl", full_records)
    write_jsonl(args.output_dir / "ibm_messages.jsonl", message_records)
    write_jsonl(args.output_dir / "dashboard_contracts.jsonl", dashboard_contracts)

    summary = {
        "record_count": len(records),
        "output_dir": str(args.output_dir.relative_to(PROJECT_ROOT)),
        "files": [
            "inspection_records.jsonl",
            "ibm_messages.jsonl",
            "dashboard_contracts.jsonl",
        ],
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
