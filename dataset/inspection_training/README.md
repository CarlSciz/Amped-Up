# Inspection Training Dataset

This folder is generated from `dataset/svgs/out/metadata.json` and the 230 SVG training scenes.

Run:

```bash
python scripts/export_inspection_training_data.py
```

Outputs:

- `inspection_records.jsonl`: full normalized scene records with pole specs, defects, regulatory references, dashboard severity, and expected dashboard output.
- `ibm_messages.jsonl`: chat-style examples with `system`, `user`, and structured JSON `assistant` messages. Use this as the IBM/watsonx adaptation source or as the basis for provider-specific conversion.
- `dashboard_contracts.jsonl`: compact input/expected-output records for app evaluation.
- `summary.json`: generated file count and record count.

The expected model output is intentionally the same contract used by the app's `PhotoAnalysis` response:

```json
{
  "severity": "critical",
  "finding": "Vegetation contact or encroachment observed on Joint-use distribution tangent pole.",
  "violation_type_id": "vt-vegetation-contact",
  "violation_family": "vegetation",
  "nesc": "NESC Rule 218.A.1...",
  "regulations": ["NESC Rule 218.A.1...", "OSHA 29 CFR 1910.269..."],
  "recommended_action": "Schedule trimming or urgent vegetation response...",
  "evidence_required": "Photos, estimated clearance/contact...",
  "specifications": {
    "pole_height_ft": 40,
    "ansi_class": 4,
    "voltage_kv": 12.47
  }
}
```

When an IBM vision/LLM service is connected, its JSON should be validated against this shape before creating a dashboard report.

