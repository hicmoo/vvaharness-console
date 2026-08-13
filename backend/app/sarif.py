"""Ingest SARIF 2.1.0 output produced by vvaharness into Finding rows."""

import json
import re
from pathlib import Path
from typing import Any

CWE_RE = re.compile(r"CWE-\d+", re.IGNORECASE)


def _extract_cwe(result: dict[str, Any], rule: dict[str, Any] | None) -> str | None:
    haystacks: list[str] = [result.get("ruleId") or ""]
    props = result.get("properties") or {}
    haystacks.extend(str(v) for v in props.values())
    if rule:
        haystacks.append(json.dumps(rule.get("properties") or {}))
        haystacks.append(rule.get("id") or "")
    for hay in haystacks:
        m = CWE_RE.search(hay)
        if m:
            return m.group(0).upper()
    return None


def parse_sarif(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text())
    findings: list[dict[str, Any]] = []
    for run in doc.get("runs", []):
        rules_by_id: dict[str, dict[str, Any]] = {}
        driver = (run.get("tool") or {}).get("driver") or {}
        for rule in driver.get("rules", []):
            if rule.get("id"):
                rules_by_id[rule["id"]] = rule
        for result in run.get("results", []):
            rule_id = result.get("ruleId")
            rule = rules_by_id.get(rule_id or "")
            message = ((result.get("message") or {}).get("text") or "").strip()
            title = message.splitlines()[0][:300] if message else (rule_id or "Finding")
            if rule and (rule.get("shortDescription") or {}).get("text"):
                title = rule["shortDescription"]["text"][:300]
            file = line = None
            locations = result.get("locations") or []
            if locations:
                phys = locations[0].get("physicalLocation") or {}
                file = (phys.get("artifactLocation") or {}).get("uri")
                line = (phys.get("region") or {}).get("startLine")
            findings.append(
                {
                    "rule_id": rule_id,
                    "title": title,
                    "message": message or None,
                    "severity": result.get("level") or "warning",
                    "cwe": _extract_cwe(result, rule),
                    "file": file,
                    "line": line,
                }
            )
    return findings
