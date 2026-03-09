from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunConfig:
    raw: dict[str, Any]
    config_path: Path
    project_root: Path

    @property
    def run_name(self) -> str:
        return str(self.raw.get("run_name", "trade_wizards_run")).strip() or "trade_wizards_run"

    def section(self, name: str) -> dict[str, Any]:
        value = self.raw.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(f"Config section '{name}' must be an object/dict.")
        return value

    def resolve_path(self, path_value: str | None, default: Path) -> Path:
        if not path_value:
            return default
        path = Path(path_value)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()


def load_config(config_path: str | Path) -> RunConfig:
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a JSON object.")

    project_root = path.parents[2]
    return RunConfig(raw=raw, config_path=path, project_root=project_root)

