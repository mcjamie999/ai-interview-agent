# How metta_sim, knowledge.py, and interviewrag.py Work Together

## Overview

These three files form a **layered architecture** for the knowledge graph system:

```
┌─────────────────────────────────────────────────────────┐
│  interviewer.py                                         │
│  (Application Layer - Uses InterviewKG)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses InterviewKG class
                     ▼
┌─────────────────────────────────────────────────────────┐
│  interviewrag.py                                        │
│  (High-Level Wrapper - InterviewKG class)               │
│  • Wraps query functions                                │
│  • Adds interview-specific methods                      │
│  • Adds candidate skill tracking                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Takes KnowledgeGraph instance
                     │ Uses query functions from metta_sim
                     ▼
┌─────────────────────────────────────────────────────────┐
│  knowledge.py                                           │
│  (Simple Import Wrapper)                                │
│  • Just re-exports build_interview_kg()                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Imports from metta_sim
                     ▼
┌─────────────────────────────────────────────────────────┐
│  metta_sim                                              │
│  (Foundation Layer - Core Engine)                       │
│  • Atom class                                           │
│  • KnowledgeGraph class                                 │
│  • build_interview_kg() function                        │
│  • Query helper functions                               │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: metta_sim (Foundation)

**Purpose**: Pure Python MeTTa-style knowledge graph engine - the core foundation.

**What it provides**:

1. **Atom Class** (lines 19-38)
   - Represents facts: `(predicate arg1 arg2 ...)`
   - Immutable data structure
   - Example: `(focus_skill HR communication)`

2. **KnowledgeGraph Class** (lines 41-146)
   - Stores atoms in memory
   - Provides pattern matching with variables
   - Supports queries with wildcards and variable binding
   - Methods:
     - `add_atom(predicate, *args)` - Add a fact
     - `match(predicate, *pattern)` - Pattern matching
     - `query(predicate, *pattern)` - Simplified query interface

3. **build_interview_kg() Function** (lines 153-277)
   - **Populates the knowledge graph with domain facts**
   - Adds hundreds of atoms like:
     ```python
     kg.add_atom("focus_skill", "HR", "communication")
     kg.add_atom("persona_priority", "HR", "culture_fit", "0.95")
     kg.add_atom("role_requires", "Junior Data Analyst", "SQL", "intermediate")
     ```
   - Returns a fully populated `KnowledgeGraph` instance

4. **Query Helper Functions** (lines 284-421)
   - Higher-level query functions that use the KnowledgeGraph
   - Examples:
     - `get_focus_skills(kg, persona)` - Get skills for a persona
     - `get_topics_for_persona(kg, persona)` - Get recommended topics
     - `get_role_requirements(kg, role)` - Get role requirements

**Key Point**: `metta_sim` is the **engine** - it doesn't know about interviews specifically. It's a general-purpose knowledge graph system.

---

## Layer 2: knowledge.py (Simple Import Wrapper)

**Purpose**: Clean import interface - just re-exports the builder function.

**What it does**:

```python
from metta_sim import build_interview_kg as _build_interview_kg, KnowledgeGraph

def build_interview_kg() -> KnowledgeGraph:
    """Build the interview knowledge graph with domain facts."""
    return _build_interview_kg()
```

**Why it exists**:
- Provides a clean import path: `from knowledge import build_interview_kg`
- Instead of: `from metta_sim import build_interview_kg`
- Acts as a simple interface layer
- Makes it easy to swap implementations later if needed

**What it doesn't do**:
- Doesn't add any functionality
- Doesn't modify the graph
- Just a thin wrapper

---

## Layer 3: interviewrag.py (High-Level Wrapper)

**Purpose**: Interview-specific wrapper class that provides convenient methods for the interviewer agent.

**What it provides**:

1. **InterviewKG Class** (lines 21-117)
   - Takes a `KnowledgeGraph` instance in constructor
   - Wraps query functions from `metta_sim`
   - Adds interview-specific functionality

2. **Wrapped Query Methods** (lines 29-63)
   - All methods delegate to functions from `metta_sim`:
     ```python
     def get_focus_skills(self, persona: str) -> List[str]:
         return get_focus_skills(self.kg, persona)  # Calls metta_sim function
     ```
   - Methods include:
     - `get_focus_skills(persona)`
     - `get_topics_for_persona(persona)`
     - `get_role_requirements(role)`
     - `get_skill_prerequisites(skill)`

3. **Interview-Specific Methods** (lines 65-117)
   - **Candidate Skill Tracking**:
     ```python
     def add_candidate_skill(self, user_address: str, skill: str, evidence: str):
         # Adds dynamic facts during interview
         self.kg.add_atom("candidate_mentioned", user_address, skill, evidence)
     ```
   
   - **Skill Gap Analysis**:
     ```python
     def analyze_skill_gaps(self, user_address: str, role: str):
         # Compares candidate skills vs role requirements
         # Returns: mentioned, missing, missing_prerequisites
     ```

**Key Point**: `InterviewKG` is the **interview domain interface** - it knows about interviews and provides convenient methods for the interviewer agent.

---

## How They Work Together: The Complete Flow

### Step 1: Initialization (in interviewer.py)

```python
# Line 23-24: Import the builder and wrapper
from knowledge import build_interview_kg
from interviewrag import InterviewKG

# Line 27: Build the knowledge graph (calls metta_sim's build_interview_kg())
_kg = build_interview_kg()
# This:
#   1. Calls knowledge.py's build_interview_kg()
#   2. Which calls metta_sim's build_interview_kg()
#   3. Which creates a KnowledgeGraph and populates it with all facts
#   4. Returns the populated KnowledgeGraph instance

# Line 28: Wrap it in InterviewKG class
interview_kg = InterviewKG(_kg)
# This:
#   - Takes the KnowledgeGraph instance
#   - Creates an InterviewKG wrapper
#   - Stores it in self.kg for later use
```

### Step 2: Using the Knowledge Graph (during interview)

```python
# Example: Get focus skills for HR persona
skills = interview_kg.get_focus_skills("HR")

# What happens internally:
#   1. interview_kg.get_focus_skills("HR") is called
#   2. InterviewKG.get_focus_skills() calls get_focus_skills(self.kg, "HR")
#   3. This is the function from metta_sim
#   4. It calls self.kg.query("focus_skill", "HR", "$skill")
#   5. KnowledgeGraph.query() performs pattern matching
#   6. Returns: ["communication", "teamwork", "culture_fit", "professionalism"]
```

### Step 3: Adding Dynamic Facts (during interview)

```python
# Example: Candidate mentions they know SQL
interview_kg.add_candidate_skill(user_address, "SQL", "mentioned in answer")

# What happens:
#   1. InterviewKG.add_candidate_skill() is called
#   2. It calls self.kg.add_atom("candidate_mentioned", user_address, "SQL", "...")
#   3. KnowledgeGraph.add_atom() adds a new fact to the graph
#   4. This fact is now queryable like any other fact
```

---

## Data Flow Example

Let's trace a complete example: **Getting recommended topics for HR persona**

```
interviewer.py
    ↓
    interview_kg.get_topics_for_persona("HR", limit=3)
    ↓
interviewrag.py (InterviewKG class)
    ↓
    get_topics_for_persona(self.kg, "HR", 3)
    ↓
metta_sim (query function)
    ↓
    self.kg.query("persona_priority", "HR", "$topic", "$weight")
    ↓
metta_sim (KnowledgeGraph class)
    ↓
    Pattern matching against atoms:
    - (persona_priority HR conflict_resolution 0.9)
    - (persona_priority HR culture_fit 0.95)
    ↓
    Returns: [("conflict_resolution", "0.9"), ("culture_fit", "0.95")]
    ↓
    Convert weights to floats, sort by weight
    ↓
    Returns: [("culture_fit", 0.95), ("conflict_resolution", 0.9)]
    ↓
Back to interviewer.py
    ↓
    Uses topics to generate question via ASI Cloud API
```

---

## Key Design Patterns

### 1. **Layered Architecture**
   - Each layer has a specific responsibility
   - Lower layers don't know about higher layers
   - Clear separation of concerns

### 2. **Dependency Injection**
   - `InterviewKG` takes a `KnowledgeGraph` instance (doesn't create it)
   - Allows flexibility and testing

### 3. **Wrapper Pattern**
   - `InterviewKG` wraps `KnowledgeGraph`
   - Adds domain-specific methods
   - Doesn't modify the core graph functionality

### 4. **Function Delegation**
   - `InterviewKG` methods delegate to `metta_sim` functions
   - Keeps code DRY (Don't Repeat Yourself)
   - Single source of truth for query logic

---

## What Each File Is Responsible For

| File | Responsibility | Knows About |
|------|---------------|-------------|
| **metta_sim** | Core knowledge graph engine | Atoms, pattern matching, general facts |
| **knowledge.py** | Import interface | Just re-exporting functions |
| **interviewrag.py** | Interview domain wrapper | Interview concepts, candidate tracking |
| **interviewer.py** | Application logic | Interview flow, question generation |

---

## Memory Model

```
┌──────────────────────────────────────────────┐
│  interviewer.py                              │
│  interview_kg (InterviewKG instance)         │
│    └─ self.kg (KnowledgeGraph instance)      │
│         └─ self._atoms (Set of Atom objects) │
│              └─ Hundreds of facts like:      │
│                 • (focus_skill HR comm...)   │
│                 • (role_requires JDA SQL...) │
│                 • (candidate_mentioned ...)  │
└──────────────────────────────────────────────┘
```

**All in memory, all in the same process!**
- No network calls between these components
- Fast, direct Python function calls
- Everything happens in the Interviewer Agent process

---

## Example Code Walkthrough

### Complete Example: Getting Skills for Question Generation

```python
# In interviewer.py, when generating first question:

# 1. Query for persona focus skills
focus_skills = interview_kg.get_focus_skills("HR")
# Returns: ["communication", "teamwork", "culture_fit", "professionalism"]

# 2. Query for recommended topics
topics = interview_kg.get_topics_for_persona("HR", limit=3)
# Returns: [("culture_fit", 0.95), ("conflict_resolution", 0.9)]

# 3. Use in prompt for ASI Cloud API
prompt = f"""
You are an HR interviewer focusing on: {', '.join(focus_skills)}
Recommended topics: {', '.join([t[0] for t in topics])}
Generate a question...
"""

# 4. ASI Cloud generates question based on KG knowledge
```

### Example: Tracking Candidate Skills

```python
# When candidate mentions SQL in their answer:
interview_kg.add_candidate_skill(
    user_address="user123",
    skill="SQL",
    evidence="I use SQL daily for data queries"
)

# Later, analyze skill gaps:
gaps = interview_kg.analyze_skill_gaps("user123", "Junior Data Analyst")
# Returns:
# {
#     'mentioned': ['SQL'],
#     'missing': ['Excel', 'data_visualization', 'Python', ...],
#     'missing_prerequisites': []
# }
```

---

## Why This Architecture?

### ✅ Benefits:

1. **Separation of Concerns**
   - Core engine (metta_sim) is reusable
   - Interview logic (interviewrag) is focused
   - Application logic (interviewer) is clean

2. **Testability**
   - Each layer can be tested independently
   - Easy to mock dependencies

3. **Maintainability**
   - Clear where to make changes
   - Easy to understand dependencies

4. **Flexibility**
   - Could swap `metta_sim` for real Hyperon later
   - Could add different wrapper classes for different domains

5. **No Binary Dependencies**
   - Pure Python all the way down
   - Works in restricted environments (Agentverse)

---

## Summary

```
metta_sim          → The ENGINE (doesn't know about interviews)
     ↓
knowledge.py       → Simple IMPORT WRAPPER
     ↓
interviewrag.py    → Interview DOMAIN WRAPPER (knows about interviews)
     ↓
interviewer.py     → APPLICATION (uses InterviewKG methods)
```

**Think of it like:**
- `metta_sim` = The database engine
- `knowledge.py` = The connection string
- `interviewrag.py` = The ORM (Object-Relational Mapping)
- `interviewer.py` = The application using the ORM

All working together seamlessly! 🎯

