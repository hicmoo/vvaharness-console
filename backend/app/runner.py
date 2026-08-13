"""Scan orchestration: clone target, generate config, run vvaharness, ingest SARIF."""

import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from . import sarif
from .config import settings
from .crypto import decrypt
from .db import SessionLocal
from .models import Finding, Provider, Scan, Target
from .profiles import generate_config
from .providers import GOOGLE_OPENAI_BASE_URL

_executor = ThreadPoolExecutor(max_workers=1)
_processes: dict[int, subprocess.Popen[bytes]] = {}
_lock = threading.Lock()


def _vvaharness_bin() -> str:
    candidate = Path(sys.executable).parent / "vvaharness"
    if candidate.exists():
        return str(candidate)
    return settings.vvaharness_bin


def _utcnow() -> datetime:
    return datetime.now(UTC)


def submit_scan(scan_id: int) -> None:
    _executor.submit(_run_scan_safe, scan_id)


def cancel_scan(scan_id: int) -> bool:
    with _lock:
        proc = _processes.get(scan_id)
    if proc and proc.poll() is None:
        proc.terminate()
        return True
    return False


def log_path_for(scan_id: int) -> Path:
    return settings.runs_dir / str(scan_id) / "scan.log"


def _set_status(scan_id: int, status: str, **fields: object) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        scan.status = status
        for key, value in fields.items():
            setattr(scan, key, value)
        db.commit()
    finally:
        db.close()


def _provider_env(provider: Provider) -> dict[str, str]:
    reserved = ("ANTHROPIC_API_KEY", "ANTHROPIC_SDK_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL")
    env = {k: v for k, v in os.environ.items() if k not in reserved}
    key = decrypt(provider.encrypted_key)
    if provider.kind == "anthropic":
        env["ANTHROPIC_SDK_API_KEY"] = key
        env["ANTHROPIC_API_KEY"] = key
        if provider.base_url:
            env["ANTHROPIC_SDK_BASE_URL"] = provider.base_url
    elif provider.kind == "openai":
        env["OPENAI_API_KEY"] = key
        if provider.base_url:
            env["OPENAI_BASE_URL"] = provider.base_url
    elif provider.kind == "google":
        env["OPENAI_API_KEY"] = key
        env["OPENAI_BASE_URL"] = provider.base_url or GOOGLE_OPENAI_BASE_URL
    elif provider.kind == "custom":
        env["OPENAI_API_KEY"] = key or "not-required"
        env["OPENAI_BASE_URL"] = provider.base_url or ""
    return env


def _resolve_target_path(target: Target, log: "_Log") -> Path:
    if target.local_path:
        path = Path(target.local_path).expanduser().resolve()
        if not path.is_dir():
            raise RuntimeError(f"target local path does not exist: {path}")
        return path
    if not target.git_url:
        raise RuntimeError("target has neither git_url nor local_path")
    clone_dir = settings.targets_dir / f"{target.id}"
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    log.write(f"cloning {target.git_url} -> {clone_dir}\n")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", target.git_url, str(clone_dir)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()[-2000:]}")
    return clone_dir


class _Log:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = path.open("a", buffering=1)

    def write(self, text: str) -> None:
        self._f.write(text)

    def close(self) -> None:
        self._f.close()


def _stream(scan_id: int, cmd: list[str], cwd: Path, env: dict[str, str], log: _Log) -> int:
    log.write(f"\n$ {' '.join(cmd)}\n")
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    with _lock:
        _processes[scan_id] = proc
    try:
        assert proc.stdout is not None
        for raw in proc.stdout:
            log.write(raw.decode(errors="replace"))
        return proc.wait()
    finally:
        with _lock:
            _processes.pop(scan_id, None)


def _newest(pattern: str, directory: Path) -> Path | None:
    matches = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    return matches[-1] if matches else None


def _run_scan_safe(scan_id: int) -> None:
    try:
        _run_scan(scan_id)
    except Exception as e:  # noqa: BLE001 - background job boundary
        _set_status(scan_id, "failed", error=str(e)[:4000], finished_at=_utcnow())


def _run_scan(scan_id: int) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        provider = db.get(Provider, scan.provider_id)
        target = db.get(Target, scan.target_id)
        if provider is None or target is None:
            raise RuntimeError("scan references a missing provider or target")
    finally:
        db.close()

    run_dir = settings.runs_dir / str(scan_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    log = _Log(log_path_for(scan_id))
    try:
        _set_status(scan_id, "cloning", started_at=_utcnow())
        target_path = _resolve_target_path(target, log)

        config_path = generate_config(run_dir, provider.kind, scan.model_id)
        env = _provider_env(provider)
        bin_path = _vvaharness_bin()

        _set_status(scan_id, "estimating")
        est = subprocess.run(
            [bin_path, "estimate", "--repo", str(target_path), "--config", str(config_path)],
            cwd=run_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
        )
        estimate_output = (est.stdout + est.stderr).strip()[-8000:]
        log.write(f"\n$ vvaharness estimate\n{estimate_output}\n")
        _set_status(scan_id, "scanning", estimate_output=estimate_output)

        code = _stream(
            scan_id,
            [
                bin_path,
                "scan",
                "--repo",
                str(target_path),
                "--application-id",
                scan.application_id,
                "--config",
                str(config_path),
                "--stop-after",
                "s9",
            ],
            run_dir,
            env,
            log,
        )
        if code != 0:
            raise RuntimeError(f"vvaharness scan exited with code {code} (see log)")

        _set_status(scan_id, "ingesting")
        scan_output_dir = target_path / "security-scan"
        sarif_file = _newest("*.sarif", scan_output_dir) if scan_output_dir.is_dir() else None
        report_file = _newest("*_report.md", scan_output_dir) if scan_output_dir.is_dir() else None

        sarif_copy = report_copy = None
        if sarif_file:
            sarif_copy = run_dir / sarif_file.name
            shutil.copy2(sarif_file, sarif_copy)
        if report_file:
            report_copy = run_dir / report_file.name
            shutil.copy2(report_file, report_copy)

        n = 0
        if sarif_copy:
            rows = sarif.parse_sarif(sarif_copy)
            db = SessionLocal()
            try:
                for row in rows:
                    db.add(Finding(scan_id=scan_id, **row))
                db.commit()
                n = len(rows)
            finally:
                db.close()
        log.write(f"\ningested {n} findings\n")

        _set_status(
            scan_id,
            "succeeded",
            finished_at=_utcnow(),
            sarif_path=str(sarif_copy) if sarif_copy else None,
            report_path=str(report_copy) if report_copy else None,
        )
    finally:
        log.close()
