from datetime import datetime

from pydantic import BaseModel, ConfigDict

PROVIDER_KINDS = ("anthropic", "openai", "google", "custom")
FINDING_STATES = ("open", "confirmed", "false_positive", "accepted_risk", "fixed")


class ProviderCreate(BaseModel):
    kind: str
    name: str
    api_key: str
    base_url: str | None = None


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    name: str
    base_url: str | None
    status: str
    last_verified_at: datetime | None
    created_at: datetime


class ModelInfo(BaseModel):
    id: str
    display_name: str | None = None


class TargetCreate(BaseModel):
    name: str
    git_url: str | None = None
    local_path: str | None = None


class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    git_url: str | None
    local_path: str | None
    created_at: datetime


class ScanCreate(BaseModel):
    target_id: int
    provider_id: int
    model_id: str
    application_id: str | None = None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_id: int
    provider_id: int
    model_id: str
    application_id: str
    status: str
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ScanDetail(ScanOut):
    estimate_output: str | None
    report_path: str | None
    sarif_path: str | None


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    rule_id: str | None
    title: str
    message: str | None
    severity: str
    cwe: str | None
    file: str | None
    line: int | None
    state: str
    created_at: datetime


class FindingStateUpdate(BaseModel):
    state: str


class Metrics(BaseModel):
    total_scans: int
    scans_by_status: dict[str, int]
    total_findings: int
    findings_by_severity: dict[str, int]
    findings_by_state: dict[str, int]
    top_cwes: list[dict[str, int | str]]
    recent_scans: list[ScanOut]
