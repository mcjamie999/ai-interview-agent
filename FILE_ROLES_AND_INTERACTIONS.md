# File Roles and Interactions - Complete Guide

## Overview

This document explains the role of each file in the Job Interview Simulator and how they interact with each other.

---

## All Files in the System

1. **metta_sim** - Core knowledge graph engine
2. **knowledge.py** - Import wrapper for knowledge graph builder
3. **interviewrag.py** - Interview domain wrapper class
4. **interviewer.py** - Main interviewer agent (handles interview flow)
5. **evaluator.py** - Evaluator agent (evaluates answers)

---

## File-by-File Breakdown

### 1. metta_sim (Foundation Layer)

**Role**: Core knowledge graph engine - the foundation of the entire system.

**What it provides**:
- **Atom class**: Represents facts as `(predicate arg1 arg2 ...)`
- **KnowledgeGraph class**: Stores atoms, performs pattern matching queries
- **build_interview_kg() function**: Populates graph with domain knowledge
- **Query helper functions**: High-level query functions for common operations

**Key Responsibilities**:
- Store structured facts (atoms) in memory
- Perform pattern matching with variable binding
- Provide query interface for retrieving information
- Define interview domain knowledge (personas, skills, topics, etc.)

**What it doesn't know about**:
- Interview flow
- User sessions
- API calls
- Only knows about atoms, patterns, and queries

**Example atoms it stores**:
```python
(focus_skill HR communication)
(persona_priority HR culture_fit 0.95)
(role_requires Junior Data Analyst SQL intermediate)
```

**Key Methods**:
- `add_atom(predicate, *args)` - Add a fact to the graph
- `match(predicate, *pattern)` - Pattern matching with variables
- `query(predicate, *pattern)` - Simplified query interface

---

### 2. knowledge.py (Import Interface)

**Role**: Simple import wrapper - provides a clean interface to the knowledge graph builder.

**What it does**:
```python
from metta_sim import build_interview_kg as _build_interview_kg, KnowledgeGraph

def build_interview_kg() -> KnowledgeGraph:
    return _build_interview_kg()
```

**Key Responsibilities**:
- Re-export the `build_interview_kg()` function from metta_sim
- Provide a clean import path (`from knowledge import build_interview_kg`)
- Act as a simple interface layer

**What it doesn't do**:
- Doesn't add any functionality
- Doesn't modify anything
- Just a thin wrapper for cleaner imports

**Why it exists**:
- Separation of concerns
- Easy to swap implementations later
- Cleaner import statements in interviewer.py

---

### 3. interviewrag.py (Domain Wrapper)

**Role**: Interview-specific wrapper class that provides convenient methods for the interviewer agent.

**What it provides**:

1. **InterviewKG Class**: Wraps a KnowledgeGraph instance
2. **Wrapped Query Methods**: Delegates to metta_sim functions
   - `get_focus_skills(persona)` - Get skills for a persona
   - `get_topics_for_persona(persona)` - Get recommended topics
   - `get_role_requirements(role)` - Get role requirements
3. **Interview-Specific Methods**: Adds domain functionality
   - `add_candidate_skill()` - Track candidate skills during interview
   - `get_candidate_skills()` - Retrieve mentioned skills
   - `analyze_skill_gaps()` - Compare candidate vs role requirements

**Key Responsibilities**:
- Provide interview-domain-specific interface
- Wrap knowledge graph queries with convenient methods
- Track dynamic facts (candidate skills) during interviews
- Perform skill gap analysis

**What it knows about**:
- Interview concepts (personas, skills, roles)
- Candidate tracking
- Skill gap analysis
- But delegates actual queries to metta_sim

**Example usage**:
```python
interview_kg = InterviewKG(knowledge_graph_instance)
skills = interview_kg.get_focus_skills("HR")
gaps = interview_kg.analyze_skill_gaps("user123", "Junior Data Analyst")
```

---

### 4. interviewer.py (Main Application)

**Role**: Main interviewer agent - handles the entire interview flow and user interaction.

**Key Responsibilities**:

1. **Session Management**:
   - Tracks user sessions (role, persona, questions, answers)
   - Stores conversation history
   - Manages interview state

2. **User Interaction**:
   - Receives chat messages from users
   - Sends questions and responses
   - Handles avatar selection

3. **Question Generation**:
   - Calls ASI Cloud API to generate questions
   - Uses knowledge graph to get persona context
   - Generates adaptive questions based on conversation history

4. **Answer Processing**:
   - Stores user answers
   - Sends evaluation requests to evaluator agent
   - Continues interview flow immediately

5. **Final Report**:
   - Generates comprehensive evaluation report
   - Calculates average scores
   - Provides strengths and improvement areas

**Key Components**:

- **SessionState dataclass**: Stores session information
- **Knowledge Graph Integration**: Uses InterviewKG to query domain knowledge
- **ASI Cloud API**: Calls for question generation
- **Agent Communication**: Sends/receives messages with evaluator agent

**Flow it manages**:
```
User Message → Avatar Selection → Question Generation → 
Answer Processing → Evaluation Request → Next Question → 
... (5 questions) → Final Report
```

---

### 5. evaluator.py (Evaluation Service)

**Role**: Separate agent that evaluates candidate answers.

**Key Responsibilities**:

1. **Receive Evaluation Requests**:
   - Receives `EvaluationRequest` messages from interviewer agent
   - Contains question, answer, persona, role context

2. **Evaluate Answers**:
   - Calls ASI Cloud API with evaluation prompt
   - Gets scores on 3 dimensions: Clarity, Specificity, Confidence
   - Calculates overall score

3. **Generate Feedback**:
   - Creates constructive feedback text
   - Generates improved answer example

4. **Send Results Back**:
   - Sends `EvaluationResponse` back to interviewer agent
   - Contains all scores, feedback, and improved answer

**Key Components**:
- **EvaluationRequest/Response Models**: Message format for agent communication
- **ASI Cloud API Integration**: Calls for answer evaluation
- **Scoring Logic**: Calculates scores and overall rating

**What it doesn't know about**:
- Interview flow
- Session management
- Knowledge graph
- Only knows about evaluating individual answers

---

## How Files Interact

### Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface                              │
│                   (Agentverse Chat)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ ChatMessage (bidirectional)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    interviewer.py                               │
│                   (Main Application)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Session Management                                     │  │
│  │  • User Interaction                                       │  │
│  │  • Question Generation                                    │  │
│  │  • Answer Processing                                      │  │
│  │  • Final Report Generation                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│          ┌──────────────────┼──────────────────┐               │
│          │                  │                  │               │
│          ▼                  ▼                  ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ interviewrag │  │  ASI Cloud   │  │  Evaluator   │        │
│  │     .py      │  │     API      │  │    Agent     │        │
│  │              │  │              │  │              │        │
│  │ InterviewKG  │  │ Question Gen │  │  Evaluation  │        │
│  │   methods    │  │              │  │   Request    │        │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘        │
│         │                                    │                │
│         │ Direct Python Calls                │ Async Messages │
│         │                                    │                │
└─────────┼────────────────────────────────────┼────────────────┘
          │                                    │
          ▼                                    ▼
┌─────────────────────┐            ┌──────────────────────┐
│  knowledge.py       │            │   evaluator.py       │
│  (Import Wrapper)   │            │   (Evaluation Agent) │
│                     │            │                      │
│  build_interview_kg()│            │  • Receives Request  │
└──────────┬──────────┘            │  • Calls ASI API    │
           │                       │  • Sends Response   │
           │ Import                └──────────┬───────────┘
           ▼                                  │
┌─────────────────────┐                      │
│    metta_sim        │                      │ Async Response
│  (Core Engine)      │                      │
│                     │                      │
│  • Atom class       │                      │
│  • KnowledgeGraph   │                      │
│  • build_interview_kg()                     │
│  • Query functions  │                      │
└─────────────────────┘                      │
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │   ASI Cloud API      │
                                  │   (Answer Eval)      │
                                  └──────────────────────┘
```

---

## Detailed Interaction Flows

### Flow 1: Initialization (System Startup)

```
1. interviewer.py imports:
   - from knowledge import build_interview_kg
   - from interviewrag import InterviewKG

2. knowledge.py imports:
   - from metta_sim import build_interview_kg as _build_interview_kg

3. interviewer.py calls:
   _kg = build_interview_kg()
   
   This triggers:
   - knowledge.py's build_interview_kg() 
   - Which calls metta_sim's build_interview_kg()
   - Which creates KnowledgeGraph and populates with facts
   - Returns populated KnowledgeGraph

4. interviewer.py creates:
   interview_kg = InterviewKG(_kg)
   
   This creates wrapper that stores the KnowledgeGraph instance
```

**Result**: System is initialized, knowledge graph is loaded, ready for queries.

---

### Flow 2: Question Generation (During Interview)

```
1. User selects avatar (e.g., "HR")
   interviewer.py receives: ChatMessage with "HR"

2. interviewer.py needs context for question generation:
   skills = interview_kg.get_focus_skills("HR")
   
   This calls:
   - InterviewKG.get_focus_skills() (interviewrag.py)
   - Which calls get_focus_skills(self.kg, "HR") (metta_sim)
   - Which queries: kg.query("focus_skill", "HR", "$skill")
   - KnowledgeGraph matches atoms and returns skills
   
   Returns: ["communication", "teamwork", "culture_fit", ...]

3. interviewer.py also gets topics:
   topics = interview_kg.get_topics_for_persona("HR", limit=3)
   
   Similar flow through layers, returns:
   [("culture_fit", 0.95), ("conflict_resolution", 0.9), ...]

4. interviewer.py builds prompt with KG context:
   prompt = f"""
   Persona: HR
   Focus skills: {skills}
   Recommended topics: {topics}
   Generate first question...
   """

5. interviewer.py calls ASI Cloud API:
   - HTTP POST request to ASI Cloud
   - Gets generated question back
   - Sends question to user
```

**Result**: Question generated with knowledge graph context, sent to user.

---

### Flow 3: Answer Processing (During Interview)

```
1. User provides answer
   interviewer.py receives: ChatMessage with answer text

2. interviewer.py stores answer:
   - Adds to session.answers[]
   - Adds Q&A pair to conversation_history[]

3. interviewer.py sends evaluation (async, non-blocking):
   await send_evaluation_request(
       question=current_question,
       answer=user_answer,
       persona=session.persona,
       role=session.role,
       user_address=sender
   )
   
   Creates EvaluationRequest message
   Sends to Evaluator Agent address
   Does NOT wait for response

4. interviewer.py generates next question immediately:
   - Queries KG for context (same as Flow 2)
   - Uses conversation_history for adaptive generation
   - Calls ASI Cloud API
   - Sends next question to user

5. In parallel, evaluator.py receives request:
   - Receives EvaluationRequest
   - Calls ASI Cloud API for evaluation
   - Gets scores and feedback
   - Sends EvaluationResponse back

6. interviewer.py receives evaluation (later):
   - Stores evaluation silently
   - No user feedback shown
   - Continues interview flow
```

**Result**: Answer stored, next question sent immediately, evaluation happens in background.

---

### Flow 4: Evaluation Response (Background)

```
1. evaluator.py receives EvaluationRequest
   - Contains: question, answer, persona, role

2. evaluator.py calls ASI Cloud API:
   - HTTP POST with evaluation prompt
   - Gets JSON response with scores

3. evaluator.py builds EvaluationResponse:
   - Extracts: clarity, specificity, confidence scores
   - Calculates overall score
   - Formats feedback text
   - Creates improved answer example

4. evaluator.py sends back to interviewer.py:
   - Async agent message
   - Contains all evaluation data

5. interviewer.py receives EvaluationResponse:
   - Stores in session.evaluations[]
   - Logs to user history
   - Checks if interview finished
   - If finished and all evals received → generate final report
```

**Result**: Evaluation stored silently, interview continues, report generated at end.

---

### Flow 5: Final Report Generation

```
1. After 5th answer:
   interviewer.py marks: session.finished = True
   Sends: "Generating your final report..."

2. When last evaluation received:
   interviewer.py checks: len(evaluations) >= QUESTIONS_PER_SESSION

3. interviewer.py generates report:
   - Calculates average scores
   - Analyzes strengths/weaknesses
   - Formats per-question breakdown
   - Generates actionable next steps

4. interviewer.py sends final report to user:
   - Complete evaluation summary
   - All scores and feedback
   - Strengths and areas to improve
```

**Result**: Comprehensive report sent to user, interview complete.

---

## Communication Patterns

### Pattern 1: Direct Python Function Calls (In-Process)

**Used between**:
- interviewer.py ↔ interviewrag.py
- interviewrag.py ↔ metta_sim
- knowledge.py ↔ metta_sim

**Characteristics**:
- Fast, synchronous
- Same process/memory space
- Direct function calls
- No network overhead

**Example**:
```python
# In interviewer.py
skills = interview_kg.get_focus_skills("HR")
# Direct call to InterviewKG method
# Which directly calls metta_sim function
# Which directly queries KnowledgeGraph
```

---

### Pattern 2: Async Agent Messaging (Network)

**Used between**:
- interviewer.py ↔ evaluator.py

**Characteristics**:
- Asynchronous (non-blocking)
- Network communication
- Separate agents/processes
- Message-based protocol

**Example**:
```python
# In interviewer.py
await ctx.send(EVALUATOR_ADDRESS, EvaluationRequest(...))
# Sends async message, doesn't wait
# Continues immediately with next question

# Later, evaluator.py sends back
await ctx.send(interviewer_address, EvaluationResponse(...))
```

---

### Pattern 3: HTTP API Calls (External Service)

**Used by**:
- interviewer.py → ASI Cloud API (question generation)
- evaluator.py → ASI Cloud API (answer evaluation)

**Characteristics**:
- Synchronous HTTP requests
- External service
- JSON request/response
- Network latency

**Example**:
```python
# In interviewer.py or evaluator.py
response = requests.post(ASI_API_URL, json=payload, headers=headers)
result = response.json()
```

---

## Data Flow Summary

### Knowledge Graph Data Flow

```
metta_sim (build_interview_kg)
    ↓ Creates & Populates
KnowledgeGraph instance
    ↓ Stored in
interviewer.py (_kg variable)
    ↓ Wrapped by
InterviewKG instance (interview_kg)
    ↓ Used by
interviewer.py methods
    ↓ Queries
KnowledgeGraph for facts
    ↓ Returns
Results used in prompts/decisions
```

### Interview Data Flow

```
User Message
    ↓
interviewer.py (receives)
    ↓
Process & Store Answer
    ↓
Send EvaluationRequest (async)
    ↓                    ↓
Generate Next Q      evaluator.py (in parallel)
    ↓                    ↓
Send to User         ASI Cloud API
    ↓                    ↓
User Sees Next Q     EvaluationResponse
                         ↓
                    interviewer.py (stores silently)
```

---

## File Dependencies

### Dependency Graph

```
interviewer.py
├── Depends on: interviewrag.py
├── Depends on: knowledge.py
├── Depends on: uagents (framework)
└── Uses: ASI Cloud API (external)

evaluator.py
├── Depends on: uagents (framework)
└── Uses: ASI Cloud API (external)

interviewrag.py
└── Depends on: metta_sim

knowledge.py
└── Depends on: metta_sim

metta_sim
└── No dependencies (pure Python standard library)
```

---

## Key Design Principles

### 1. Separation of Concerns
- **metta_sim**: Core engine (doesn't know about interviews)
- **interviewrag.py**: Domain wrapper (knows about interviews)
- **interviewer.py**: Application logic (orchestrates flow)
- **evaluator.py**: Evaluation service (separate concern)

### 2. Layered Architecture
- Foundation → Domain → Application
- Each layer builds on previous
- Clear interfaces between layers

### 3. Async Evaluation
- Interview flow continues immediately
- Evaluation happens in background
- No blocking operations

### 4. In-Process Knowledge Graph
- Fast direct calls
- No network overhead
- Shared memory

---

## Summary Table

| File | Role | Knows About | Interacts With |
|------|------|-------------|----------------|
| **metta_sim** | Core engine | Atoms, patterns, queries | Used by knowledge.py, interviewrag.py |
| **knowledge.py** | Import wrapper | Just re-exports | Imports metta_sim, used by interviewer.py |
| **interviewrag.py** | Domain wrapper | Interviews, skills, candidates | Uses metta_sim, used by interviewer.py |
| **interviewer.py** | Main application | Interview flow, sessions, users | Uses interviewrag, communicates with evaluator.py |
| **evaluator.py** | Evaluation service | Answer evaluation, scoring | Communicates with interviewer.py |

All working together to create a complete interview simulator! 🎯

