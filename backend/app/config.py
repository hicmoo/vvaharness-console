from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    harness_repo: Path = Path.home() / "repos" / "visa-vulnerability-agentic-harness"
    vvaharness_bin: str = "vvaharness"

    model_config = {"env_prefix": "VVC_"}

    @property
    def db_path(self) -> Path:
        return self.data_dir / "console.db"

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def targets_dir(self) -> Path:
        return self.data_dir / "targets"

    @property
    def fernet_key_path(self) -> Path:
        return self.data_dir / ".fernet.key"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.runs_dir.mkdir(parents=True, exist_ok=True)
settings.targets_dir.mkdir(parents=True, exist_ok=True)
