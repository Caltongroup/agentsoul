#!/usr/bin/env python3
"""
AgentSoul REST API — Production-ready service for any agent framework.
Exposes SDK methods via HTTP + Bearer auth.
"""

from flask import Flask, request, jsonify
from functools import wraps
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

from .sdk import AgentSoul

app = Flask(__name__)
DB_PATH = Path.home() / "agent_soul.db"


# ============ AUTH ============


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token or token != "demo_token_dev":
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


# ============ MEMORY OPERATIONS ============


@app.route("/api/memory/store", methods=["POST"])
@require_auth
def store_memory():
    """Store a memory using AgentSoul SDK."""
    data = request.json or {}

    try:
        soul = AgentSoul.from_sqlite(
            db_path=str(DB_PATH), agent_id=data.get("agent_id", "unknown")
        )

        memory_id = soul.remember(
            memory_type=data["memory_type"],
            entity_id=data["entity_id"],
            data=data["data"],
        )

        return jsonify({"status": "success", "memory_id": memory_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/recall", methods=["GET"])
@require_auth
def recall_memory():
    """Retrieve memory with optional consolidation."""
    agent_id = request.args.get("agent_id", "unknown")
    memory_type = request.args.get("memory_type")
    entity_id = request.args.get("entity_id")
    consolidate = request.args.get("consolidate", "true").lower() == "true"

    try:
        soul = AgentSoul.from_sqlite(db_path=str(DB_PATH), agent_id=agent_id)
        memory = soul.recall(memory_type, entity_id, consolidate=consolidate)

        return jsonify({"status": "success", "memory": memory}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/<memory_id>", methods=["PATCH"])
@require_auth
def update_memory(memory_id):
    """Update a memory record."""
    data = request.json or {}

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE agent_soul_memories
            SET data = ?, updated = ?
            WHERE id = ?
        """,
            (json.dumps(data.get("data", {})), datetime.now().isoformat(), memory_id),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/<memory_id>", methods=["DELETE"])
@require_auth
def delete_memory(memory_id):
    """Delete a memory (GDPR compliance)."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM agent_soul_memories WHERE id = ?", (memory_id,))

        conn.commit()
        conn.close()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============ SOUL EXPORT / IMPORT ============


@app.route("/api/soul/export", methods=["POST"])
@require_auth
def export_soul():
    """Export agent soul as encrypted artifact."""
    data = request.json or {}
    agent_id = data.get("agent_id", "unknown")
    passphrase = data.get("passphrase", "default_dev")

    try:
        soul = AgentSoul.from_sqlite(db_path=str(DB_PATH), agent_id=agent_id)
        artifact = soul.export_soul(passphrase)

        return jsonify({"status": "success", "artifact": artifact}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/soul/import", methods=["POST"])
@require_auth
def import_soul():
    """Import encrypted soul artifact."""
    data = request.json or {}
    agent_id = data.get("agent_id", "unknown")
    artifact = data.get("artifact")
    passphrase = data.get("passphrase", "default_dev")

    if not artifact:
        return jsonify({"error": "No artifact provided"}), 400

    try:
        soul = AgentSoul.from_sqlite(db_path=str(DB_PATH), agent_id=agent_id)
        success = soul.import_soul(artifact, passphrase)

        return jsonify({"status": "success" if success else "error"}), 200 if success else 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ SYSTEM PROMPT INJECTION ============


@app.route("/api/soul/system-prompt", methods=["GET"])
@require_auth
def get_system_prompt():
    """Get consolidated system prompt for entity."""
    agent_id = request.args.get("agent_id", "unknown")
    entity_id = request.args.get("entity_id")

    try:
        soul = AgentSoul.from_sqlite(db_path=str(DB_PATH), agent_id=agent_id)
        system_prompt = soul.get_system_context(entity_id)

        return jsonify({"status": "success", "system_prompt": system_prompt}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ AUDIT & COMPLIANCE ============


@app.route("/api/audit/log", methods=["POST"])
@require_auth
def log_audit():
    """Log action for audit trail."""
    data = request.json or {}

    try:
        import secrets

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        log_id = secrets.token_hex(16)
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO agent_soul_audit
            (id, agent_id, action, entity_id, actor, changes, ip_address, timestamp, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                log_id,
                data.get("agent_id"),
                data.get("action"),
                data.get("entity_id"),
                data.get("actor", "system"),
                json.dumps(data.get("details", {})),
                request.remote_addr,
                now,
                now,
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "log_id": log_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/audit/trail", methods=["GET"])
@require_auth
def get_audit_trail():
    """Retrieve audit history."""
    agent_id = request.args.get("agent_id", "unknown")
    entity_id = request.args.get("entity_id")
    limit = int(request.args.get("limit", 100))

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM agent_soul_audit
            WHERE agent_id = ? AND entity_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (agent_id, entity_id, limit),
        )

        audit_trail = [
            {
                "id": row["id"],
                "action": row["action"],
                "actor": row["actor"],
                "timestamp": row["timestamp"],
                "changes": json.loads(row["changes"]) if row["changes"] else {},
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        return jsonify({"status": "success", "audit_trail": audit_trail}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ HEALTH & STATUS ============


@app.route("/api/health", methods=["GET"])
def health():
    """Health check (no auth)."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agent_soul_memories")
        count = cursor.fetchone()[0]
        conn.close()

        return (
            jsonify(
                {"status": "healthy", "database": "connected", "total_memories": count}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/api/info", methods=["GET"])
def info():
    """API info (no auth)."""
    return (
        jsonify(
            {
                "service": "AgentSoul",
                "version": "1.0.0",
                "description": "Framework-agnostic agent persistence platform",
                "docs": "https://github.com/agentsoul/docs",
            }
        ),
        200,
    )


# ============ ERROR HANDLERS ============


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500


# ============ MAIN ============


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AgentSoul REST API v1.0.0")
    print("=" * 70)
    print("\nListening on http://0.0.0.0:5001")
    print("\nKey Endpoints:")
    print("  POST   /api/memory/store            (Bearer auth)")
    print("  GET    /api/memory/recall           (Bearer auth)")
    print("  POST   /api/soul/export             (Bearer auth)")
    print("  POST   /api/soul/import             (Bearer auth)")
    print("  GET    /api/soul/system-prompt      (Bearer auth)")
    print("  GET    /api/health                  (no auth)")
    print("\nAuth: Bearer token in Authorization header")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=5001, debug=False)
