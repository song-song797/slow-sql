from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "slow-sql-backend-main" / "slow-sql-backend-main"
REPORTS_DIR = ROOT / "docs" / "workflow-upload" / "reports"

os.chdir(BACKEND_ROOT)
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.report_provider import RemoteWorkflowReportProvider  # noqa: E402
from validate_workflow_report import render_markdown_summary, validate_report_text  # noqa: E402


async def invoke_file_workflow(upload_text: str) -> dict:
    provider = RemoteWorkflowReportProvider(file_input_mode=True)
    first_resp = await provider.invoke_workflow(workflow_id=provider.workflow_id, stream=False)
    workflow_input = provider._extract_input_event(first_resp, sql_text=upload_text)
    follow_resp = await provider._invoke_followup_with_candidates(
        input_candidates=workflow_input["input_payload"],
        session_id=workflow_input["session_id"],
        message_id=workflow_input["message_id"],
    )
    parsed = provider._parse_workflow_result(follow_resp)
    return {
        "first_response": first_resp,
        "workflow_input": workflow_input,
        "follow_response": follow_resp,
        "parsed": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real workflow file-upload regression case.")
    parser.add_argument("--upload", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--label")
    args = parser.parse_args()

    upload_path = args.upload.resolve()
    manifest_path = args.manifest.resolve()
    label = args.label or upload_path.stem
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    upload_text = upload_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload = asyncio.run(invoke_file_workflow(upload_text))
    report_text = payload["parsed"].get("report_content") or ""
    validation = validate_report_text(manifest, report_text)

    raw_path = REPORTS_DIR / f"{label}.raw.json"
    report_path = REPORTS_DIR / f"{label}.report.md"
    validation_json_path = REPORTS_DIR / f"{label}.validation.json"
    validation_md_path = REPORTS_DIR / f"{label}.validation.md"

    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(report_text, encoding="utf-8")
    validation_json_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation_md_path.write_text(render_markdown_summary(validation), encoding="utf-8")

    print(json.dumps({"report_path": str(report_path), "validation": validation}, ensure_ascii=False, indent=2))
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
