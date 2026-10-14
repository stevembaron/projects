"""Run every enabled source. Sources run in parallel; each host is paced on its own."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .adapters import SourceReport, collect
from .net import Client


def load_sources(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources", []) if isinstance(payload, dict) else []
    ids = [s.get("id") for s in sources]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates or not all(ids):
        raise ValueError(f"Every source needs a unique id (duplicates: {sorted(d for d in duplicates if d)})")
    return sources


def run(sources: list[dict[str, Any]], observed_at: str, workers: int = 6, only: set[str] | None = None,
        client_factory=Client) -> list[SourceReport]:
    selected = [s for s in sources if not only or s["id"] in only]

    def one(source: dict[str, Any]) -> SourceReport:
        return collect(source, client_factory(), observed_at)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(one, selected))
