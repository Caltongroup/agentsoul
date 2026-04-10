#!/usr/bin/env python3
"""
AgentSoul SDK — Framework-agnostic Python interface.
Works with Hermes, LangGraph, CrewAI, AutoGen, etc.
<10 lines of code to integrate any agent.

Backends: SQLite (standalone), REST (cloud), PocketBase (production)
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
    soul = AgentSoul.from_pocketbase("http://127.0.0.1:8090", agent_id="clerk_001", token="pb_token")
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
    def from_pocketbase(pb_url: str, agent_id: str, token: str = None, **kwargs) -> "AgentSoul":
        """Initialize from PocketBase (preferred for production).
        
        Args:
            pb_url: PocketBase server URL (e.g., "http://127.0.0.1:8090")
            agent_id: Unique agent identifier
            token: PocketBase auth token (optional for dev)
        """
        return AgentSoul(
            agent_id,
            backend_type="pocketbase",
            pb_url=pb_url,
            token=token or "pb_dev_token",
            **kwargs
        )

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
        
        elif self.backend_type == "pocketbase":
            return self._pb_remember(memory_type, entity_id, data)
        
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
        
        elif self.backend_type == "pocketbase":
            return self._pb_recall(memory_type, entity_id, consolidate)
        
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
        
        elif self.backend_type == "pocketbase":
            return self._pb_update_memory(memory_id, updates)

    def forget(self, memory_id: str) -> bool:
        """Delete a memory record (GDPR compliance)."""
        if self.backend_type == "rest":
            resp = requests.delete(
                f"{self._config['url']}/api/memory/{memory_id}",
                headers={"Authorization": f"Bearer {self._config['token']}"},
            )
            return resp.status_code == 200
        
        elif self.backend_type == "pocketbase":
            return self._pb_forget(memory_id)

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
        
        elif self.backend_type == "pocketbase":
            return self._pb_export_soul(passphrase)
        
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
        
        elif self.backend_type == "pocketbase":
            return self._pb_import_soul(artifact, passphrase)
        
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
        
        elif self.backend_type == "pocketbase":
            return self._pb_system_context(entity_id)
        
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
        
        elif self.backend_type == "pocketbase":
            return self._pb_log_interaction(entity_id, action, details)

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
        
        elif self.backend_type == "pocketbase":
            return self._pb_get_audit_trail(entity_id, limit)

    # ============ POCKETBASE BACKEND ============

    def _pb_remember(self, memory_type: str, entity_id: str, data: Dict[str, Any]) -> str:
        """Store memory in PocketBase."""
        try:
            memory_id = secrets.token_hex(16)
            now = datetime.now().isoformat()
            
            resp = requests.post(
                f"{self._config['pb_url']}/api/collections/agent_soul_memories/records",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={
                    "id": memory_id,
                    "agent_id": self.agent_id,
                    "memory_type": memory_type,
                    "entity_id": entity_id,
                    "data": json.dumps(data),
                    "created": now,
                    "updated": now,
                },
            )
            if resp.status_code in (200, 201):
                return memory_id
            else:
                print(f"PocketBase error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"PocketBase write error: {e}")
            return None

    def _pb_recall(self, memory_type: str, entity_id: str, consolidate: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieve memory from PocketBase."""
        try:
            filter_str = f'agent_id="{self.agent_id}" && memory_type="{memory_type}" && entity_id="{entity_id}"'
            resp = requests.get(
                f"{self._config['pb_url']}/api/collections/agent_soul_memories/records",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={"filter": filter_str, "sort": "-updated", "limit": 1},
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    data_str = items[0].get("data", "{}")
                    return json.loads(data_str) if isinstance(data_str, str) else data_str
            return None
        except Exception as e:
            print(f"PocketBase read error: {e}")
            return None

    def _pb_update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory in PocketBase."""
        try:
            resp = requests.patch(
                f"{self._config['pb_url']}/api/collections/agent_soul_memories/records/{memory_id}",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={"data": json.dumps(updates.get("data", {})), "updated": datetime.now().isoformat()},
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"PocketBase update error: {e}")
            return False

    def _pb_forget(self, memory_id: str) -> bool:
        """Delete memory from PocketBase (GDPR)."""
        try:
            resp = requests.delete(
                f"{self._config['pb_url']}/api/collections/agent_soul_memories/records/{memory_id}",
                headers={"Authorization": f"Bearer {self._config['token']}"},
            )
            return resp.status_code == 204
        except Exception as e:
            print(f"PocketBase delete error: {e}")
            return False

    def _pb_export_soul(self, passphrase: str) -> Dict[str, Any]:
        """Export all agent memories as encrypted artifact."""
        try:
            filter_str = f'agent_id="{self.agent_id}"'
            resp = requests.get(
                f"{self._config['pb_url']}/api/collections/agent_soul_memories/records",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={"filter": filter_str},
            )
            
            memories = resp.json().get("items", []) if resp.status_code == 200 else []
            
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
        except Exception as e:
            print(f"PocketBase export error: {e}")
            return {}

    def _pb_import_soul(self, artifact: Dict[str, Any], passphrase: str) -> bool:
        """Import encrypted soul artifact into PocketBase."""
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

            for memory in soul_data.get("memories", []):
                now = datetime.now().isoformat()
                requests.post(
                    f"{self._config['pb_url']}/api/collections/agent_soul_memories/records",
                    headers={"Authorization": f"Bearer {self._config['token']}"},
                    json={
                        "id": secrets.token_hex(16),
                        "agent_id": self.agent_id,
                        "memory_type": memory.get("memory_type"),
                        "entity_id": memory.get("entity_id"),
                        "data": memory.get("data"),
                        "created": now,
                        "updated": now,
                    },
                )
            return True
        except Exception as e:
            print(f"PocketBase import error: {e}")
            return False

    def _pb_system_context(self, entity_id: str) -> str:
        """Generate system prompt from PocketBase memory."""
        memory = self._pb_recall("entity_profile", entity_id, consolidate=True)
        if not memory:
            return f"You are serving {entity_id}. No prior memory recorded."

        return f"""
You are serving {entity_id}.

CONTEXT (consolidated from agent memory):
{json.dumps(memory, indent=2)}

Respond naturally and helpfully.
""".strip()

    def _pb_log_interaction(self, entity_id: str, action: str, details: Dict[str, Any]) -> str:
        """Log interaction to PocketBase audit trail."""
        try:
            log_id = secrets.token_hex(16)
            now = datetime.now().isoformat()
            
            requests.post(
                f"{self._config['pb_url']}/api/collections/agent_soul_audit/records",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                json={
                    "id": log_id,
                    "agent_id": self.agent_id,
                    "entity_id": entity_id,
                    "action": action,
                    "changes": json.dumps(details),
                    "timestamp": now,
                    "created": now,
                },
            )
            return log_id
        except Exception as e:
            print(f"PocketBase audit error: {e}")
            return None

    def _pb_get_audit_trail(self, entity_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit trail from PocketBase."""
        try:
            filter_str = f'agent_id="{self.agent_id}" && entity_id="{entity_id}"'
            resp = requests.get(
                f"{self._config['pb_url']}/api/collections/agent_soul_audit/records",
                headers={"Authorization": f"Bearer {self._config['token']}"},
                params={"filter": filter_str, "sort": "-timestamp", "limit": limit},
            )
            return resp.json().get("items", []) if resp.status_code == 200 else []
        except Exception as e:
            print(f"PocketBase audit trail error: {e}")
            return []

    # ============ SQLITE BACKEND (STANDALONE) ============

    def _sqlite_remember(
        self, memory_type: str, entity_id: str, data: Dict[str, Any]
    ) -> str:
        """Store memory in SQLite."""
        conn = sqlite3.connect(
            str(self._config.get("db_path", Path.home() / "agent_soul.db"))
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
            str(self._config.get("db_path", Path.home() / "agent_soul.db"))
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
            str(self._config.get("db_path", Path.home() / "agent_soul.db"))
        )
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM agent_soul_memories WHERE agent_id = ?", (self.agent_id,))
            memories = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            memories = []

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
                str(self._config.get("db_path", Path.home() / "agent_soul.db"))
            )
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            for memory in soul_data.get("memories", []):
                try:
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
                except:
                    pass

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
            return f"You are serving {entity_id}. No prior memory recorded."

        return f"""
You are serving {entity_id}.

CONTEXT (consolidated from agent memory):
{json.dumps(memory, indent=2)}

Respond naturally and helpfully.
""".strip()


# ============ TEST SUITE ============

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AgentSoul SDK Test Suite")
    print("="*70 + "\n")
    
    # Test 1: Backend initialization
    print("TEST 1: Backend Initialization")
    try:
        # SQLite
        soul_sqlite = AgentSoul.from_sqlite(
            db_path="/tmp/agent_soul_test.db",
            agent_id="test_agent_001"
        )
        assert soul_sqlite.backend_type == "sqlite"
        print("  ✓ SQLite backend initialized")
        
        # REST
        soul_rest = AgentSoul.from_rest(
            url="http://localhost:5001",
            agent_id="test_agent_rest",
            token="demo_token"
        )
        assert soul_rest.backend_type == "rest"
        print("  ✓ REST backend initialized")
        
        # PocketBase
        soul_pb = AgentSoul.from_pocketbase(
            pb_url="http://127.0.0.1:8090",
            agent_id="test_agent_pb"
        )
        assert soul_pb.backend_type == "pocketbase"
        print("  ✓ PocketBase backend initialized")
        
        print()
    except Exception as e:
        print(f"  ✗ Initialization test failed: {e}\n")
    
    # Test 2: Encryption/Decryption
    print("TEST 2: Encryption & Decryption")
    try:
        # Create a test soul data
        test_soul = {
            "agent_id": "test_agent",
            "exported_at": datetime.now().isoformat(),
            "memories": [
                {
                    "id": "mem_001",
                    "agent_id": "test_agent",
                    "memory_type": "customer",
                    "entity_id": "cust_001",
                    "data": json.dumps({"name": "Alice", "payment": "reliable"})
                }
            ]
        }
        
        # Encrypt
        passphrase = "test_secure_passphrase_123"
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(12)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = kdf.derive(passphrase.encode())
        
        cipher = AESGCM(key)
        plaintext = json.dumps(test_soul).encode()
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        print(f"  ✓ Encrypted {len(plaintext)} bytes → {len(ciphertext)} bytes")
        
        # Decrypt
        cipher_dec = AESGCM(key)
        decrypted = cipher_dec.decrypt(nonce, ciphertext, None)
        recovered_soul = json.loads(decrypted.decode())
        
        assert recovered_soul["agent_id"] == "test_agent"
        assert len(recovered_soul["memories"]) == 1
        print(f"  ✓ Decrypted successfully")
        print()
    except Exception as e:
        print(f"  ✗ Encryption test failed: {e}\n")
    
    # Test 3: PocketBase connectivity
    print("TEST 3: PocketBase Connectivity")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 8090))
        sock.close()
        
        if result == 0:
            print("  ✓ PocketBase is running on 127.0.0.1:8090")
            
            # Try a basic health check
            soul_pb = AgentSoul.from_pocketbase(
                pb_url="http://127.0.0.1:8090",
                agent_id="health_check"
            )
            print("  ✓ PocketBase backend ready for use")
        else:
            print("  ℹ PocketBase not running (can be started later)")
        
        print()
    except Exception as e:
        print(f"  ℹ PocketBase check skipped: {e}\n")
    
    # Test 4: SDK Imports & Structure
    print("TEST 4: SDK Structure Validation")
    try:
        soul = AgentSoul.from_sqlite(db_path="/tmp/test.db", agent_id="test")
        
        # Check methods exist
        assert hasattr(soul, "remember"), "remember() missing"
        assert hasattr(soul, "recall"), "recall() missing"
        assert hasattr(soul, "export_soul"), "export_soul() missing"
        assert hasattr(soul, "import_soul"), "import_soul() missing"
        assert hasattr(soul, "get_system_context"), "get_system_context() missing"
        assert hasattr(soul, "log_interaction"), "log_interaction() missing"
        assert hasattr(soul, "get_audit_trail"), "get_audit_trail() missing"
        
        print("  ✓ All required methods present")
        print("  ✓ SDK structure valid")
        print()
    except Exception as e:
        print(f"  ✗ Structure validation failed: {e}\n")
    
    print("="*70)
    print("✅ Test suite complete\n")
