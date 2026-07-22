# Job Interview Simulator - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Interview Flow](#interview-flow)
5. [Knowledge Graph System](#knowledge-graph-system)
6. [Output and Evaluation](#output-and-evaluation)
7. [API Integration](#api-integration)
8. [File Structure](#file-structure)

**📊 For visual flowcharts, see:**
- `flowchart.md` - Comprehensive flowchart with Mermaid diagram
- `flowchart.dot` - Graphviz DOT format (for professional diagrams)
- `flowchart_simplified.md` - Quick reference visual overview
- `FLOWCHART_README.md` - Instructions for viewing/generating flowcharts

---

## Overview

This is a job interview simulator built using the uAgents framework. The system allows users to practice job interviews by selecting one of four different interviewer avatars (personas) and going through a natural, flowing interview conversation. The system evaluates answers in real-time and provides comprehensive feedback at the end.

### Key Features
- **Four Interviewer Avatars**: HR, Junior Developer, Senior Developer, Corporate Executive
- **Adaptive Question Generation**: Questions are generated dynamically based on previous answers
- **Natural Interview Flow**: Conversations flow naturally like real interviews
- **Knowledge Graph Integration**: Uses pure Python MeTTa-style knowledge graph (no Hyperon dependency)
- **Real-time Evaluation**: Answers are evaluated asynchronously during the interview
- **Comprehensive Final Report**: Detailed feedback with scores, strengths, and improvement areas

### Technology Stack
- **uAgents Framework**: Multi-agent system architecture
- **ASI Cloud API**: For question generation and answer evaluation
- **Pure Python Knowledge Graph**: Custom implementation (no binary dependencies)

---

## System Architecture

The system consists of two main agents:

### 1. Interviewer Agent (`interviewer.py`)
- Handles user interactions
- Manages interview sessions
- Generates questions adaptively
- Coordinates with evaluator agent

### 2. Evaluator Agent (`evaluator.py`)
- Evaluates candidate answers
- Provides scores and feedback
- Generates improved answer examples

### Communication Flow
```
User → Interviewer Agent → Evaluator Agent
  ↑                              ↓
  └──────── Response ────────────┘
```

---

## Core Components

### 1. Knowledge Graph System (`metta_sim`)

**Purpose**: Pure Python implementation of MeTTa-style symbolic reasoning for interview domain knowledge.

**Key Classes**:
- `Atom`: Represents a MeTTa-style atom `(predicate arg1 arg2 ...)`
- `KnowledgeGraph`: Stores and queries atoms with pattern matching

**Features**:
- Immutable atoms for safe pattern matching
- Variable binding queries (`$variable`)
- Wildcard matching (`_`)
- Predicate indexing for fast lookups

**Example**:
```python
kg.add_atom("focus_skill", "HR", "communication")
results = kg.match("focus_skill", "HR", "$skill")
# Returns: [{"$skill": "communication"}]
```

### 2. Interview Knowledge Graph Builder (`knowledge.py`)

**Purpose**: Wrapper that builds the interview-specific knowledge graph.

**Function**:
- `build_interview_kg()`: Creates knowledge graph with interview domain facts

### 3. InterviewKG Wrapper (`interviewrag.py`)

**Purpose**: High-level interface for interview-specific knowledge graph queries.

**Key Methods**:
- `get_focus_skills(persona)`: Get skills a persona focuses on
- `get_topics_for_persona(persona)`: Get recommended question topics
- `analyze_skill_gaps(user, role)`: Compare candidate skills vs role requirements
- `suggest_next_question_topic(persona, previous_topics)`: Suggest next topic

**Knowledge Graph Facts Stored**:
- Persona → Focus Skills mapping
- Question → Skills mapping
- Question follow-up chains
- Topic → Skills mapping
- Persona → Topic priorities
- Role requirements
- Skill prerequisites

### 4. Interviewer Agent (`interviewer.py`)

**Purpose**: Main agent handling interview flow and user interaction.

**Session State Management**:
```python
@dataclass
class SessionState:
    role: Optional[str]           # Job role (e.g., "Junior Data Analyst")
    persona: Optional[str]         # Interviewer avatar
    question_index: int            # Current question number
    finished: bool                 # Interview completion status
    answers: List[str]             # User's answers
    evaluations: List[Dict]        # Evaluation results
    questions: List[str]           # Generated questions
    conversation_history: List[Dict]  # Q&A pairs for adaptive generation
```

**Interview Avatars**:

1. **HR Interviewer**
   - Focus: Communication, teamwork, culture fit, professionalism
   - Style: Friendly, structured, policy-minded
   - Questions: Open-ended, assess soft skills

2. **Junior Developer Interviewer**
   - Focus: Problem-solving, learning, collaboration, basic technical skills
   - Style: Informal, collaborative, peer-level
   - Questions: Practical, concrete scenarios

3. **Senior Developer Interviewer**
   - Focus: System design, mentoring, trade-offs, code quality
   - Style: Direct, analytical, detail-oriented
   - Questions: Scenario-based, design decisions, edge cases

4. **Corporate Executive Interviewer**
   - Focus: Business impact, leadership, strategic thinking, stakeholder communication
   - Style: High-level, strategic, time-efficient
   - Questions: Big picture, business alignment

### 5. Evaluator Agent (`evaluator.py`)

**Purpose**: Evaluates candidate answers and provides structured feedback.

**Evaluation Metrics** (1-5 scale):
- **Clarity**: How clear and well-structured the answer is
- **Specificity**: Use of concrete examples, numbers, metrics
- **Confidence**: How confident and assertive the candidate sounds

**Overall Score**: Average of the three metrics

**Output**:
- Scores for each metric
- Constructive feedback (2-3 sentences)
- Improved example answer with specific details

---

## Interview Flow

### 1. Initialization Phase

1. User starts conversation with interviewer agent
2. System automatically sets role to "Junior Data Analyst"
3. User selects interviewer avatar (HR, Junior Developer, Senior Developer, Corporate Executive)
4. System logs role and persona selection
5. Persona-specific introduction message is displayed

### 2. Question Generation

#### First Question
- Generated using `generate_first_question_with_asi()`
- Query knowledge graph for persona focus skills
- ASI Cloud API generates broad opening question
- Question allows candidate to introduce themselves

#### Subsequent Questions
- Generated using `generate_next_adaptive_question()`
- Based on full conversation history (all previous Q&A pairs)
- Knowledge graph provides:
  - Persona focus skills
  - Recommended topics based on persona priorities
- Questions naturally follow from previous answers
- Adaptive and context-aware

### 3. Answer Processing

1. User provides answer
2. Answer is stored in session state
3. Q&A pair added to conversation history
4. Evaluation request sent to evaluator agent (asynchronous)
5. Interview continues immediately (no waiting for evaluation)

### 4. Evaluation Process

1. Evaluator agent receives evaluation request
2. ASI Cloud API evaluates answer on three dimensions
3. Evaluation stored silently (no user feedback during interview)
4. Evaluation includes:
   - Scores (clarity, specificity, confidence)
   - Overall score
   - Constructive feedback
   - Improved example answer

### 5. Interview Completion

After 5 questions:
1. Interview marked as finished
2. System waits for all evaluations to complete
3. Final report generated when all evaluations received
4. Report includes:
   - Role and interviewer style
   - Average scores
   - Detailed per-question feedback
   - Strengths identified
   - Areas for improvement
   - Next steps

---

## Knowledge Graph System

### Knowledge Graph Structure

The knowledge graph stores facts about:
- Interview personas and their focus areas
- Question-to-skill mappings
- Topic-to-skill relationships
- Role requirements
- Skill prerequisites

### Example Facts

```python
# Persona focus skills
(focus_skill HR communication)
(focus_skill HR teamwork)
(focus_skill Junior Developer problem_solving)

# Question skills
(question_skill Q1 communication)
(question_skill Q1 culture_fit)

# Persona priorities (weights)
(persona_priority HR culture_fit 0.95)
(persona_priority Senior Developer system_design 0.9)

# Role requirements
(role_requires Junior Data Analyst SQL intermediate)
(role_requires Junior Data Analyst Python basic)
```

### Query Examples

```python
# Get focus skills for HR persona
skills = interview_kg.get_focus_skills("HR")
# Returns: ["communication", "teamwork", "culture_fit", "professionalism"]

# Get recommended topics for persona
topics = interview_kg.get_topics_for_persona("HR", limit=3)
# Returns: [("culture_fit", 0.95), ("conflict_resolution", 0.9)]

# Analyze skill gaps
gaps = interview_kg.analyze_skill_gaps(user_address, "Junior Data Analyst")
# Returns: {
#     'mentioned': ['SQL', 'Python'],
#     'missing': ['Excel', 'data_visualization'],
#     'missing_prerequisites': []
# }
```

### Why Pure Python Implementation?

The system uses a pure Python implementation instead of Hyperon because:
- **Agentverse Compatibility**: Agentverse build environment doesn't support Hyperon package
- **No Binary Dependencies**: Pure Python works in restricted environments
- **Lightweight**: Simple, hackathon-friendly API
- **Sufficient Functionality**: Meets all interview domain requirements

---

## Output and Evaluation

### System Outputs

The system produces several types of outputs throughout the interview process:

#### 1. User-Facing Messages (Real-time)

**Welcome Message**: 
- Introduces the system
- Prompts for avatar selection

**Persona Introduction**:
- Explains the selected interviewer's style and focus areas
- Sets expectations for the interview

**Interview Questions**:
- Generated dynamically using ASI Cloud API
- Adaptive based on conversation history
- Natural and conversational

**Status Messages**:
- "Thanks for completing the interview! Generating your final report..."
- "This interview session is finished. Type 'restart' to begin a new one."

#### 2. Evaluation Outputs (Background/Stored)

Each answer is evaluated on three dimensions:
- **Clarity Score** (1-5): Structure and comprehensibility
- **Specificity Score** (1-5): Use of concrete examples and details
- **Confidence Score** (1-5): Assertiveness and decisiveness
- **Overall Score**: Average of the three metrics
- **Feedback Text**: 2-3 sentences of constructive feedback
- **Improved Answer Example**: Complete rewritten answer with specific details

#### 3. Final Report (Comprehensive Output)

The final report includes:
- Role and interviewer style information
- Number of questions answered
- Average scores across all dimensions
- Detailed per-question breakdown with scores and feedback
- Identified strengths (2-3 items)
- Areas for improvement (2-3 items)
- Actionable next steps

### During Interview

- **No feedback shown**: Evaluations happen silently in background
- **Natural flow**: Interview proceeds without interruption
- **Questions adapt**: Each question builds on previous answers

### Final Report Structure

```
✅ Interview complete – here's your detailed report

Role: Junior Data Analyst

Interviewer style: HR

Questions answered: 5

Average scores this session

Clarity: 3.8 / 5
Specificity: 2.5 / 5
Confidence: 3.2 / 5
Overall: 3.17 / 5

📋 Detailed Question-by-Question Feedback

Question 1: [Question text]

Your answer: "[Answer text]"

Scores: Clarity 4/5, Specificity 2/5, Confidence 3/5, Overall 3/5

Feedback: [Constructive feedback]

Improved example answer:
[Detailed improved version with specific examples]

---

[... continues for all questions ...]

💪 Strengths

[2-3 identified strengths]

🎯 Key areas to improve

[2-3 areas for improvement]

📝 Next steps

[Actionable next steps]
```

### Evaluation Criteria

#### Clarity (1-5)
- **5**: Extremely clear, well-structured, easy to follow
- **3**: Generally clear but could be better organized
- **1**: Confusing, unclear, hard to follow

#### Specificity (1-5)
- **5**: Rich with concrete examples, numbers, metrics, tools
- **3**: Some examples but could be more specific
- **1**: Very generic, lacks concrete details

#### Confidence (1-5)
- **5**: Very confident, assertive, decisive
- **3**: Moderately confident
- **1**: Uncertain, apologetic, lacks confidence

### Score Analysis Logic

The system analyzes scores to provide:
- **Strengths**: Identified when scores ≥ 3.5
- **Areas to improve**: Identified when scores < 3.0
- **Role-specific feedback**: Tailored to Junior Data Analyst role
- **Actionable next steps**: Based on specific weaknesses

---

## API Integration

### ASI Cloud API

**Endpoint**: `https://inference.asicloud.cudos.org/v1/chat/completions`

**Model**: `asi1-mini`

**Usage**:
1. **Question Generation**: Generates interview questions based on persona and context
2. **Answer Evaluation**: Evaluates answers and provides structured feedback

### Question Generation Prompts

#### First Question Prompt
```
- Persona description
- Role context
- Focus skills from knowledge graph
- Instruction to generate broad opening question
```

#### Adaptive Question Prompt
```
- Persona description
- Full conversation history (all previous Q&A)
- Focus skills from knowledge graph
- Recommended topics from knowledge graph
- Instruction to generate natural follow-up question
```

### Evaluation Prompt
```
- Question and answer
- Role and persona context
- Instructions for 3-dimensional scoring
- Request for JSON-formatted response
```

### Error Handling

- **API Failures**: Fallback to hardcoded questions
- **JSON Parsing Errors**: Default evaluation scores
- **Timeout Handling**: 30-second timeout with fallback

---

## File Structure

```
project/
├── metta_sim              # Pure Python MeTTa-style knowledge graph
│   ├── Atom class         # Atom representation
│   ├── KnowledgeGraph     # Graph storage and queries
│   ├── build_interview_kg()  # Domain knowledge builder
│   └── Query functions    # Helper query functions
│
├── knowledge.py           # Wrapper for knowledge graph builder
│
├── interviewrag.py        # InterviewKG wrapper class
│   └── InterviewKG        # High-level interview queries
│
├── interviewer.py         # Main interviewer agent
│   ├── SessionState       # Session management
│   ├── Question generation functions
│   ├── Interview flow handlers
│   └── Final report generator
│
└── evaluator.py          # Evaluator agent
    ├── EvaluationRequest/Response models
    └── ASI Cloud evaluation logic
```

---

## Key Design Decisions

### 1. Two-Agent Architecture
- **Separation of Concerns**: Interview flow separate from evaluation
- **Scalability**: Evaluator can handle multiple interviews
- **Asynchronous Processing**: Interview continues while evaluation happens

### 2. Adaptive Question Generation
- **Conversation History**: Full context for natural flow
- **Knowledge Graph Guidance**: Ensures questions align with persona goals
- **ASI Cloud API**: Provides natural language generation

### 3. Silent Evaluation During Interview
- **Natural Experience**: No interruption to interview flow
- **Comprehensive Feedback**: All feedback at end for better learning

### 4. Pure Python Knowledge Graph
- **Agentverse Compatibility**: No binary dependencies
- **Sufficient Functionality**: Meets all domain requirements
- **Maintainability**: Simple, readable code

### 5. Session State Management
- **Persistent Storage**: Uses uAgents storage for session persistence
- **Multi-user Support**: Each user has isolated session
- **Resumable**: Sessions can be resumed if interrupted

---

## Usage Flow Example

```
1. User: "Hello"
   System: Welcome message + avatar selection prompt

2. User: "HR"
   System: HR introduction + First question generated

3. User: "I have 3 years of experience in data analysis..."
   System: [Stores answer, sends evaluation, generates next question]
   System: Second question (adapts based on answer)

4. User: "I used Python and SQL to clean datasets..."
   System: [Stores answer, sends evaluation, generates next question]
   System: Third question (continues natural flow)

5. ... continues for 5 questions ...

6. After 5th answer:
   System: "Thanks for completing the interview! Generating your final report..."
   System: [Waits for all evaluations]
   System: Comprehensive final report with scores and feedback
```

---

## Extensibility

### Adding New Personas
1. Add persona to `PERSONAS` list
2. Add persona description to dictionaries
3. Add focus skills to knowledge graph
4. Add persona priorities to knowledge graph

### Adding New Roles
1. Add role to `ROLES` list
2. Add role requirements to knowledge graph
3. Update role-specific feedback logic

### Customizing Evaluation
- Modify evaluation prompt in `evaluator.py`
- Adjust scoring criteria
- Add new evaluation dimensions

### Extending Knowledge Graph
- Add new predicate types in `build_interview_kg()`
- Add query functions in `metta_sim`
- Use in question generation logic

---

## Technical Notes

### Session Keys
- Uses `x-session-id` if present, else falls back to sender address
- Format: `session:{session_id}` or `session:sender:{address}`

### Evaluation Mapping
- Stores mapping from user address to session key
- Allows evaluator response to update correct session

### Conversation History Format
```python
[
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    ...
]
```

### Evaluation Data Format
```python
{
    "question": "...",
    "answer": "...",
    "clarity": 4,
    "specificity": 2,
    "confidence": 3,
    "overall_score": 3.0,
    "feedback": "...",
    "improved_answer": "..."
}
```

---

## Conclusion

This job interview simulator provides a comprehensive, natural interview practice experience with:
- **Multiple interviewer personas** for varied practice
- **Adaptive question generation** for natural conversation flow
- **Comprehensive evaluation** with detailed feedback
- **Knowledge graph integration** for intelligent question routing
- **Pure Python implementation** for maximum compatibility

The system is designed to be extensible, maintainable, and provide a realistic interview practice environment for candidates.

