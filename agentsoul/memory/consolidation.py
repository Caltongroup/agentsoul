#!/usr/bin/env python3
"""
AgentSoul Memory Consolidation — Importance-based decay + semantic compression.
Unlike time-only decay, this tracks business value and interaction patterns.
"""

import json
import sqlite3
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class ImportanceScoring:
    """Score memory importance based on business signals, not just time."""

    # Weight factors (tune per use case)
    WEIGHTS = {
        "recency": 0.15,  # Recent = fresh
        "frequency": 0.25,  # Often mentioned = important
        "interaction_count": 0.20,  # Many interactions = well-known
        "revenue_impact": 0.25,  # High-value customers = higher weight
        "customer_feedback": 0.15,  # Explicit signals
    }

    @staticmethod
    def compute_recency_score(timestamp_str: str) -> float:
        """Recency: 1.0 at 0 days, 0.5 at 30 days, 0.25 at 60 days."""
        try:
            record_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            age_days = (now - record_time).days
            return 0.5 ** (age_days / 30.0)  # 30-day half-life
        except:
            return 0.5

    @staticmethod
    def compute_frequency_score(mention_count: int, max_threshold: int = 50) -> float:
        """Frequency: logarithmic scale, saturates at ~50 mentions."""
        if mention_count <= 0:
            return 0.1
        return min(1.0, math.log(mention_count + 1) / math.log(max_threshold + 1))

    @staticmethod
    def compute_revenue_score(revenue_value: float, percentile_90th: float = 5000.0) -> float:
        """Revenue impact: high-value customers get higher score."""
        if revenue_value <= 0:
            return 0.3
        return min(1.0, revenue_value / percentile_90th)

    @staticmethod
    def compute_feedback_score(feedback_text: Optional[str]) -> float:
        """Feedback signal: explicit mentions boost importance."""
        if not feedback_text:
            return 0.5

        positive_signals = ["important", "critical", "always", "never", "key", "essential"]
        signal_count = sum(1 for signal in positive_signals if signal.lower() in feedback_text.lower())

        return min(1.0, 0.5 + (signal_count * 0.1))

    @classmethod
    def compute_overall_importance(cls, memory_record: Dict[str, Any]) -> float:
        """Compute final importance score (0-1)."""

        recency = cls.compute_recency_score(memory_record.get("updated", datetime.now().isoformat()))
        frequency = cls.compute_frequency_score(memory_record.get("mention_count", 1))
        interactions = cls.compute_frequency_score(memory_record.get("interaction_count", 0))
        revenue = cls.compute_revenue_score(memory_record.get("total_revenue", 0))
        feedback = cls.compute_feedback_score(memory_record.get("business_notes", ""))

        # Weighted sum
        score = (
            cls.WEIGHTS["recency"] * recency
            + cls.WEIGHTS["frequency"] * frequency
            + cls.WEIGHTS["interaction_count"] * interactions
            + cls.WEIGHTS["revenue_impact"] * revenue
            + cls.WEIGHTS["customer_feedback"] * feedback
        )

        return score


class SemanticCompression:
    """Compress memories while preserving semantic meaning."""

    @staticmethod
    def compress_memory(memories: List[Dict[str, Any]]) -> str:
        """Consolidate multiple memory fragments into semantic summary."""

        if not memories:
            return "No prior interactions recorded."

        # Extract key dimensions
        summaries = {
            "reliability": [],
            "preferences": [],
            "patterns": [],
            "concerns": [],
        }

        for mem in memories:
            data = mem.get("data", {})

            if isinstance(data, str):
                data = json.loads(data) if data.startswith("{") else {}

            if "payment" in mem.get("memory_type", ""):
                summaries["reliability"].append(data.get("on_time_ratio", 0.5))

            if "communication" in mem.get("memory_type", ""):
                summaries["preferences"].append(data.get("preferred_contact", ""))

            if "history" in mem.get("memory_type", ""):
                summaries["patterns"].append(data.get("service_type", ""))

            if data.get("concern"):
                summaries["concerns"].append(data["concern"])

        # Synthesize compressed summary
        output_lines = []

        if summaries["reliability"]:
            avg_reliability = sum(summaries["reliability"]) / len(summaries["reliability"])
            reliability_desc = (
                "highly reliable"
                if avg_reliability > 0.85
                else "mostly reliable" if avg_reliability > 0.7 else "needs follow-up"
            )
            output_lines.append(f"Reliability: {reliability_desc} ({avg_reliability:.0%})")

        if summaries["preferences"]:
            preferred = max(set(summaries["preferences"]), key=summaries["preferences"].count)
            output_lines.append(f"Prefers: {preferred}")

        if summaries["patterns"]:
            pattern_summary = ", ".join(set(summaries["patterns"]))
            output_lines.append(f"Service types: {pattern_summary}")

        if summaries["concerns"]:
            output_lines.append(f"Notes: {'; '.join(summaries['concerns'][:3])}")

        return ". ".join(output_lines)


class ConsolidatedMemory:
    """Final consolidated memory snapshot with decay + importance."""

    def __init__(self, agent_id: str, db_path: Path):
        self.agent_id = agent_id
        self.db_path = db_path

    def consolidate_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Generate consolidated memory snapshot for one entity.
        Output: Ready-to-inject system prompt context.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Retrieve all memories for this entity
        cursor.execute(
            """
            SELECT * FROM agent_soul_memories
            WHERE agent_id = ? AND entity_id = ?
            ORDER BY updated DESC
        """,
            (self.agent_id, entity_id),
        )

        raw_memories = [dict(row) for row in cursor.fetchall()]

        # Compute importance for each
        scored_memories = []
        for mem in raw_memories:
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) as mention_count FROM agent_soul_interactions
                    WHERE agent_id = ? AND entity_id = ?
                """,
                    (self.agent_id, entity_id),
                )

                mention_count = cursor.fetchone()[0]
                mem["mention_count"] = mention_count

                # Compute revenue impact
                try:
                    cursor.execute(
                        """
                        SELECT SUM(CAST(JSON_EXTRACT(data, '$.amount') AS REAL)) as total
                        FROM agent_soul_memories
                        WHERE agent_id = ? AND entity_id = ? AND memory_type LIKE '%transaction%'
                    """,
                        (self.agent_id, entity_id),
                    )

                    revenue_row = cursor.fetchone()
                    mem["total_revenue"] = revenue_row[0] or 0 if revenue_row else 0
                except:
                    mem["total_revenue"] = 0

                # Score importance
                importance = ImportanceScoring.compute_overall_importance(mem)
                mem["computed_importance"] = importance
                scored_memories.append(mem)
            except:
                pass

        conn.close()

        # Sort by importance (not just recency)
        scored_memories.sort(key=lambda m: m.get("computed_importance", 0), reverse=True)

        # Compress top memories
        top_memories = scored_memories[:20]  # Keep top 20
        compressed = SemanticCompression.compress_memory(top_memories)

        return {
            "agent_id": self.agent_id,
            "entity_id": entity_id,
            "consolidated_at": datetime.now().isoformat(),
            "memory_snapshot": compressed,
            "importance_distribution": {
                "high": sum(1 for m in scored_memories if m.get("computed_importance", 0) > 0.7),
                "medium": sum(
                    1 for m in scored_memories if 0.4 < m.get("computed_importance", 0) <= 0.7
                ),
                "low": sum(1 for m in scored_memories if m.get("computed_importance", 0) <= 0.4),
            },
            "total_records": len(raw_memories),
        }

    def get_system_prompt(self, entity_id: str) -> str:
        """Generate final system prompt for agent."""
        consolidated = self.consolidate_entity(entity_id)
        snapshot = consolidated["memory_snapshot"]

        return f"""
You are serving {entity_id}.

CONSOLIDATED MEMORY (importance-weighted):
{snapshot}

GUIDANCE:
1. Tailor responses based on reliability and preferences
2. Reference past patterns to anticipate needs
3. Log all interactions for future consolidation
4. Maintain consistent tone and communication style

Respond naturally and helpfully.
""".strip()
