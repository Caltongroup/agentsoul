#!/usr/bin/env python3
"""
AgentSoul Persistence Schema — Core data model.
Bootstraps all required tables in PocketBase SQLite backend.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def init_schema(db_path: Path):
    """Create all required tables."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    tables = {
        "agent_soul_memories": """
            CREATE TABLE IF NOT EXISTS agent_soul_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                data TEXT NOT NULL,
                importance REAL DEFAULT 1.0,
                decay_factor REAL DEFAULT 1.0,
                last_accessed TEXT,
                created TEXT NOT NULL,
                updated TEXT NOT NULL,
                UNIQUE(agent_id, memory_type, entity_id)
            )
        """,
        "agent_soul_interactions": """
            CREATE TABLE IF NOT EXISTS agent_soul_interactions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                interaction_type TEXT,
                message TEXT,
                response TEXT,
                sentiment REAL,
                timestamp TEXT NOT NULL,
                created TEXT NOT NULL
            )
        """,
        "agent_soul_exports": """
            CREATE TABLE IF NOT EXISTS agent_soul_exports (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                export_name TEXT,
                encrypted_payload TEXT NOT NULL,
                encryption_metadata TEXT,
                exported_at TEXT NOT NULL,
                exported_by TEXT,
                created TEXT NOT NULL,
                updated TEXT NOT NULL
            )
        """,
        "agent_soul_audit": """
            CREATE TABLE IF NOT EXISTS agent_soul_audit (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_id TEXT,
                actor TEXT,
                changes TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL,
                created TEXT NOT NULL
            )
        """,
        "agent_soul_embeddings": """
            CREATE TABLE IF NOT EXISTS agent_soul_embeddings (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_id TEXT NOT NULL,
                embedding BLOB,
                similarity_group TEXT,
                created TEXT NOT NULL,
                FOREIGN KEY(memory_id) REFERENCES agent_soul_memories(id)
            )
        """,
        "agent_soul_traits": """
            CREATE TABLE IF NOT EXISTS agent_soul_traits (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                trait_name TEXT NOT NULL,
                trait_value TEXT,
                confidence REAL,
                extracted_from TEXT,
                created TEXT NOT NULL,
                updated TEXT NOT NULL,
                UNIQUE(agent_id, entity_id, trait_name)
            )
        """,
    }

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_memories_agent ON agent_soul_memories(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_memories_entity ON agent_soul_memories(entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_interactions_agent ON agent_soul_interactions(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_agent ON agent_soul_audit(agent_id)",
    ]

    try:
        for table_name, schema in tables.items():
            cursor.execute(schema)
            print(f"✓ Table '{table_name}' ready")

        for index_sql in indexes:
            cursor.execute(index_sql)
        print(f"✓ Indexes created")

        conn.commit()
        conn.close()
        print("\n✅ Schema initialized successfully")
        return True

    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print(f"ℹ Tables already exist: {e}")
            conn.close()
            return True
        else:
            print(f"❌ Error: {e}")
            conn.close()
            return False


if __name__ == "__main__":
    print("AgentSoul Persistence Schema Bootstrap\n")
    db_path = Path.home() / "pocketbase" / "pb_data" / "data.db"
    init_schema(db_path)
