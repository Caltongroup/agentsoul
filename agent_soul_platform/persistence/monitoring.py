#!/usr/bin/env python3
"""AgentSoul persistence monitoring utility.

Collects DB size and table-level record counts and optionally writes a snapshot.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


TABLES = [
    "agent_soul_memories",
    "agent_soul_interactions",
    "agent_soul_audit",
    "agent_soul_exports",
    "agent_soul_embeddings",
    "agent_soul_traits",
]


def _default_db_path() -> Path:
    p1 = Path.home() / "LLM" / "pocketbase" / "pb_data" / "data.db"
    p2 = Path.home() / "pocketbase" / "pb_data" / "data.db"
    return p1 if p1.exists() else p2


def _default_snapshot_path(db_path: Path) -> Path:
    return db_path.parent / "agentsoul_metrics_snapshot.json"


def collect_metrics(db_path: Path) -> Dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
        freelist_count = int(conn.execute("PRAGMA freelist_count").fetchone()[0])

        table_counts: Dict[str, int] = {}
        for table in TABLES:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if row:
                cnt = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                table_counts[table] = cnt

    finally:
        conn.close()

    file_bytes = db_path.stat().st_size
    allocated_bytes = page_count * page_size
    free_bytes = freelist_count * page_size

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "file_bytes": file_bytes,
        "allocated_bytes": allocated_bytes,
        "free_bytes": free_bytes,
        "table_counts": table_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentSoul DB growth and health metrics")
    parser.add_argument("--db-path", type=Path, default=_default_db_path())
    parser.add_argument("--snapshot-path", type=Path, default=None)
    parser.add_argument("--write-snapshot", action="store_true")
    parser.add_argument("--warn-db-mb", type=float, default=2048.0)
    args = parser.parse_args()

    snapshot_path = args.snapshot_path or _default_snapshot_path(args.db_path)
    metrics = collect_metrics(args.db_path)

    previous = None
    if snapshot_path.exists():
        try:
            previous = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except Exception:
            previous = None

    delta = {}
    if previous and "table_counts" in previous:
        prev_counts = previous.get("table_counts", {})
        for key, value in metrics["table_counts"].items():
            delta[f"delta_{key}"] = value - int(prev_counts.get(key, 0))

    metrics["delta"] = delta
    metrics["warn_db_size_exceeded"] = metrics["file_bytes"] > int(args.warn_db_mb * 1024 * 1024)

    if args.write_snapshot:
        snapshot_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        metrics["snapshot_written"] = str(snapshot_path)

    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
