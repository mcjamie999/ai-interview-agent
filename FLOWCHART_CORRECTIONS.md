# Flowchart Corrections - What's Missing

## ❌ What's Wrong with the Current Flowchart

The flowchart is **missing the Knowledge Graph component**, which is a crucial part of the system!

### Current Flowchart Shows:
```
Interviewer Agent → LLM Service (Question Generation)
```

### ✅ What Actually Happens:
```
Interviewer Agent → Knowledge Graph (query for context) → LLM Service (Question Generation)
```

---

## The Missing Component: Knowledge Graph

The Knowledge Graph (MeTTa-based) is **queried BEFORE** calling the LLM. It provides:

1. **Persona Focus Skills** - What skills this interviewer persona focuses on
2. **Topic Priorities** - Recommended question topics for the persona
3. **Role Requirements** - Skills needed for the role

This context is then used to build a better prompt for the LLM.

---

## Corrected Flowchart

```
┌───────────────────────────────────────────────────────────────────┐
│                    Agentverse Chat                                │
│                 (Chat Protocol Frontend)                          │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               │ ChatMessage (bidirectional)
                               │
        ┌──────────────────────▼────────────────────────────────────┐
        │              Interviewer Agent                            │
        │          (Four types of personas)                         │
        │  ┌──────────────────────────────────────────────────────┐ │
        │  │ Responsibilities:                                     │ │
        │  │ • Handles Chat Protocol messages                     │ │
        │  │ • Manages SessionState & logs                        │ │
        │  │ • Sends EvaluationRequest to Evaluator               │ │
        │  │ • Receives EvaluationResponse back                   │ │
        │  └──────────────────────────────────────────────────────┘ │
        │                                                           │
        │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
        │  │ Queries:     │  │ Sends:       │  │ Receives:    │   │
        │  │              │  │              │  │              │   │
        │  │ Knowledge    │  │ Evaluation   │  │ Evaluation   │   │
        │  │ Graph        │  │ Request      │  │ Response     │   │
        │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
        │         │                  │                  │           │
        │         │ In-Process       │ Async Message    │ Async     │
        │         │ Python Calls     │                  │ Message   │
        └─────────┼──────────────────┼──────────────────┼───────────┘
                  │                  │                  │
                  ▼                  ▼                  ▼
        ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
        │ Knowledge Graph  │  │ Evaluator    │  │ Evaluator Agent  │
        │ (MeTTa-based)    │  │ Agent        │  │                  │
        │                  │  │              │  │ Receives:        │
        │ • Persona skills │  │ Receives:    │  │ EvaluationRequest│
        │ • Topic          │  │ Evaluation   │  │                  │
        │   priorities     │  │ Request      │  │ Sends:           │
        │ • Role           │  │              │  │ EvaluationResponse│
        │   requirements   │  │ Sends:       │  └────────┬─────────┘
        │                  │  │ Evaluation   │           │
        │ Returns context  │  │ Response     │           │
        │ for prompt       │  └──────┬───────┘           │
        └──────────┬───────┘         │                   │
                   │                 │                   │
                   │                 │ HTTP API          │
                   │                 │                   │
                   │                 ▼                   │
                   │         ┌──────────────────┐        │
                   │         │ ASI Cloud API    │        │
                   │         │ (Answer Eval)    │        │
                   │         └──────────────────┘        │
                   │                                      │
                   │                                      │
        ┌──────────┴──────────────────────────────────────┘
        │
        │ Uses KG context in prompt
        │
        ▼
┌──────────────────────────────────────┐
│     ASI Cloud API                    │
│     (Question Generation)            │
│                                      │
│  Called with enhanced prompt that    │
│  includes Knowledge Graph context:   │
│  • Persona focus skills              │
│  • Recommended topics                │
│  • Role requirements                 │
└──────────────────────────────────────┘
```

---

## Detailed Correct Flow

### Question Generation Flow (CORRECTED)

```
Step 1: User selects avatar (e.g., "HR")
        ↓
Step 2: Interviewer Agent queries Knowledge Graph:
        • interview_kg.get_focus_skills("HR")
          → Returns: ["communication", "teamwork", "culture_fit", ...]
        • interview_kg.get_topics_for_persona("HR", limit=3)
          → Returns: [("culture_fit", 0.95), ("conflict_resolution", 0.9), ...]
        ↓
Step 3: Interviewer Agent builds enhanced prompt:
        "You are an HR interviewer focusing on: communication, teamwork, culture_fit
         Recommended topics: culture_fit, conflict_resolution
         Generate question..."
        ↓
Step 4: Interviewer Agent calls ASI Cloud API with enhanced prompt
        ↓
Step 5: ASI Cloud API returns generated question
        ↓
Step 6: Interviewer Agent sends question to user
```

### What the Current Flowchart Misses:

**Missing Step 2**: The Knowledge Graph query that happens BEFORE the LLM call.

The Knowledge Graph is not just a component - it's an **active part of the question generation process** that provides context to make the LLM prompts better.

---

## Code Evidence

From `interviewer.py` lines 163-165 and 241-247:

```python
# FIRST: Query Knowledge Graph
focus_skills = interview_kg.get_focus_skills(persona)
skills_context = ", ".join(focus_skills)

recommended_topics = interview_kg.get_topics_for_persona(persona, limit=3)
topics_context = ", ".join([topic for topic, _ in recommended_topics])

# THEN: Use KG context in prompt
prompt = f"""
Based on symbolic reasoning, your interviewer persona focuses on these key skills: {skills_context}.
Recommended question topics: {topics_context}
...
"""

# FINALLY: Call LLM with enhanced prompt
response = requests.post(ASI_API_URL, json=payload, ...)
```

---

## Key Correction Points

### 1. Knowledge Graph is MISSING from the flowchart

The flowchart should show:
- Knowledge Graph as a component
- Interviewer Agent querying KG BEFORE calling LLM
- KG providing context that enhances the LLM prompt

### 2. The Flow is More Complex

Current flowchart shows: `Interviewer → LLM`

Actual flow is: `Interviewer → KG (query) → Build enhanced prompt → LLM`

### 3. KG is In-Process, Not Network

The Knowledge Graph queries are **in-process Python function calls**, not network calls. This should be indicated differently than the async agent messaging.

---

## Corrected Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 Agentverse Chat                              │
│              (User Interface)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ ChatMessage
                       │
        ┌──────────────▼──────────────────────────────┐
        │       Interviewer Agent                      │
        │  ┌────────────────────────────────────────┐ │
        │  │ • Session Management                   │ │
        │  │ • User Interaction                     │ │
        │  │ • Question Generation                  │ │
        │  │ • Answer Processing                    │ │
        │  └────────────────────────────────────────┘ │
        │                                              │
        │  ┌──────────────┐  ┌──────────────┐         │
        │  │ Queries:     │  │ Sends async: │         │
        │  │              │  │              │         │
        │  │ Knowledge    │  │ Evaluation   │         │
        │  │ Graph        │  │ Request      │         │
        │  └──────┬───────┘  └──────┬───────┘         │
        └─────────┼──────────────────┼─────────────────┘
                  │                  │
                  │ In-Process       │ Async Agent
                  │ Python Calls     │ Message
                  │                  │
        ┌─────────▼──────────┐      │
        │  Knowledge Graph   │      │
        │  (MeTTa-based)     │      │
        │                    │      │
        │  In-process with   │      │
        │  Interviewer Agent │      │
        │                    │      │
        │  • Persona skills  │      │
        │  • Topics          │      │
        │  • Role reqs       │      │
        └─────────┬──────────┘      │
                  │                 │
                  │ Context used    │
                  │ in prompt       │
                  │                 │
        ┌─────────▼─────────────────▼──────────┐
        │     ASI Cloud API                    │
        │                                      │
        │  Called with prompt that includes:   │
        │  • KG context (skills, topics)       │
        │  • Conversation history              │
        │  • Persona description               │
        └──────────────────────────────────────┘
```

---

## Summary of Issues

| Issue | Current Flowchart | Correct Flowchart |
|-------|------------------|-------------------|
| **Knowledge Graph** | ❌ Missing | ✅ Shows KG component |
| **Query Sequence** | ❌ Direct to LLM | ✅ KG query → Enhanced prompt → LLM |
| **Communication Type** | ❌ Not specified | ✅ In-process Python calls |
| **KG Context Usage** | ❌ Not shown | ✅ KG context used in prompt |

---

## Recommendation

Update the flowchart to include:

1. **Knowledge Graph component** between Interviewer Agent and LLM Service
2. **Two-step process**: Query KG first, then call LLM with enhanced prompt
3. **Indication** that KG is in-process (not network communication)
4. **Label** showing KG provides "context for prompt enhancement"

The Knowledge Graph is a **critical component** that makes the question generation intelligent and persona-appropriate! 🎯

