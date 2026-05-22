#!/usr/bin/env python3
"""AgentSoul persistence maintenance: retention + compaction.

This utility is safe to run on live systems. Use --dry-run first to preview
record impact before applying changes.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict


@dataclass
class RetentionPolicy:
    interactions_days: int = 180
    audit_days: int = 365
    keep_latest_exports: int = 50


class PersistenceMaintenance:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cur.fetchone() is not None

    def _count_before_date(
        self, conn: sqlite3.Connection, table: str, date_column: str, iso_cutoff: str
    ) -> int:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {date_column} < ?",
            (iso_cutoff,),
        ).fetchone()
        return int(row[0]) if row else 0

    def _delete_before_date(
        self, conn: sqlite3.Connection, table: str, date_column: str, iso_cutoff: str
    ) -> int:
        cur = conn.execute(
            f"DELETE FROM {table} WHERE {date_column} < ?",
            (iso_cutoff,),
        )
        return cur.rowcount

    def run(self, policy: RetentionPolicy, dry_run: bool, do_vacuum: bool) -> Dict[str, int]:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        now = datetime.now(timezone.utc)
        interactions_cutoff = (now - timedelta(days=policy.interactions_days)).isoformat()
        audit_cutoff = (now - timedelta(days=policy.audit_days)).isoformat()

        report: Dict[str, int] = {
            "interactions_pruned": 0,
            "audit_pruned": 0,
            "exports_pruned": 0,
            "vacuum_ran": 0,
        }

        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA foreign_keys=ON")

            if self._table_exists(conn, "agent_soul_interactions"):
                count = self._count_before_date(
                    conn,
                    "agent_soul_interactions",
                    "timestamp",
                    interactions_cutoff,
                )
                if dry_run:
                    report["interactions_pruned"] = count
                else:
                    report["interactions_pruned"] = self._delete_before_date(
                        conn,
                        "agent_soul_interactions",
                        "timestamp",
                        interactions_cutoff,
                    )

            if self._table_exists(conn, "agent_soul_audit"):
                count = self._count_before_date(
                    conn,
                    "agent_soul_audit",
                    "timestamp",
                    audit_cutoff,
                )
                if dry_run:
                    report["audit_pruned"] = count
                else:
                    report["audit_pruned"] = self._delete_before_date(
                        conn,
                        "agent_soul_audit",
                        "timestamp",
                        audit_cutoff,
                    )

            if self._table_exists(conn, "agent_soul_exports"):
                total_row = conn.execute(
                    "SELECT COUNT(*) FROM agent_soul_exports"
                ).fetchone()
                total_exports = int(total_row[0]) if total_row else 0
                if total_exports > policy.keep_latest_exports:
                    to_prune = total_exports - policy.keep_latest_exports
                    if dry_run:
                        report["exports_pruned"] = to_prune
                    else:
                        cur = conn.execute(
                            """
                            DELETE FROM agent_soul_exports
                            WHERE id IN (
                                SELECT id FROM agent_soul_exports
                                ORDER BY exported_at ASC
                                LIMIT ?
                            )
                            """,
                            (to_prune,),
                        )
                        report["exports_pruned"] = cur.rowcount

            if not dry_run:
                conn.commit()

            if not dry_run and do_vacuum:
                conn.execute("PRAGMA wal_checkpoint(FULL)")
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                report["vacuum_ran"] = 1

        finally:
            conn.close()

        return report


def _default_db_path() -> Path:
    p1 = Path.home() / "LLM" / "pocketbase" / "pb_data" / "data.db"
    p2 = Path.home() / "pocketbase" / "pb_data" / "data.db"
    return p1 if p1.exists() else p2


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentSoul retention and compaction utility")
    parser.add_argument("--db-path", type=Path, default=_default_db_path())
    parser.add_argument("--interactions-days", type=int, default=180)
    parser.add_argument("--audit-days", type=int, default=365)
    parser.add_argument("--keep-latest-exports", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-vacuum", action="store_true")
    args = parser.parse_args()

    policy = RetentionPolicy(
        interactions_days=args.interactions_days,
        audit_days=args.audit_days,
        keep_latest_exports=args.keep_latest_exports,
    )

    runner = PersistenceMaintenance(args.db_path)
    result = runner.run(policy, dry_run=args.dry_run, do_vacuum=not args.skip_vacuum)

    print(json.dumps({
        "db_path": str(args.db_path),
        "dry_run": args.dry_run,
        "policy": {
            "interactions_days": policy.interactions_days,
            "audit_days": policy.audit_days,
            "keep_latest_exports": policy.keep_latest_exports,
        },
        "result": result,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
