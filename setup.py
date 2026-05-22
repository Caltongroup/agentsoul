#!/usr/bin/env python3
"""
AgentSoul Setup Script
Initializes LanceDB directory and basic configuration.
"""

from pathlib import Path
import lancedb

DEFAULT_LANCEDB_PATH = Path.home() / "LLM" / "models" / "lancedb" / "agent_memory"


def setup_lancedb():
    """Initialize LanceDB directory and create empty table if needed."""
    db_path = DEFAULT_LANCEDB_PATH
    db_path.mkdir(parents=True, exist_ok=True)

    db = lancedb.connect(str(db_path))

    try:
        # Create empty table if it doesn't exist
        if "agent_memory" not in db.table_names():
            import pandas as pd
            df = pd.DataFrame({
                "id": pd.Series([], dtype="str"),
                "content": pd.Series([], dtype="str"),
                "role": pd.Series([], dtype="str"),
                "source": pd.Series([], dtype="str"),
                "timestamp": pd.Series([], dtype="str"),
                "importance": pd.Series([], dtype="float"),
                "source_session_id": pd.Series([], dtype="str"),
            })
            db.create_table("agent_memory", df)
            print("✓ Created LanceDB table: agent_memory")
        else:
            print("✓ LanceDB table 'agent_memory' already exists")
    except Exception as e:
        print(f"⚠ LanceDB setup note: {e}")

    print(f"✓ LanceDB path ready: {db_path}")
    return db_path


if __name__ == "__main__":
    print("AgentSoul Setup\n")
    setup_lancedb()
    print("\n✅ Basic setup complete")