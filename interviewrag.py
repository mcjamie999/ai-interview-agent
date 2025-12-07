# interviewrag.py
"""
Interview Knowledge Graph wrapper using pure Python MeTTa simulation.
Compatible with Agentverse (no binary dependencies).
"""

from typing import List, Optional, Dict, Tuple
from metta_sim import (
    KnowledgeGraph,
    get_focus_skills,
    get_question_skills,
    get_followup_question,
    get_topics_for_persona,
    get_topics_for_skills,
    get_role_requirements,
    get_skill_prerequisites,
    get_persona_skills_for_question,
    suggest_next_question_topic,
)

class InterviewKG:
    """
    Wrapper class for interview knowledge graph queries.
    Uses pure Python MeTTa simulation instead of Hyperon.
    """
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def get_focus_skills(self, persona: str) -> List[str]:
        """Get all focus skills for a given persona."""
        return get_focus_skills(self.kg, persona)

    def get_topics_for_persona(self, persona: str, limit: int = 3) -> List[Tuple[str, float]]:
        """
        Get recommended question topics for a persona, ordered by priority.
        Returns list of (topic, weight) tuples.
        """
        return get_topics_for_persona(self.kg, persona, limit)

    def get_topics_for_skills(self, skills: List[str]) -> List[str]:
        """
        Given a list of skills mentioned by candidate, find relevant question topics.
        """
        return get_topics_for_skills(self.kg, skills)

    def get_role_requirements(self, role: str) -> List[Tuple[str, str]]:
        """
        Get all required skills for a role with their levels.
        Returns list of (skill, level) tuples.
        """
        return get_role_requirements(self.kg, role)

    def get_skill_prerequisites(self, skill: str) -> List[str]:
        """Get prerequisites for a given skill."""
        return get_skill_prerequisites(self.kg, skill)

    def get_question_skills(self, qid: str) -> List[str]:
        """Get all skills assessed by a question ID."""
        return get_question_skills(self.kg, qid)

    def get_followup_question(self, qid: str) -> Optional[str]:
        """Get the next question ID in the follow-up chain."""
        return get_followup_question(self.kg, qid)

    def add_candidate_skill(self, user_address: str, skill: str, evidence: str):
        """
        Add a fact that candidate mentioned a skill.
        (candidate_mentioned User Skill Evidence)
        """
        self.kg.add_atom("candidate_mentioned", user_address, skill, evidence)

    def get_candidate_skills(self, user_address: str) -> List[Tuple[str, str]]:
        """
        Get all skills mentioned by candidate with evidence.
        Returns list of (skill, evidence) tuples.
        """
        results = self.kg.query("candidate_mentioned", user_address, "$skill", "$evidence")
        return [(r[0], r[1]) for r in results]

    def analyze_skill_gaps(self, user_address: str, role: str) -> Dict[str, List[str]]:
        """
        Analyze gaps between candidate skills and role requirements.
        Returns dict with:
        - 'mentioned': skills candidate mentioned
        - 'missing': required skills not mentioned
        - 'missing_prerequisites': prerequisites of mentioned skills that are missing
        """
        mentioned_skills = [skill for skill, _ in self.get_candidate_skills(user_address)]
        required_skills = [skill for skill, _ in self.get_role_requirements(role)]
        
        mentioned_set = set(mentioned_skills)
        required_set = set(required_skills)
        
        missing = [skill for skill in required_set if skill not in mentioned_set]
        
        # Check for missing prerequisites
        missing_prereqs = []
        for skill in mentioned_skills:
            prereqs = self.get_skill_prerequisites(skill)
            for prereq in prereqs:
                if prereq not in mentioned_set and prereq in required_set:
                    if prereq not in missing_prereqs:
                        missing_prereqs.append(prereq)
        
        return {
            'mentioned': mentioned_skills,
            'missing': missing,
            'missing_prerequisites': missing_prereqs
        }

    def get_persona_skills_for_question(self, persona: str, qid: str) -> List[str]:
        """Get skills that are both focus skills for the persona and assessed by the question."""
        return get_persona_skills_for_question(self.kg, persona, qid)

    def suggest_next_question_topic(self, persona: str, previous_topics: List[str]) -> Optional[str]:
        """Suggest the next question topic based on persona priorities, avoiding topics already covered."""
        return suggest_next_question_topic(self.kg, persona, previous_topics)
