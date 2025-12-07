# knowledge.py
"""
Knowledge graph builder using pure Python MeTTa simulation.
Works in restricted environments like Agentverse (no binary dependencies).
"""

from metta_sim import build_interview_kg as _build_interview_kg, KnowledgeGraph

def build_interview_kg() -> KnowledgeGraph:
    """
    Build the interview knowledge graph with domain facts.
    Uses pure Python MeTTa simulation instead of Hyperon.
    """
    return _build_interview_kg()

