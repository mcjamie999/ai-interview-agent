# Job Interview Simulator - Simplified Flowchart

## Quick Visual Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                     (Agentverse Chat UI)                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ ChatMessage
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERVIEWER AGENT                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  SessionState: role, persona, questions, answers, evals     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             │ In-Process Calls                       │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              InterviewKG Wrapper                              │  │
│  │  • get_focus_skills(persona)                                 │  │
│  │  • get_topics_for_persona(persona)                           │  │
│  └──────────────────┬───────────────────────────────────────────┘  │
│                     │                                                │
└─────────────────────┼───────────────────────────────────────────────┘
                      │
                      │ Direct Python Function Calls
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│          METTA KNOWLEDGE GRAPH (Pure Python)                        │
│  • Persona → Focus Skills Mapping                                   │
│  • Persona → Topic Priorities                                       │
│  • Question → Skills Mapping                                        │
│  • Role Requirements                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    INTERVIEWER AGENT                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Question Generation Flow:                                   │  │
│  │  1. Query KG for persona skills/topics                       │  │
│  │  2. Build prompt with KG context + conversation_history      │  │
│  │  3. Call ASI Cloud API → Get question                        │  │
│  │  4. Send question to user                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Answer Processing Flow:                                     │  │
│  │  1. Store answer in session                                  │  │
│  │  2. Add to conversation_history                              │  │
│  │  3. Send EvaluationRequest (async) → Evaluator Agent         │  │
│  │  4. Generate next question immediately                       │  │
│  │  5. Store EvaluationResponse when received (silently)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ Async Agent Messaging
                      │
                      │ EvaluationRequest
                      │                    EvaluationResponse
                      │◀────────────────────────────────────
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                    EVALUATOR AGENT                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Receive EvaluationRequest                                │  │
│  │  2. Call ASI Cloud API with evaluation prompt                │  │
│  │  3. Get scores: Clarity, Specificity, Confidence             │  │
│  │  4. Get feedback text and improved answer                    │  │
│  │  5. Build EvaluationResponse                                 │  │
│  │  6. Send back to Interviewer Agent                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ HTTP API Calls
                      │
┌─────────────────────▼───────────────────────────────────────────────┐
│                    ASI CLOUD API                                    │
│                  (asi1-mini Model)                                  │
│  • Question Generation                                              │
│  • Answer Evaluation                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Flow

### 1️⃣ Initialization Phase
```
User → [ChatMessage] → Interviewer Agent
                    ↓
              Send ACK
                    ↓
         Auto-set Role: "Junior Data Analyst"
                    ↓
          Display Avatar Options
                    ↓
    User Selects: HR / Junior Dev / Senior Dev / Corporate Exec
                    ↓
         Store Persona Selection
```

### 2️⃣ First Question Generation
```
Interviewer Agent → Query InterviewKG.get_focus_skills(persona)
                 ↓
        MeTTa KG Returns Skills
                 ↓
    Build prompt with persona + skills + role
                 ↓
    Call ASI Cloud API (Question Generation)
                 ↓
         Get First Question
                 ↓
    Send Persona Intro + First Question to User
```

### 3️⃣ Interview Loop (Repeat 5 times)
```
User Answer → Store in Session
           ↓
    Add to conversation_history
           ↓
    ┌──────────────────────────┐
    │ Send EvaluationRequest   │  (ASYNC - doesn't wait)
    │ to Evaluator Agent       │
    └──────────────────────────┘
           ↓
    Query InterviewKG for next question context
           ↓
    Get focus skills + topic priorities from KG
           ↓
    Build prompt with:
    - conversation_history (all previous Q&A)
    - persona description
    - KG skills/topics
           ↓
    Call ASI Cloud API (Adaptive Question Generation)
           ↓
    Get Next Question
           ↓
    Send Next Question to User (immediately)
           ↓
    [In Parallel] Evaluator processes answer...
```

### 4️⃣ Evaluation (Happens in Parallel)
```
Evaluator Agent ← EvaluationRequest
                ↓
        Build evaluation prompt
                ↓
    Call ASI Cloud API (Evaluation)
                ↓
    Get JSON with:
    - clarity, specificity, confidence scores
    - feedback text
    - improved_answer
                ↓
        Build EvaluationResponse
                ↓
    Send back to Interviewer Agent
                ↓
    Interviewer Agent stores silently
    (no user feedback shown)
```

### 5️⃣ Final Report
```
After 5th Answer:
    ↓
Mark Interview Finished
    ↓
Send "Generating report..." message
    ↓
Wait for all evaluations to complete
    ↓
When last evaluation received:
    ↓
Calculate average scores
Analyze strengths/weaknesses
Format per-question breakdown
Generate actionable next steps
    ↓
Send Comprehensive Final Report to User
    ↓
Interview Complete ✓
```

## Key Data Structures

### SessionState
```python
{
    "role": "Junior Data Analyst",
    "persona": "HR",
    "question_index": 3,
    "finished": False,
    "answers": ["answer1", "answer2", "answer3"],
    "questions": ["Q1", "Q2", "Q3"],
    "conversation_history": [
        {"question": "Q1", "answer": "answer1"},
        {"question": "Q2", "answer": "answer2"},
        {"question": "Q3", "answer": "answer3"}
    ],
    "evaluations": [
        {
            "question": "Q1",
            "answer": "answer1",
            "clarity": 4,
            "specificity": 2,
            "confidence": 3,
            "overall_score": 3.0,
            "feedback": "...",
            "improved_answer": "..."
        },
        ...
    ]
}
```

### EvaluationResponse
```python
{
    "question": "...",
    "answer": "...",
    "persona": "HR",
    "role": "Junior Data Analyst",
    "user_address": "...",
    "clarity": 4,
    "specificity": 2,
    "confidence": 3,
    "overall_score": 3.0,
    "feedback": "Constructive feedback text...",
    "improved_answer": "Improved example answer..."
}
```

## Communication Patterns

| Component A | Component B | Method | Direction |
|------------|-------------|--------|-----------|
| User | Interviewer Agent | ChatMessage | Bidirectional |
| Interviewer Agent | InterviewKG | Python function calls | In-process |
| InterviewKG | MeTTa KG | Python function calls | In-process |
| Interviewer Agent | Evaluator Agent | Agent messaging | Async bidirectional |
| Interviewer Agent | ASI Cloud API | HTTP POST | Request/Response |
| Evaluator Agent | ASI Cloud API | HTTP POST | Request/Response |

## Timing Diagram

```
Time →

User:          [Select Avatar] [Answer 1] [Answer 2] ... [Answer 5]
                     ↓            ↓          ↓              ↓
Interviewer:   [Setup] → [Q1] → [Eval1] → [Q2] → [Eval2] → ... → [Q5] → [Report]
                     ↓            ↓          ↓              ↓           ↓
Evaluator:           [────] [Eval1] [────] [Eval2] [────] ... [Eval5] [────]
                           ↓              ↓                      ↓
ASI API:                  [Eval1]        [Eval2]                [Eval5]
```

Note: Evaluations happen asynchronously. Interview continues without waiting.

