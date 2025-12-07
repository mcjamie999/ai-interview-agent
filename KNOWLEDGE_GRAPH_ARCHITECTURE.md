# Knowledge Graph Architecture - Visual Guide

## The Three-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      interviewer.py                              │
│                   (Application Layer)                            │
│                                                                  │
│  from knowledge import build_interview_kg                       │
│  from interviewrag import InterviewKG                           │
│                                                                  │
│  _kg = build_interview_kg()      # Builds graph                 │
│  interview_kg = InterviewKG(_kg)  # Wraps it                    │
│                                                                  │
│  # Uses InterviewKG methods:                                    │
│  skills = interview_kg.get_focus_skills("HR")                   │
│  topics = interview_kg.get_topics_for_persona("HR")             │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                │ Imports & Uses
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌──────────────────────────┐              ┌────────────────────────────┐
│     knowledge.py         │              │    interviewrag.py         │
│  (Import Wrapper)        │              │  (High-Level Wrapper)      │
│                          │              │                            │
│  from metta_sim import   │              │  from metta_sim import (   │
│      build_interview_kg  │              │      KnowledgeGraph,       │
│                          │              │      get_focus_skills,     │
│  def build_interview_kg()│              │      get_topics_for_...    │
│      return _build_...   │              │  )                         │
└──────────┬───────────────┘              │                            │
           │                               │  class InterviewKG:       │
           │                               │      def __init__(self, kg)│
           │                               │          self.kg = kg      │
           │                               │                            │
           │                               │      def get_focus_skills()│
           │                               │          return get_...()  │
           │                               └────────────┬───────────────┘
           │                                            │
           │                                            │ Uses functions &
           │                                            │ KnowledgeGraph
           │                                            │
           └────────────────────┬───────────────────────┘
                                │
                                │ Imports from
                                │
                    ┌───────────▼────────────┐
                    │     metta_sim          │
                    │  (Foundation Layer)    │
                    │                        │
                    │  • Atom class          │
                    │  • KnowledgeGraph class│
                    │  • build_interview_kg()│
                    │    (populates graph)   │
                    │  • Query functions:    │
                    │    - get_focus_skills()│
                    │    - get_topics_...()  │
                    │    - get_role_...()    │
                    └────────────────────────┘
```

## Detailed Call Flow

### When interviewer.py calls: `interview_kg.get_focus_skills("HR")`

```
┌─────────────────────────────────────────────────────────────────┐
│  interviewer.py                                                 │
│                                                                 │
│  skills = interview_kg.get_focus_skills("HR")                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Call method
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  interviewrag.py                                                │
│  InterviewKG.get_focus_skills(self, "HR")                       │
│                                                                 │
│      return get_focus_skills(self.kg, "HR")                    │
│                     │                                           │
│                     │ self.kg is the KnowledgeGraph instance    │
│                     │ get_focus_skills is from metta_sim        │
└─────────────────────┼───────────────────────────────────────────┘
                      │
                      │ Call function
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  metta_sim                                                      │
│  get_focus_skills(kg: KnowledgeGraph, persona: str)            │
│                                                                 │
│      results = kg.query("focus_skill", persona, "$skill")      │
│                     │                                           │
│                     │ kg is the KnowledgeGraph instance         │
└─────────────────────┼───────────────────────────────────────────┘
                      │
                      │ Query the graph
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  metta_sim                                                      │
│  KnowledgeGraph.query("focus_skill", "HR", "$skill")           │
│                                                                 │
│  1. Get all atoms with predicate "focus_skill"                 │
│  2. Match pattern: (focus_skill "HR" $skill)                   │
│  3. Find matching atoms:                                        │
│     • (focus_skill HR communication)                           │
│     • (focus_skill HR teamwork)                                │
│     • (focus_skill HR culture_fit)                             │
│     • (focus_skill HR professionalism)                         │
│  4. Extract $skill values                                      │
│  5. Return: [("communication",), ("teamwork",), ...]           │
└─────────────────────┼───────────────────────────────────────────┘
                      │
                      │ Return results
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Back up the chain...                                           │
│                                                                 │
│  get_focus_skills() extracts: ["communication", "teamwork",...]│
│  InterviewKG.get_focus_skills() returns the list                │
│  interviewer.py receives the skills                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Structure Hierarchy

```
KnowledgeGraph Instance (in memory)
│
├── _atoms: Set[Atom]
│   ├── Atom("focus_skill", ("HR", "communication"))
│   ├── Atom("focus_skill", ("HR", "teamwork"))
│   ├── Atom("persona_priority", ("HR", "culture_fit", "0.95"))
│   ├── Atom("role_requires", ("Junior Data Analyst", "SQL", "intermediate"))
│   └── ... (hundreds more)
│
└── _predicate_index: Dict[str, Set[Atom]]
    ├── "focus_skill" → {Atom(...), Atom(...), ...}
    ├── "persona_priority" → {Atom(...), Atom(...), ...}
    ├── "role_requires" → {Atom(...), Atom(...), ...}
    └── ... (indexed by predicate for fast lookup)
```

## Initialization Sequence

```
1. interviewer.py starts
   ↓
2. Import: from knowledge import build_interview_kg
   ↓
3. knowledge.py imports: from metta_sim import build_interview_kg as _build_interview_kg
   ↓
4. interviewer.py calls: _kg = build_interview_kg()
   ↓
5. knowledge.py's build_interview_kg() calls metta_sim's _build_interview_kg()
   ↓
6. metta_sim.build_interview_kg():
   a. Creates new KnowledgeGraph() instance
   b. Calls kg.add_atom() hundreds of times:
      • kg.add_atom("focus_skill", "HR", "communication")
      • kg.add_atom("focus_skill", "HR", "teamwork")
      • kg.add_atom("persona_priority", "HR", "culture_fit", "0.95")
      • ... (all domain facts)
   c. Returns the populated KnowledgeGraph
   ↓
7. Back to interviewer.py: _kg now contains the populated graph
   ↓
8. Import: from interviewrag import InterviewKG
   ↓
9. interviewer.py creates: interview_kg = InterviewKG(_kg)
   ↓
10. InterviewKG.__init__() stores: self.kg = _kg
   ↓
11. Ready to use! interview_kg.get_focus_skills("HR") works
```

## Complete Example: Question Generation

```
┌──────────────────────────────────────────────────────────────┐
│  interviewer.py: Generate first question                    │
└───────────────────────────────┬──────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌───────────────────────┐  ┌───────────────────────┐
        │  Get Focus Skills     │  │  Get Topic Priorities │
        └───────────┬───────────┘  └───────────┬───────────┘
                    │                           │
                    ▼                           ▼
    interview_kg.get_focus_skills("HR")   interview_kg.get_topics_for_persona("HR")
                    │                           │
                    │                           │
        ┌───────────┴───────────┐  ┌───────────┴───────────┐
        │                       │  │                       │
        ▼                       ▼  ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ metta_sim        │   │ metta_sim        │   │ metta_sim        │
│ queries KG for:  │   │ queries KG for:  │   │ queries KG for:  │
│                  │   │                  │   │                  │
│ (focus_skill     │   │ (persona_priority│   │ (persona_priority│
│  HR communication)│  │  HR culture_fit  │   │  HR conflict_... │
│ (focus_skill     │   │  0.95)           │   │  0.9)            │
│  HR teamwork)    │   │                  │   │                  │
│ ...              │   │                  │   │                  │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │
         └──────────┬───────────┴──────────┬───────────┘
                    │                      │
                    ▼                      ▼
         ["communication",         [("culture_fit", 0.95),
          "teamwork",              ("conflict_resolution", 0.9)]
          "culture_fit", ...]
                    │                      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Build prompt with:  │
                    │  • Persona desc      │
                    │  • Focus skills      │
                    │  • Topic priorities  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Call ASI Cloud API  │
                    │  (Question Gen)      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Generated Question  │
                    └──────────────────────┘
```

## Key Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    Relationships                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  knowledge.py  ──imports──>  metta_sim                     │
│       │                          ↑                          │
│       │                          │                          │
│       └──re-exports function─────┘                          │
│                                                             │
│  interviewrag.py  ──imports──>  metta_sim                  │
│       │                          ↑                          │
│       │                          │                          │
│       └──wraps KnowledgeGraph────┘                          │
│          uses query functions                               │
│                                                             │
│  interviewer.py  ──imports──>  knowledge.py                │
│       │                          │                          │
│       │                          └──imports──> metta_sim    │
│       │                                              ↑      │
│       └──imports──> interviewrag.py ───uses──────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Memory Layout

```
Process Memory (Interviewer Agent)
│
├── metta_sim module (loaded once)
│   ├── Atom class definition
│   ├── KnowledgeGraph class definition
│   ├── build_interview_kg() function
│   └── Query helper functions
│
├── knowledge.py module
│   └── build_interview_kg() wrapper function
│
├── interviewrag.py module
│   ├── InterviewKG class definition
│   └── Imported query functions from metta_sim
│
└── interviewer.py (main execution)
    ├── _kg: KnowledgeGraph instance
    │   └── Contains all atoms (facts) in memory
    │
    └── interview_kg: InterviewKG instance
        └── self.kg = _kg (reference to same object)
```

**Everything is in the same process, in memory, with direct function calls!**

## Summary Table

| Component | Role | Knows About | Created By |
|-----------|------|-------------|------------|
| **metta_sim** | Core engine | Atoms, patterns, queries | Original implementation |
| **knowledge.py** | Import wrapper | Just re-exports | Thin wrapper |
| **interviewrag.py** | Domain wrapper | Interviews, candidates | Interview-specific |
| **_kg** | Graph instance | All domain facts | `build_interview_kg()` |
| **interview_kg** | Wrapper instance | Interview methods | `InterviewKG(_kg)` |

All working together seamlessly! 🎯

