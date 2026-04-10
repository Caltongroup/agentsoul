#!/usr/bin/env python3
"""
AgentSoul Encryption Engine — AES-256-GCM serialization + export.
Encrypts identity, memory, interactions, and audit trail.
Stores encryption metadata for recovery.
"""

import os
import json
import base64
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets


class SoulEncryption:
    """Manages encryption/decryption of AgentSoul artifacts."""

    ALGORITHM = "AES-256-GCM"
    NONCE_SIZE = 12  # 96-bit nonce (GCM standard)
    TAG_SIZE = 16  # 128-bit auth tag
    SALT_SIZE = 16  # 128-bit salt

    @staticmethod
    def derive_key(passphrase: str, salt: bytes) -> bytes:
        """Derive 256-bit key from passphrase using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=480000,  # NIST recommendation (2024)
        )
        return kdf.derive(passphrase.encode())

    @staticmethod
    def encrypt_soul(soul_data: Dict[str, Any], passphrase: str) -> Tuple[bytes, Dict[str, Any]]:
        """Encrypt soul data and return (ciphertext, metadata)."""

        # Generate random salt and nonce
        salt = secrets.token_bytes(SoulEncryption.SALT_SIZE)
        nonce = secrets.token_bytes(SoulEncryption.NONCE_SIZE)

        # Derive encryption key
        key = SoulEncryption.derive_key(passphrase, salt)

        # Serialize soul to JSON
        plaintext = json.dumps(soul_data).encode()

        # Encrypt using AES-256-GCM
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)

        # Metadata for decryption
        metadata = {
            "algorithm": SoulEncryption.ALGORITHM,
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "timestamp": datetime.now().isoformat(),
        }

        return ciphertext, metadata

    @staticmethod
    def decrypt_soul(ciphertext: bytes, passphrase: str, metadata: Dict[str, Any]) -> Dict[str, Any]:\n        """Decrypt soul data."""

        # Recover salt and nonce
        salt = base64.b64decode(metadata["salt"])
        nonce = base64.b64decode(metadata["nonce"])

        # Derive key
        key = SoulEncryption.derive_key(passphrase, salt)

        # Decrypt
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)

        return json.loads(plaintext.decode())


class AgentSoulExporter:
    """Exports complete AgentSoul as encrypted artifact."""

    def __init__(self, agent_id: str, db_path: Path):
        self.agent_id = agent_id
        self.db_path = db_path

    def gather_soul_data(self) -> Dict[str, Any]:
        """Aggregate all soul components from database."""

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        soul_data = {
            "agent_id": self.agent_id,
            "exported_at": datetime.now().isoformat(),
            "components": {},
        }

        # Fetch all memories
        try:
            cursor.execute("SELECT * FROM agent_soul_memories WHERE agent_id = ?", (self.agent_id,))
            soul_data["components"]["memories"] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            soul_data["components"]["memories"] = []

        # Fetch interactions
        try:
            cursor.execute("SELECT * FROM agent_soul_interactions WHERE agent_id = ?", (self.agent_id,))
            soul_data["components"]["interactions"] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            soul_data["components"]["interactions"] = []

        # Fetch audit trail
        try:
            cursor.execute(
                "SELECT * FROM agent_soul_audit WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 100",
                (self.agent_id,),
            )
            soul_data["components"]["audit_log"] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            soul_data["components"]["audit_log"] = []

        conn.close()
        return soul_data

    def export_soul(self, passphrase: str = None) -> Dict[str, Any]:
        """Export encrypted soul artifact."""

        if passphrase is None:
            passphrase = "default_dev_passphrase"

        # Gather all soul components
        soul_data = self.gather_soul_data()

        # Encrypt
        ciphertext, metadata = SoulEncryption.encrypt_soul(soul_data, passphrase)

        # Create export artifact
        artifact = {
            "format_version": "1.0",
            "agent_id": self.agent_id,
            "encrypted_payload": base64.b64encode(ciphertext).decode(),
            "encryption_metadata": metadata,
            "artifact_created": datetime.now().isoformat(),
        }

        return artifact

    def save_export_to_db(self, artifact: Dict[str, Any], export_name: str) -> bool:
        """Save export to database for recovery."""

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO agent_soul_exports
                (id, agent_id, export_name, encrypted_payload, encryption_metadata, exported_at, exported_by, created, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    secrets.token_hex(16),
                    self.agent_id,
                    export_name,
                    artifact["encrypted_payload"],
                    json.dumps(artifact["encryption_metadata"]),
                    datetime.now().isoformat(),
                    "system",
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving export: {e}")
            return False


class AgentSoulImporter:
    """Imports encrypted Soul artifact back into system."""

    def __init__(self, artifact: Dict[str, Any], db_path: Path):
        self.artifact = artifact
        self.db_path = db_path

    def import_soul(self, passphrase: str) -> bool:
        """Decrypt and import soul back into database."""

        try:
            # Decode ciphertext
            ciphertext = base64.b64decode(self.artifact["encrypted_payload"])

            # Decrypt
            soul_data = SoulEncryption.decrypt_soul(
                ciphertext, passphrase, self.artifact["encryption_metadata"]
            )

            # Import back to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Insert memories
            for memory in soul_data["components"].get("memories", []):
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO agent_soul_memories
                        (id, agent_id, memory_type, entity_id, data, created, updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            secrets.token_hex(16),
                            memory.get("agent_id"),
                            memory.get("memory_type"),
                            memory.get("entity_id"),
                            memory.get("data"),
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )
                except:
                    pass

            # Insert interactions
            for interaction in soul_data["components"].get("interactions", []):
                try:
                    cursor.execute(
                        """
                        INSERT INTO agent_soul_interactions
                        (id, agent_id, entity_id, interaction_type, message, response, timestamp, created)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            secrets.token_hex(16),
                            interaction.get("agent_id"),
                            interaction.get("entity_id"),
                            interaction.get("interaction_type"),
                            interaction.get("message"),
                            interaction.get("response"),
                            interaction.get("timestamp"),
                            datetime.now().isoformat(),
                        ),
                    )
                except:
                    pass

            conn.commit()
            conn.close()
            print("✅ Soul imported successfully")
            return True

        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False
