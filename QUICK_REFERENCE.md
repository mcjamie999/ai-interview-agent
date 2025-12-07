# Quick Reference: How metta_sim, knowledge.py, and interviewrag.py Work Together

## 🎯 TL;DR

Three layers working together:
1. **metta_sim** = Core knowledge graph engine (foundation)
2. **knowledge.py** = Simple import wrapper (interface)
3. **interviewrag.py** = Interview-specific wrapper (domain layer)

## 📊 The Flow

```
interviewer.py
    ↓ uses
InterviewKG (from interviewrag.py)
    ↓ wraps
KnowledgeGraph (from metta_sim)
    ↓ contains
Atoms (facts stored in memory)
```

## 🔄 Initialization

```python
# In interviewer.py:
from knowledge import build_interview_kg          # Import wrapper
from interviewrag import InterviewKG              # Import wrapper class

_kg = build_interview_kg()                        # Builds graph (calls metta_sim)
interview_kg = InterviewKG(_kg)                   # Wraps it for interview use
```

## 💡 What Each Does

### metta_sim (Foundation)
- **Core engine**: Atom storage, pattern matching, queries
- **Domain facts**: Populates graph with all interview knowledge
- **Query functions**: `get_focus_skills()`, `get_topics_for_persona()`, etc.

### knowledge.py (Interface)
- **Simple wrapper**: Just re-exports `build_interview_kg()`
- **Clean imports**: `from knowledge import build_interview_kg`

### interviewrag.py (Domain Layer)
- **InterviewKG class**: Wraps KnowledgeGraph with interview methods
- **Convenience methods**: `get_focus_skills()`, `analyze_skill_gaps()`, etc.
- **Candidate tracking**: Adds dynamic facts during interview

## 📝 Example Usage

```python
# Get skills for HR persona
skills = interview_kg.get_focus_skills("HR")
# → ["communication", "teamwork", "culture_fit", "professionalism"]

# Get recommended topics
topics = interview_kg.get_topics_for_persona("HR", limit=3)
# → [("culture_fit", 0.95), ("conflict_resolution", 0.9)]

# Track candidate skills
interview_kg.add_candidate_skill("user123", "SQL", "mentioned in answer")

# Analyze gaps
gaps = interview_kg.analyze_skill_gaps("user123", "Junior Data Analyst")
# → {'mentioned': ['SQL'], 'missing': [...], ...}
```

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────┐
│  interviewer.py (Application)          │
│  Uses InterviewKG methods              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  interviewrag.py (Domain Wrapper)       │
│  InterviewKG wraps KnowledgeGraph       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  knowledge.py (Import Wrapper)          │
│  Re-exports build_interview_kg()        │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  metta_sim (Core Engine)                │
│  KnowledgeGraph + domain facts          │
└─────────────────────────────────────────┘
```

## 🔑 Key Points

1. **All in-process**: No network calls, all direct Python function calls
2. **Layered design**: Clear separation of concerns
3. **Single graph instance**: One KnowledgeGraph shared by all queries
4. **Pure Python**: No binary dependencies (Agentverse compatible)

## 📚 More Details

- **Full explanation**: See `HOW_THEY_WORK_TOGETHER.md`
- **Visual architecture**: See `KNOWLEDGE_GRAPH_ARCHITECTURE.md`
- **Complete docs**: See `documentation.md`

