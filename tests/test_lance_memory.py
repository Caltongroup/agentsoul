"""Basic tests for LanceDB memory module."""

import pytest
from agentsoul.memory.lance import recall, recall_formatted


def test_recall_returns_list():
    """Recall should always return a list."""
    result = recall("test query about retirement", top_k=3)
    assert isinstance(result, list)


def test_recall_formatted_returns_string():
    """Formatted recall should return a string."""
    result = recall_formatted("test query", top_k=2)
    assert isinstance(result, str)


def test_recall_respects_top_k():
    """Top_k parameter should limit results."""
    result = recall("test", top_k=5)
    assert len(result) <= 5