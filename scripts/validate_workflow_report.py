from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_report_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_number_variants(value: int) -> list[str]:
    return [str(value), f"{value:,}", f"{value:,}".replace(",", "，")]


def has_any_literal(text: str, values: list[str]) -> bool:
    return any(value in text for value in values if value)


def has_primary_key_mention(text: str, primary_key: list[str]) -> bool:
    if not primary_key:
        return True
    joined = r"\s*,\s*".join(re.escape(item) for item in primary_key)
    patterns = [
        rf"PRIMARY\s*\(\s*{joined}\s*\)",
        rf"主键[^。\n]{{0,30}}{joined}",
        rf"{joined}[^。\n]{{0,12}}主键",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def has_forbidden_primary_key_claim(text: str, columns: list[str]) -> bool:
    if not columns:
        return False
    joined = "|".join(re.escape(column) for column in columns)
    patterns = [
        rf"主键[^。\n]{{0,20}}(?:{joined})",
        rf"(?:{joined})[^。\n]{{0,12}}主键",
        rf"PRIMARY\s*\(\s*(?:{joined})\s*\)",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def validate_report_text(manifest: dict, report_text: str) -> dict:
    normalized = report_text.replace("\r\n", "\n")
    failures: list[dict] = []
    passes: list[str] = []

    for phrase in manifest.get("global_forbidden_phrases", []):
        if phrase in normalized:
            failures.append({"type": "forbidden_phrase", "detail": phrase})
    if not failures:
        passes.append("未命中全局禁止短语")

    for unit in manifest.get("sql_units", []):
        sql_id = unit["sql_id"]
        required_indexes = unit.get("required_index_names", [])
        if required_indexes and has_any_literal(normalized, required_indexes):
            passes.append(f"{sql_id}: 命中至少一个要求的索引名")
        elif required_indexes:
            failures.append({"type": "missing_index_name", "sql_id": sql_id, "detail": required_indexes})

        for table_expectation in unit.get("table_expectations", []):
            table_name = table_expectation["table_name"]
            if table_name in normalized:
                passes.append(f"{sql_id}: 命中表名 {table_name}")
            else:
                failures.append({"type": "missing_table_name", "sql_id": sql_id, "detail": table_name})

            row_variants = build_number_variants(int(table_expectation["table_rows_exact"]))
            if has_any_literal(normalized, row_variants):
                passes.append(f"{sql_id}: 命中表行数 {table_expectation['table_rows_exact']}")
            else:
                failures.append(
                    {
                        "type": "missing_table_rows_exact",
                        "sql_id": sql_id,
                        "detail": table_expectation["table_rows_exact"],
                    }
                )

            primary_key = table_expectation.get("primary_key", [])
            if has_primary_key_mention(normalized, primary_key):
                if primary_key:
                    passes.append(f"{sql_id}: 命中主键 {primary_key}")
            else:
                if primary_key:
                    failures.append({"type": "missing_primary_key", "sql_id": sql_id, "detail": primary_key})

            forbidden_columns = table_expectation.get("forbidden_primary_key_columns", [])
            if has_forbidden_primary_key_claim(normalized, forbidden_columns):
                failures.append({"type": "wrong_primary_key_claim", "sql_id": sql_id, "detail": forbidden_columns})
            else:
                passes.append(f"{sql_id}: 未发现错误主键推断 {forbidden_columns}")

    return {
        "passed": not failures,
        "failure_count": len(failures),
        "pass_count": len(passes),
        "failures": failures,
        "passes": passes,
    }


def render_markdown_summary(result: dict) -> str:
    lines = [
        "# 工作流报告校验结果",
        "",
        f"- passed: {result['passed']}",
        f"- failure_count: {result['failure_count']}",
        f"- pass_count: {result['pass_count']}",
        "",
        "## Failures",
    ]
    if result["failures"]:
        lines.extend([f"- {json.dumps(item, ensure_ascii=False)}" for item in result["failures"]])
    else:
        lines.append("- none")
    lines.extend(["", "## Passes"])
    if result["passes"]:
        lines.extend([f"- {item}" for item in result["passes"]])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate workflow report against upload manifest.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = validate_report_text(load_manifest(args.manifest), load_report_text(args.report))
    if args.output_json:
        args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.write_text(render_markdown_summary(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
