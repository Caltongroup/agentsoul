#!/usr/bin/env python3
"""
AgentSoul SDK — Framework-agnostic Python interface.
Works with Hermes, LangGraph, CrewAI, AutoGen, etc.
<10 lines of code to integrate any agent.
"""

import json
import requests
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets


class AgentSoul:
    """
    ONE-LINER INTEGRATION:
    soul = AgentSoul.from_rest("http://localhost:5001", agent_id="clerk_001", token="demo")
    """

    def __init__(self, agent_id: str, backend_type: str = "rest", **kwargs):
        self.agent_id = agent_id
        self.backend_type = backend_type
        self._config = kwargs

    @staticmethod
    def from_rest(url: str, agent_id: str, token: str, **kwargs) -> "AgentSoul":
        """Initialize from REST backend (cloud or local API)."""
        return AgentSoul(agent_id, backend_type="rest", url=url, token=token, **kwargs)

    @staticmethod
    def from_sqlite(db_path: str, agent_id: str, **kwargs) -> "AgentSoul":
        """Initialize from local SQLite (standalone mode)."""
        return AgentSoul(agent_id, backend_type="sqlite", db_path=db_path, **kwargs)

    @staticmethod
    def from_pocketbase(pb_url: str, agent_id: str, token: str, **kwargs) -> "AgentSoul":
        """Initialize from PocketBase (preferred for production)."""
        return AgentSoul(agent_id, backend_type="pocketbase", pb_url=pb_url, token=token, **kwargs)

    # ============ MEMORY OPERATIONS ============

    def remember(self, memory_type: str, entity_id: str, data: Dict[str, Any]) -> str:
        """Store a memory."""
        if self.backend_type == "rest":
            resp = requests.post(
                f"{self._config['url']}/api/memory/store",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={
                    "agent_id": self.agent_id,
                    "memory_type": memory_type,
                    "entity_id": entity_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return resp.json().get("memory_id")
        elif self.backend_type == "sqlite":
            return self._sqlite_remember(memory_type, entity_id, data)

    def recall(
        self, memory_type: str, entity_id: str, consolidate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Retrieve memory with optional consolidation (decay + summarization)."""
        if self.backend_type == "rest":
            resp = requests.get(
                f"{self._config['url']}/api/memory/recall",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={
                    "agent_id": self.agent_id,
                    "memory_type": memory_type,
                    "entity_id": entity_id,
                    "consolidate": consolidate,
                },
            )
            return resp.json().get("memory")
        elif self.backend_type == "sqlite":
            return self._sqlite_recall(memory_type, entity_id, consolidate)

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing memory record."""
        if self.backend_type == "rest":
            resp = requests.patch(
                f"{self._config['url']}/api/memory/{memory_id}",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json=updates,
            )
            return resp.status_code == 200

    def forget(self, memory_id: str) -> bool:
        """Delete a memory record (GDPR compliance)."""
        if self.backend_type == "rest":
            resp = requests.delete(
                f"{self._config['url']}/api/memory/{memory_id}",
                headers={"Authorization": f"Bearer {self._config['token']}"},
            )
            return resp.status_code == 200

    # ============ SOUL PORTABILITY ============

    def export_soul(self, passphrase: str) -> Dict[str, Any]:
        """Export complete soul as encrypted artifact."""
        if self.backend_type == "rest":
            resp = requests.post(
                f"{self._config['url']}/api/soul/export",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={"agent_id": self.agent_id, "passphrase": passphrase},
            )
            return resp.json().get("artifact")
        elif self.backend_type == "sqlite":
            return self._sqlite_export_soul(passphrase)

    def import_soul(self, artifact: Dict[str, Any], passphrase: str) -> bool:
        """Import encrypted soul artifact (e.g., from Mac to RPi5)."""
        if self.backend_type == "rest":
            resp = requests.post(
                f"{self._config['url']}/api/soul/import",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={
                    "agent_id": self.agent_id,
                    "artifact": artifact,
                    "passphrase": passphrase,
                },
            )
            return resp.status_code == 200
        elif self.backend_type == "sqlite":
            return self._sqlite_import_soul(artifact, passphrase)

    # ============ SYSTEM PROMPT INJECTION ============

    def get_system_context(self, entity_id: str) -> str:
        """Get consolidated system prompt for current interaction."""
        if self.backend_type == "rest":
            resp = requests.get(
                f"{self._config['url']}/api/soul/system-prompt",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={"agent_id": self.agent_id, "entity_id": entity_id},
            )
            return resp.json().get("system_prompt", "")
        elif self.backend_type == "sqlite":
            return self._sqlite_system_context(entity_id)

    # ============ AUDIT & COMPLIANCE ============

    def log_interaction(self, entity_id: str, action: str, details: Dict[str, Any]) -> str:
        """Log agent action for audit trail."""
        if self.backend_type == "rest":
            resp = requests.post(
                f"{self._config['url']}/api/audit/log",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={
                    "agent_id": self.agent_id,
                    "entity_id": entity_id,
                    "action": action,
                    "details": details,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            return resp.json().get("log_id")

    def get_audit_trail(self, entity_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit history for compliance."""
        if self.backend_type == "rest":
            resp = requests.get(
                f"{self._config['url']}/api/audit/trail",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={
                    "agent_id": self.agent_id,
                    "entity_id": entity_id,
                    "limit": limit,
                },
            )
            return resp.json().get("audit_trail", [])

    # ============ SQLITE BACKEND (STANDALONE) ============

    def _sqlite_remember(
        self, memory_type: str, entity_id: str, data: Dict[str, Any]
    ) -> str:
        """Store memory in SQLite."""
        conn = sqlite3.connect(
            str(self._config.get("db_path", Path.home() / "pocketbase" / "pb_data" / "data.db"))
        )
        cursor = conn.cursor()

        memory_id = secrets.token_hex(16)
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO agent_soul_memories
            (id, agent_id, memory_type, entity_id, data, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (memory_id, self.agent_id, memory_type, entity_id, json.dumps(data), now, now),
        )

        conn.commit()
        conn.close()
        return memory_id

    def _sqlite_recall(
        self, memory_type: str, entity_id: str, consolidate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Retrieve memory from SQLite."""
        conn = sqlite3.connect(
            str(self._config.get("db_path", Path.home() / "pocketbase" / "pb_data" / "data.db"))
        )
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM agent_soul_memories
            WHERE agent_id = ? AND memory_type = ? AND entity_id = ?
            ORDER BY updated DESC LIMIT 1
        """,
            (self.agent_id, memory_type, entity_id),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row["data"])
        return None

    def _sqlite_export_soul(self, passphrase: str) -> Dict[str, Any]:
        """Export all agent memories as encrypted artifact."""
        conn = sqlite3.connect(
            str(self._config.get("db_path", Path.home() / "pocketbase" / "pb_data" / "data.db"))
        )
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agent_soul_memories WHERE agent_id = ?", (self.agent_id,))
        memories = [dict(row) for row in cursor.fetchall()]
        conn.close()

        soul_data = {
            "agent_id": self.agent_id,
            "exported_at": datetime.now().isoformat(),
            "memories": memories,
        }

        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(12)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = kdf.derive(passphrase.encode())

        plaintext = json.dumps(soul_data).encode()
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)

        return {
            "format_version": "1.0",
            "agent_id": self.agent_id,
            "encrypted_payload": base64.b64encode(ciphertext).decode(),
            "encryption_metadata": {
                "algorithm": "AES-256-GCM",
                "salt": base64.b64encode(salt).decode(),
                "nonce": base64.b64encode(nonce).decode(),
            },
            "artifact_created": datetime.now().isoformat(),
        }

    def _sqlite_import_soul(self, artifact: Dict[str, Any], passphrase: str) -> bool:
        """Import encrypted soul artifact."""
        try:
            ciphertext = base64.b64decode(artifact["encrypted_payload"])
            salt = base64.b64decode(artifact["encryption_metadata"]["salt"])
            nonce = base64.b64decode(artifact["encryption_metadata"]["nonce"])

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = kdf.derive(passphrase.encode())

            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            soul_data = json.loads(plaintext.decode())

            conn = sqlite3.connect(
                str(self._config.get("db_path", Path.home() / "pocketbase" / "pb_data" / "data.db"))
            )
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            for memory in soul_data.get("memories", []):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO agent_soul_memories
                    (id, agent_id, memory_type, entity_id, data, created, updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        secrets.token_hex(16),
                        self.agent_id,
                        memory.get("memory_type"),
                        memory.get("entity_id"),
                        memory.get("data"),
                        now,
                        now,
                    ),
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False

    def _sqlite_system_context(self, entity_id: str) -> str:
        """Generate system prompt from consolidated memory."""
        memory = self._sqlite_recall("entity_profile", entity_id, consolidate=True)
        if not memory:
            return "You are a helpful agent with no prior memory of this entity."

        return f"""
You are serving {entity_id}.

CONTEXT (consolidated from agent memory):
{json.dumps(memory, indent=2)}

Provide responses consistent with this context.
"""
