from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import requests
import json
import re

from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    StartSessionContent,
    EndSessionContent,
    TextContent,
    MetadataContent,
    chat_protocol_spec,
)

# -------------------------------------------------------
# MeTTa-inspired Knowledge Graph (Pure Python)
# -------------------------------------------------------
from knowledge import build_interview_kg
from interviewrag import InterviewKG

# Initialize knowledge graph at module load
_kg = build_interview_kg()
interview_kg = InterviewKG(_kg)

# -------------------------------------------------------
# Interviewer Personas + Questions + Session State
# -------------------------------------------------------

ROLES = ["Junior Data Analyst"]  # Only one role supported
PERSONAS = ["HR", "Junior Developer", "Senior Developer", "Corporate Executive"]

# In-memory interview history per user (resets on agent restart)
# Structure: {user_address: {role, persona, interview_history: [{question, answer, scores, timestamp}]}}
INTERVIEW_HISTORY: Dict[str, Dict[str, Any]] = {}

# Number of questions per interview session
QUESTIONS_PER_SESSION = 5

# Fallback questions if API generation fails
PERSONA_QUESTIONS: Dict[str, List[str]] = {
    "HR": [
        "Can you tell me a bit about yourself and why you're interested in this role?",
        "Tell me about a time you had a conflict in a team. How did you handle it?",
        "What motivates you at work?",
        "How do you handle feedback, especially when it's critical?",
        "What are your salary expectations for this position?",
    ],
    "Junior Developer": [
        "How would you approach debugging a bug that's hard to reproduce?",
        "Tell me about a time you had to ask for help on a technical problem. What did you learn?",
        "How do you stay motivated when working on a challenging technical problem?",
        "Can you walk me through how you'd explain a technical concept to a non-technical teammate?",
        "What's your process for learning a new technology or tool?",
    ],
    "Senior Developer": [
        "Walk me through how you would design a system to handle [specific scenario]. What trade-offs would you consider?",
        "Tell me about a time you had to make a technical decision under pressure. How did you evaluate the options?",
        "How do you approach code reviews? What do you look for?",
        "Describe a situation where you had to balance technical perfection with business deadlines.",
        "How would you mentor a junior developer who's struggling with a concept?",
    ],
    "Corporate Executive": [
        "How would you prioritise between improving code quality and delivering new features quickly?",
        "Tell me about a decision you made that had meaningful business impact.",
        "How do you ensure your technical work aligns with the company's strategic goals?",
        "Describe a time when you had to communicate a technical issue to non-technical stakeholders.",
        "What does leadership mean to you in the context of a technical role?",
    ],
}

# -------------------------------------------------------
# ASI Cloud Configuration for Question Generation
# -------------------------------------------------------

# ASI Cloud API Configuration
# TODO: Move API key to environment variable for security
# import os
# ASI_API_KEY = os.getenv("ASI_API_KEY", "your-key-here")
ASI_API_KEY = "sk-FVoN14UREfvuUPIZugEWKiJGuxMROZ18Ahz4MT6L8TE"
ASI_API_URL = "https://inference.asicloud.cudos.org/v1/chat/completions"
ASI_MODEL = "asi1-mini"


@dataclass
class SessionState:
    role: Optional[str] = None
    persona: Optional[str] = None
    question_index: int = 0
    finished: bool = False
    answers: List[str] = None
    evaluations: List[Dict[str, Any]] = None
    questions: List[str] = None  # Store generated questions (for backward compatibility)
    conversation_history: List[Dict[str, str]] = None  # Store Q&A pairs: [{"question": "...", "answer": "..."}]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "persona": self.persona,
            "question_index": self.question_index,
            "finished": self.finished,
            "answers": self.answers or [],
            "evaluations": self.evaluations or [],
            "questions": self.questions or [],
            "conversation_history": self.conversation_history or [],
        }

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> "SessionState":
        if not d:
            return SessionState(role=None, persona=None, question_index=0, finished=False, answers=[], evaluations=[], questions=[], conversation_history=[])
        return SessionState(
            role=d.get("role"),
            persona=d.get("persona"),
            question_index=d.get("question_index", 0),
            finished=d.get("finished", False),
            answers=d.get("answers", []),
            evaluations=d.get("evaluations", []),
            questions=d.get("questions", []),
            conversation_history=d.get("conversation_history", []),
        )


# -------------------------------------------------------
# Helper function to normalize persona/role names (case-insensitive matching)
# -------------------------------------------------------

def normalize_persona_name(user_input: str) -> Optional[str]:
    """Normalize user input to match capitalized persona names (case-insensitive)."""
    user_lower = user_input.lower().strip()
    persona_map = {
        "hr interviewer": "HR",
        "hr": "HR",
        "junior developer": "Junior Developer",
        "senior developer": "Senior Developer",
        "corporate executive": "Corporate Executive",
    }
    return persona_map.get(user_lower)

def normalize_role_name(user_input: str) -> Optional[str]:
    """Normalize user input to match capitalized role names (case-insensitive)."""
    user_lower = user_input.lower().strip()
    role_map = {
        "junior data analyst": "Junior Data Analyst",
    }
    return role_map.get(user_lower)

# -------------------------------------------------------
# ASI Cloud Question Generation
# -------------------------------------------------------

async def generate_first_question_with_asi(role: str, persona: str) -> str:
    """
    Generate the first, broad opening question for the interview.
    This question should be general and allow the candidate to introduce themselves.
    
    Uses MeTTa-inspired knowledge graph to enhance prompt with persona focus skills.
    """
    # Query knowledge graph for persona focus skills
    focus_skills = interview_kg.get_focus_skills(persona)
    skills_context = ", ".join(focus_skills) if focus_skills else "general professional skills"
    
    persona_descriptions = {
        "hr interviewer": "You are an HR interviewer focusing on culture fit, communication, and basic role alignment. You check whether the candidate's values, attitude, and behaviour match the company culture. You verify basic qualifications, work eligibility, and salary expectations. You assess soft skills: communication, teamwork, professionalism. Your style is friendly, structured, and policy-minded. You ask open questions and pay close attention to how clearly and honestly the candidate answers.",
        "junior developer": "You are a junior developer interviewer, relatively early in your own career and closer to the candidate's level. You understand the practical realities of junior work. You test basic technical understanding and problem-solving skills. You see how the candidate collaborates and explains ideas to peers. You evaluate willingness to learn, ask questions, and accept feedback. Your style is informal and collaborative. You often use simpler, concrete questions and may share your own experiences. You're less intimidating, but still notice whether the candidate is curious, humble, and logical.",
        "senior developer": "You are a senior developer or tech lead interviewer, deeply technical and responsible for system quality and team productivity. You assess depth of technical knowledge and reasoning, not just memorised answers. You evaluate how the candidate designs, scales, and maintains systems in the real world. You check code quality, trade-off thinking, and ability to mentor or be mentored. Your style is direct, analytical, and detail-oriented. You ask scenario-based and 'why?' questions, dig into design decisions, edge cases, and trade-offs. You're less interested in buzzwords, more in how the candidate thinks under pressure and explains their solutions.",
        "corporate executive": "You are a corporate executive interviewer (e.g., CTO, VP, founder) who cares about the 'big picture': business impact, risk, and long-term value. You understand how the candidate contributes to business goals, not just code. You gauge leadership potential, judgement, and maturity. You assess whether the candidate can represent the company well with clients and stakeholders. Your style is high-level, strategic, and time-efficient. You ask broad, probing questions and focus on clarity, confidence, ownership, and alignment with the company's mission.",
    }
    
    persona_desc = persona_descriptions.get(persona, "professional and standard interviewer")
    
    prompt = f"""You are an expert interviewer conducting an interview for a {role} position.

You are acting as: {persona_desc}

Based on symbolic reasoning, your interviewer persona focuses on these key skills: {skills_context}.
Use this knowledge to craft a question that naturally assesses these areas.

Generate ONE broad, opening question to start the interview. This should be:
1. A general question that allows the candidate to introduce themselves or share their background
2. Appropriate for a {role} role
3. Match your interviewer avatar style and focus on: {skills_context}
4. Natural and conversational - something that would start a real interview
5. Open-ended enough to allow the candidate to share meaningful information

Return ONLY the question text, nothing else. No JSON, no explanations, just the question."""

    try:
        payload = {
            "model": ASI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
        }
        
        headers = {
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(ASI_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        question = result["choices"][0]["message"]["content"].strip()
        
        # Clean up the question (remove quotes if present, remove markdown formatting)
        question = question.strip('"').strip("'").strip()
        if question.startswith("**"):
            question = question.replace("**", "")
        
        return question
        
    except Exception as e:
        print(f"ASI API error generating first question: {e}")
        # Fallback to a generic opening question
        fallback_questions = PERSONA_QUESTIONS.get(persona, PERSONA_QUESTIONS["HR"])
        return fallback_questions[0] if fallback_questions else "Can you tell me a bit about yourself?"


async def generate_next_adaptive_question(
    role: str, 
    persona: str, 
    conversation_history: List[Dict[str, str]],
    question_number: int
) -> str:
    """
    Generate the next question adaptively based on previous Q&A pairs.
    The question should naturally follow from the candidate's previous answers.
    
    Uses MeTTa-inspired knowledge graph to:
    1. Get persona focus skills for question alignment
    2. Suggest next question topics based on persona priorities
    3. Ensure questions assess relevant skills
    """
    # Query knowledge graph for persona focus skills and recommended topics
    focus_skills = interview_kg.get_focus_skills(persona)
    skills_context = ", ".join(focus_skills) if focus_skills else "general professional skills"
    
    # Get recommended topics for this persona (prioritized)
    recommended_topics = interview_kg.get_topics_for_persona(persona, limit=3)
    topics_context = ", ".join([topic for topic, _ in recommended_topics]) if recommended_topics else ""
    
    persona_descriptions = {
        "HR": "You are an HR interviewer focusing on culture fit, communication, and basic role alignment. You check whether the candidate's values, attitude, and behaviour match the company culture. You verify basic qualifications, work eligibility, and salary expectations. You assess soft skills: communication, teamwork, professionalism. Your style is friendly, structured, and policy-minded. You ask open questions and pay close attention to how clearly and honestly the candidate answers.",
        "Junior Developer": "You are a junior developer interviewer, relatively early in your own career and closer to the candidate's level. You understand the practical realities of junior work. You test basic technical understanding and problem-solving skills. You see how the candidate collaborates and explains ideas to peers. You evaluate willingness to learn, ask questions, and accept feedback. Your style is informal and collaborative. You often use simpler, concrete questions and may share your own experiences. You're less intimidating, but still notice whether the candidate is curious, humble, and logical.",
        "Senior Developer": "You are a senior developer or tech lead interviewer, deeply technical and responsible for system quality and team productivity. You assess depth of technical knowledge and reasoning, not just memorised answers. You evaluate how the candidate designs, scales, and maintains systems in the real world. You check code quality, trade-off thinking, and ability to mentor or be mentored. Your style is direct, analytical, and detail-oriented. You ask scenario-based and 'why?' questions, dig into design decisions, edge cases, and trade-offs. You're less interested in buzzwords, more in how the candidate thinks under pressure and explains their solutions.",
        "Corporate Executive": "You are a corporate executive interviewer (e.g., CTO, VP, founder) who cares about the 'big picture': business impact, risk, and long-term value. You understand how the candidate contributes to business goals, not just code. You gauge leadership potential, judgement, and maturity. You assess whether the candidate can represent the company well with clients and stakeholders. Your style is high-level, strategic, and time-efficient. You ask broad, probing questions and focus on clarity, confidence, ownership, and alignment with the company's mission.",
    }
    
    persona_desc = persona_descriptions.get(persona, "professional and standard interviewer")
    
    # Build conversation context
    conversation_text = ""
    for i, qa in enumerate(conversation_history, 1):
        conversation_text += f"Question {i}: {qa.get('question', '')}\n"
        conversation_text += f"Answer {i}: {qa.get('answer', '')}\n\n"
    
    # Build symbolic reasoning context
    kg_context = f"""
Symbolic Reasoning Context:
- Your persona focuses on these skills: {skills_context}
- Recommended question topics for your persona: {topics_context}
- Use this knowledge to ensure your question aligns with your interviewer's assessment goals.
"""
    
    prompt = f"""You are an expert interviewer conducting an interview for a {role} position.

You are acting as: {persona_desc}

{kg_context}

So far in this interview, you have asked the following questions and received these answers:

{conversation_text}

Based on the candidate's previous answers, generate the next question (Question {question_number}) that:
1. Naturally follows from what the candidate has shared - build on their previous answers
2. Digs deeper into interesting points they mentioned, or explores new relevant areas
3. Is appropriate for a {role} role
4. Matches your interviewer avatar style and focuses on assessing: {skills_context}
5. Feels like a natural continuation of the conversation
6. Is clear, concise, and ready to ask directly
7. Aligns with recommended topics: {topics_context} (when relevant)

IMPORTANT: Make the question feel like a real conversation. Reference or build upon something from their previous answers when relevant, but don't force it. The question should flow naturally while still assessing the key skills your persona focuses on.

Return ONLY the question text, nothing else. No JSON, no explanations, just the question."""

    try:
        payload = {
            "model": ASI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,  # Higher temperature for more natural, varied follow-ups
        }
        
        headers = {
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(ASI_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        question = result["choices"][0]["message"]["content"].strip()
        
        # Clean up the question
        question = question.strip('"').strip("'").strip()
        if question.startswith("**"):
            question = question.replace("**", "")
        
        return question
        
    except Exception as e:
        print(f"ASI API error generating adaptive question: {e}")
        # Fallback: try to generate a generic question based on persona
        fallback_questions = PERSONA_QUESTIONS.get(persona, PERSONA_QUESTIONS["HR"])
        if question_number <= len(fallback_questions):
            return fallback_questions[question_number - 1]
        else:
            return "Can you tell me more about that?"


async def generate_questions_with_asi(role: str, persona: str, num_questions: int = QUESTIONS_PER_SESSION) -> List[str]:
    """
    Generate interview questions using ASI Cloud API based on role and persona.
    Returns a list of questions, or falls back to hardcoded questions if API fails.
    """
    # Build the prompt for question generation
    persona_descriptions = {
        "HR": "You are an HR interviewer focusing on culture fit, communication, and basic role alignment. You check whether the candidate's values, attitude, and behaviour match the company culture. You verify basic qualifications, work eligibility, and salary expectations. You assess soft skills: communication, teamwork, professionalism. Your style is friendly, structured, and policy-minded. You ask open questions and pay close attention to how clearly and honestly the candidate answers.",
        "Junior Developer": "You are a junior developer interviewer, relatively early in your own career and closer to the candidate's level. You understand the practical realities of junior work. You test basic technical understanding and problem-solving skills. You see how the candidate collaborates and explains ideas to peers. You evaluate willingness to learn, ask questions, and accept feedback. Your style is informal and collaborative. You often use simpler, concrete questions and may share your own experiences. You're less intimidating, but still notice whether the candidate is curious, humble, and logical.",
        "Senior Developer": "You are a senior developer or tech lead interviewer, deeply technical and responsible for system quality and team productivity. You assess depth of technical knowledge and reasoning, not just memorised answers. You evaluate how the candidate designs, scales, and maintains systems in the real world. You check code quality, trade-off thinking, and ability to mentor or be mentored. Your style is direct, analytical, and detail-oriented. You ask scenario-based and 'why?' questions, dig into design decisions, edge cases, and trade-offs. You're less interested in buzzwords, more in how the candidate thinks under pressure and explains their solutions.",
        "Corporate Executive": "You are a corporate executive interviewer (e.g., CTO, VP, founder) who cares about the 'big picture': business impact, risk, and long-term value. You understand how the candidate contributes to business goals, not just code. You gauge leadership potential, judgement, and maturity. You assess whether the candidate can represent the company well with clients and stakeholders. Your style is high-level, strategic, and time-efficient. You ask broad, probing questions and focus on clarity, confidence, ownership, and alignment with the company's mission.",
    }
    
    persona_desc = persona_descriptions.get(persona, "professional and standard interviewer")
    
    prompt = f"""You are an expert interviewer creating interview questions for a {role} position.

You are acting as: {persona_desc}

Generate exactly {num_questions} interview questions that:
1. Are appropriate for a {role} role
2. Match the interviewer avatar style and goals described above
3. Are diverse and cover different aspects relevant to this interviewer type
4. Are clear, concise, and ready to ask directly to a candidate
5. Reflect the specific focus areas and style of this interviewer type

Return ONLY a JSON array of strings, one question per string, like this:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]

Do not include any other text, explanations, or markdown formatting. Just the JSON array."""

    try:
        # Call ASI Cloud API
        payload = {
            "model": ASI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # Slightly higher temperature for more varied questions
        }
        
        headers = {
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(ASI_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result["choices"][0]["message"]["content"].strip()
        
        # Parse the JSON response from ASI
        # Try to extract JSON array from the response (it might have markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', ai_response)
        if json_match:
            json_str = json_match.group(0)
            questions = json.loads(json_str)
        else:
            # Fallback: try to parse the whole response as JSON
            questions = json.loads(ai_response)
        
        # Validate that we got a list of strings
        if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
            # Ensure we have the right number of questions
            if len(questions) >= num_questions:
                return questions[:num_questions]
            elif len(questions) > 0:
                # If we got fewer questions, return what we have
                return questions
            else:
                raise ValueError("Empty questions list from API")
        else:
            raise ValueError("Invalid format from API")
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        # API call failed - fallback to hardcoded questions
        print(f"ASI API error generating questions: {e}")
        print(f"Falling back to hardcoded questions for persona: {persona}")
        # Return fallback questions
        fallback_questions = PERSONA_QUESTIONS.get(persona, PERSONA_QUESTIONS["HR"])
        return fallback_questions[:num_questions]


# -------------------------------------------------------
# Evaluation Models (for talking to evaluator agent)
# -------------------------------------------------------

class EvaluationRequest(Model):
    question: str
    answer: str
    persona: Optional[str] = None
    role: Optional[str] = None
    user_address: str


class EvaluationResponse(Model):
    question: str
    answer: str
    persona: Optional[str] = None
    role: Optional[str] = None
    user_address: str

    clarity: int
    specificity: int
    confidence: int
    overall_score: float

    feedback: str
    improved_answer: str


# -------------------------------------------------------
# Helpers for session key + storage
# -------------------------------------------------------

def get_session_key(sender: str, msg: ChatMessage) -> str:
    """
    Prefer x-session-id if present, else fall back to sender.
    This key is what we use in ctx.storage.
    """
    for item in msg.content:
        if isinstance(item, MetadataContent):
            sid = item.metadata.get("x-session-id")
            if sid:
                return f"session:{sid}"
    return f"session:sender:{sender}"


def load_session(ctx: Context, session_key: str) -> SessionState:
    stored = ctx.storage.get(session_key)
    session = SessionState.from_dict(stored)
    ctx.logger.info(
        f"Loaded session for {session_key}: role={session.role}, persona={session.persona}, "
        f"q_index={session.question_index}, finished={session.finished}"
    )
    return session


def save_session(ctx: Context, session_key: str, session: SessionState):
    ctx.storage.set(session_key, session.to_dict())
    ctx.logger.info(
        f"Saved session for {session_key}: role={session.role}, persona={session.persona}, "
        f"q_index={session.question_index}, finished={session.finished}"
    )


# -------------------------------------------------------
# In-memory logging functions for demo
# -------------------------------------------------------

def initialize_user_history(user_address: str):
    """Initialize a new interview history entry for a user."""
    INTERVIEW_HISTORY[user_address] = {
        "role": None,
        "persona": None,
        "interview_history": []  # List of {question, answer, clarity, specificity, confidence, overall_score, timestamp}
    }


def get_user_history(user_address: str) -> Dict[str, Any]:
    """Get the interview history for a user."""
    if user_address not in INTERVIEW_HISTORY:
        initialize_user_history(user_address)
    return INTERVIEW_HISTORY[user_address]


def log_role_selection(user_address: str, role: str):
    """Log the selected role for a user."""
    history = get_user_history(user_address)
    history["role"] = role


def log_persona_selection(user_address: str, persona: str):
    """Log the selected persona for a user."""
    history = get_user_history(user_address)
    history["persona"] = persona


def log_question_answer_evaluation(
    user_address: str,
    question: str,
    answer: str,
    clarity: int,
    specificity: int,
    confidence: int,
    overall_score: float
):
    """Log a complete Q&A with evaluation scores and timestamp."""
    history = get_user_history(user_address)
    history["interview_history"].append({
        "question": question,
        "answer": answer,
        "clarity": clarity,
        "specificity": specificity,
        "confidence": confidence,
        "overall_score": overall_score,
        "timestamp": datetime.utcnow().isoformat()
    })


def reset_user_history(user_address: str):
    """Reset the interview history for a user (for restart command)."""
    initialize_user_history(user_address)


def get_user_interview_history(user_address: str) -> Dict[str, Any]:
    """
    Get the complete interview history for a user.
    Returns: {
        "role": str or None,
        "persona": str or None,
        "interview_history": [
            {
                "question": str,
                "answer": str,
                "clarity": int,
                "specificity": int,
                "confidence": int,
                "overall_score": float,
                "timestamp": str (ISO format)
            },
            ...
        ]
    }
    """
    return get_user_history(user_address)


def generate_end_of_interview_summary(session: SessionState) -> str:
    """Generate end-of-interview summary matching the example format."""
    if not session.evaluations or len(session.evaluations) == 0:
        return "Interview complete. No evaluations available."
    
    evals = session.evaluations
    n = len(evals)
    
    # Calculate averages
    avg_clarity = round(sum(e.get("clarity", 0) for e in evals) / n, 2)
    avg_specificity = round(sum(e.get("specificity", 0) for e in evals) / n, 2)
    avg_confidence = round(sum(e.get("confidence", 0) for e in evals) / n, 2)
    avg_overall = round(sum(e.get("overall_score", 0) for e in evals) / n, 2)
    
    # Determine strengths and areas to improve based on scores
    strengths = []
    areas_to_improve = []
    
    # Clarity analysis
    if avg_clarity >= 3.5:
        strengths.append("You explain your motivations clearly and stay on topic.")
    elif avg_clarity < 3.0:
        areas_to_improve.append("Structure your answers more clearly using situation → action → result.")
    
    # Specificity analysis
    if avg_specificity < 3.0:
        if not any("specific" in s.lower() or "examples" in s.lower() for s in areas_to_improve):
            areas_to_improve.append("Your examples are often too general. Add numbers, tools, and concrete outcomes.")
    elif avg_specificity >= 3.5:
        strengths.append("You use concrete examples and specific details effectively.")
    
    # Confidence analysis
    if avg_confidence >= 3.5:
        if not any("confident" in s.lower() for s in strengths):
            strengths.append("You generally sound confident when talking about your background.")
    elif avg_confidence < 3.0:
        areas_to_improve.append("Use more direct language ('I led', 'I delivered') and avoid apologetic phrasing.")
    
    # Role-specific improvements
    if session.role == "Junior Data Analyst":
        if avg_specificity < 3.0:
            if not any("technical" in s.lower() or "data" in s.lower() for s in areas_to_improve):
                areas_to_improve.append("For technical questions, mention datasets, metrics, and specific steps you took.")
    
    # Fill strengths if needed
    if len(strengths) == 0:
        if avg_overall >= 3.0:
            strengths.append("You show willingness to work hard and take responsibility.")
        else:
            strengths.append("You're comfortable speaking about yourself and stay reasonably on topic.")
    
    # Fill areas to improve if needed
    if len(areas_to_improve) == 0:
        areas_to_improve.append("Continue refining your interview responses with more specific examples.")
    
    # Limit to 2-3 items each
    strengths = strengths[:3]
    areas_to_improve = areas_to_improve[:3]
    
    # Build summary in exact format from example
    role_display = session.role.title() if session.role else "N/A"
    persona_display = session.persona.title() if session.persona else "N/A"
    
    summary = (
        f"✅ Interview complete – here's your detailed report\n\n"
        f"Role: {role_display}\n\n"
        f"Interviewer style: {persona_display}\n\n"
        f"Questions answered: {n}\n\n"
        f"Average scores this session\n\n"
        f"Clarity: {avg_clarity} / 5\n"
        f"Specificity: {avg_specificity} / 5\n"
        f"Confidence: {avg_confidence} / 5\n"
        f"Overall: {avg_overall} / 5\n\n"
    )
    
    # Add detailed per-question feedback (since we don't show it during interview)
    summary += "📋 Detailed Question-by-Question Feedback\n\n"
    for i, eval_data in enumerate(evals, 1):
        question = eval_data.get("question", "N/A")
        answer = eval_data.get("answer", "N/A")
        clarity = eval_data.get("clarity", 0)
        specificity = eval_data.get("specificity", 0)
        confidence = eval_data.get("confidence", 0)
        overall = eval_data.get("overall_score", 0)
        feedback = eval_data.get("feedback", "No feedback available.")
        improved = eval_data.get("improved_answer", "No improved answer available.")
        
        summary += f"Question {i}: {question}\n\n"
        summary += f'Your answer: "{answer}"\n\n'
        summary += f"Scores: Clarity {clarity}/5, Specificity {specificity}/5, Confidence {confidence}/5, Overall {overall}/5\n\n"
        summary += f"Feedback: {feedback}\n\n"
        summary += f"Improved example answer:\n{improved}\n\n"
        summary += "---\n\n"
    
    if strengths:
        summary += "💪 Strengths\n\n"
        for strength in strengths:
            summary += f"{strength}\n"
        summary += "\n"
    
    if areas_to_improve:
        summary += "🎯 Key areas to improve\n\n"
        for area in areas_to_improve:
            summary += f"{area}\n"
        summary += "\n"
    
    # Next steps
    summary += "📝 Next steps\n\n"
    next_steps = []
    
    if avg_specificity < 3.0:
        next_steps.append("Practise giving 1–2 quantified examples for each answer.")
    
    if avg_specificity < 3.0 or avg_clarity < 3.0:
        next_steps.append("Focus especially on making your answers more specific and measurable.")
    
    # Role-specific next steps
    if session.role == "Junior Data Analyst" and avg_specificity < 3.0:
        next_steps.append("Review common data-cleaning steps for junior analyst interviews.")
    
    # Ensure at least one next step
    if len(next_steps) == 0:
        next_steps.append("Review your feedback and practice the improved answer examples.")
    
    for step in next_steps:
        summary += f"{step}\n"
    
    summary += "\nType 'restart' to try another interview with a different interviewer style."
    
    return summary


# -------------------------------------------------------
# Agent + Protocol Setup
# -------------------------------------------------------

agent = Agent()
chat_proto = Protocol(spec=chat_protocol_spec)
eval_client_proto = Protocol(name="interview-eval-client", version="1.0")

# Your evaluator's address:
# IMPORTANT: Make sure the evaluator agent is running and update this address with the actual evaluator agent address
# You can find the evaluator address when you start evaluator.py - it will be printed in the logs
EVALUATOR_AGENT_ADDRESS = "agent1qtd83x6878sacthkcvzsdtak4v2a67l9d6v56tpysmvf4dgze0t3wmknm2h"


def make_text_message(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )


# -------------------------------------------------------
# Helper to send evaluation requests
# -------------------------------------------------------

async def send_evaluation_request(
    ctx: Context,
    user_address: str,
    question: str,
    answer: str,
    persona: Optional[str],
    session_key: str,
    role: Optional[str],
):
    if not EVALUATOR_AGENT_ADDRESS.startswith("agent1"):
        ctx.logger.warning("EVALUATOR_AGENT_ADDRESS not set correctly.")
        return

    try:
        # Store mapping from user_address to session_key so we can retrieve it in response handler
        ctx.storage.set(f"eval_session:{user_address}", session_key)
        ctx.logger.info(f"Stored session mapping: {user_address} -> {session_key}")

        req = EvaluationRequest(
            question=question,
            answer=answer,
            persona=persona,
            role=role,
            user_address=user_address,
        )

        ctx.logger.info(f"Sending EvaluationRequest to evaluator: {req}")
        await ctx.send(EVALUATOR_AGENT_ADDRESS, req)
    except Exception as e:
        ctx.logger.error(f"Failed to send evaluation request to evaluator at {EVALUATOR_AGENT_ADDRESS}: {e}")
        ctx.logger.warning("Make sure the evaluator agent is running. Start it with: python evaluator.py")
        # Note: The error will be logged but the interview will wait for the evaluator
        # The user will see "Evaluating your response..." but won't get feedback until evaluator is available
        raise  # Re-raise to let the caller know the evaluation failed


# -------------------------------------------------------
# ChatMessage Handler
# -------------------------------------------------------

@chat_proto.on_message(ChatMessage)
async def on_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got ChatMessage from {sender}: {msg}")

    try:
        # Always ACK
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id,
            ),
        )

        session_key = get_session_key(sender, msg)
        session = load_session(ctx, session_key)

        # Split incoming content types
        text_items = [i for i in msg.content if isinstance(i, TextContent)]
        start_items = [i for i in msg.content if isinstance(i, StartSessionContent)]
        end_items = [i for i in msg.content if isinstance(i, EndSessionContent)]

        # If persona already selected, ignore StartSession noise
        if session.persona is not None:
            start_items = []

        # 1) Handle TextContent FIRST
        if text_items:
            user_text = text_items[0].text.strip().lower()
            ctx.logger.info(f"User text from {sender}: {user_text}")

        # Commands that work regardless of session state
        if user_text == "help":
            await ctx.send(
                sender,
                make_text_message(
                    "You can answer questions normally, or use:\n"
                    "– 'restart' to start again\n"
                    "– 'stop' to end the interview\n"
                    "– 'help' to see this message again."
                ),
            )
            return

        if user_text == "stop":
            session.finished = True
            save_session(ctx, session_key, session)
            
            if session.evaluations and len(session.evaluations) > 0:
                summary = generate_end_of_interview_summary(session)
                if summary:
                    await ctx.send(sender, make_text_message(summary))
            else:
                await ctx.send(
                    sender,
                    make_text_message("Interview stopped. Type 'restart' to start a new one.")
                )
            return

        # Restart command - resets session and history
        if user_text == "restart":
            # Reset session state
            session = SessionState(role=None, persona=None, question_index=0, finished=False, answers=[], evaluations=[], questions=[], conversation_history=[])
            save_session(ctx, session_key, session)
            
            # Reset user history for this user
            reset_user_history(sender)
            
            await ctx.send(
                sender,
                make_text_message(
                    "Interview restarted.\n\n"
                    "Hi, I'm your AI interview coach.\n\n"
                    "We'll run a short mock interview for a Junior Data Analyst role and then give you detailed feedback on each answer.\n\n"
                    "Choose an interviewer avatar:\n\n"
                    "HR\n"
                    "Junior Developer\n"
                    "Senior Developer\n"
                    "Corporate Executive\n\n"
                    "Type your choice, or help for commands."
                ),
            )
            return

        # Role not chosen yet -> automatically set to Junior Data Analyst
        if session.role is None:
            # Automatically set role to Junior Data Analyst
            session.role = "Junior Data Analyst"
            session.persona = None
            session.question_index = 0
            session.finished = False
            session.answers = []
            session.evaluations = []
            session.questions = []
            session.conversation_history = []

            # Initialize and log role selection
            log_role_selection(sender, "Junior Data Analyst")

            save_session(ctx, session_key, session)

        # Persona not chosen yet -> treat as persona selection
        if session.persona is None:
            persona_choice = normalize_persona_name(user_text)
            if persona_choice is None:
                # If it's a greeting or not a valid persona, send welcome message
                greeting_words = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
                # Check if the message contains a greeting (handles cases like "@Interviewer hello")
                is_greeting = any(greeting in user_text for greeting in greeting_words)
                
                if is_greeting:
                    await ctx.send(
                        sender,
                        make_text_message(
                            "Hi! I'm your AI interview coach.\n\n"
                            "We'll run a short mock interview for a Junior Data Analyst role and then give you detailed feedback on each answer.\n\n"
                            "Choose an interviewer avatar:\n\n"
                            "HR\n"
                            "Junior Developer\n"
                            "Senior Developer\n"
                            "Corporate Executive\n\n"
                            "Type your choice, or 'help' for commands."
                        ),
                    )
                else:
                    await ctx.send(
                        sender,
                        make_text_message(
                            "Hi! I'm your AI interview coach.\n\n"
                            "Please choose an interviewer avatar to begin:\n\n"
                            "HR\n"
                            "Junior Developer\n"
                            "Senior Developer\n"
                            "Corporate Executive\n\n"
                            "Or type 'restart' to start over, or 'help' for commands."
                        ),
                    )
                return

            # Select persona
            session.persona = persona_choice
            session.question_index = 0
            session.finished = False
            session.answers = []
            session.evaluations = []
            session.questions = []
            session.conversation_history = []

            # Log persona selection
            log_persona_selection(sender, persona_choice)

            save_session(ctx, session_key, session)

            # Persona-specific introduction messages
            persona_intros = {
                "HR": (
                    f"You selected HR.\n\n"
                    f"I'll focus on culture fit, communication, and basic role alignment. I'll assess your soft skills, teamwork, and professionalism.\n\n"
                    f"We'll do {QUESTIONS_PER_SESSION} questions and then I'll give you a summary of your performance.\n\n"
                    f"Let's begin..."
                ),
                "Junior Developer": (
                    f"You selected the Junior Developer interviewer.\n\n"
                    f"I'm relatively early in my career too, so I understand the practical realities of junior work. I'll test your basic technical understanding and see how you collaborate and explain ideas.\n\n"
                    f"We'll do {QUESTIONS_PER_SESSION} questions and then I'll give you a summary of your performance.\n\n"
                    f"Let's begin..."
                ),
                "Senior Developer": (
                    f"You selected the Senior Developer / Tech Lead interviewer.\n\n"
                    f"I'm deeply technical and responsible for system quality. I'll assess your technical knowledge depth, design thinking, and how you handle trade-offs and edge cases.\n\n"
                    f"We'll do {QUESTIONS_PER_SESSION} questions and then I'll give you a summary of your performance.\n\n"
                    f"Let's begin..."
                ),
                "Corporate Executive": (
                    f"You selected the Corporate Executive interviewer.\n\n"
                    f"I care about the big picture: business impact, risk, and long-term value. I'll gauge your leadership potential, judgement, and how you contribute to business goals.\n\n"
                    f"We'll do {QUESTIONS_PER_SESSION} questions and then I'll give you a summary of your performance.\n\n"
                    f"Let's begin..."
                ),
            }
            
            intro_message = persona_intros.get(persona_choice, f"You selected the {persona_choice} interviewer. Let's begin your mock interview.")
            await ctx.send(sender, make_text_message(intro_message))

            # Generate the first, broad opening question
            first_question = await generate_first_question_with_asi(
                role=session.role,
                persona=persona_choice
            )
            
            # Store the first question
            if session.questions is None:
                session.questions = []
            session.questions.append(first_question)
            save_session(ctx, session_key, session)
            
            # Send the first question
            await ctx.send(sender, make_text_message(first_question))
            return

        # Persona already chosen → treat text as an answer
        if session.finished:
            await ctx.send(
                sender,
                make_text_message(
                    "This interview session is finished.\n"
                    "Type 'restart' to begin a new interview."
                ),
            )
            return

        # Save answer
        if session.answers is None:
            session.answers = []
        session.answers.append(user_text)

        # Get the current question that was just answered
        if session.questions and len(session.questions) > 0 and session.question_index < len(session.questions):
            current_q = session.questions[session.question_index]
        else:
            # Fallback if we don't have the question stored
            current_q = "Tell me about yourself."
        
        # Store Q&A pair in conversation history for adaptive question generation
        if session.conversation_history is None:
            session.conversation_history = []
        session.conversation_history.append({
            "question": current_q,
            "answer": user_text
        })

        # Save session before sending evaluation (so we can track which question was answered)
        save_session(ctx, session_key, session)

        # Send evaluation to evaluator agent (silently, in background)
        # The evaluation will be stored when it comes back, but we don't wait for it
        try:
            await send_evaluation_request(
                ctx,
                user_address=sender,
                question=current_q,
                answer=user_text,
                persona=session.persona,
                session_key=session_key,
                role=session.role,
            )
        except Exception as e:
            ctx.logger.warning(f"Evaluation request failed (will continue interview): {e}")

        # Move to next question immediately (natural interview flow)
        session.question_index += 1

        # Check if we've completed all questions
        if session.question_index >= QUESTIONS_PER_SESSION:
            # Interview is complete - mark as finished
            session.finished = True
            save_session(ctx, session_key, session)
            
            # Don't send summary yet - wait for evaluation to come back
            # The evaluation handler will send the final report when it receives the last evaluation
            # For now, just acknowledge completion
            await ctx.send(
                sender,
                make_text_message(
                    "Thanks for completing the interview! Generating your final report..."
                )
            )
        else:
            # Generate the next adaptive question based on conversation history
            next_question_number = session.question_index + 1
            
            # Get conversation history for adaptive generation
            conversation_history = session.conversation_history or []
            
            # Generate next question adaptively based on previous answers
            next_q = await generate_next_adaptive_question(
                role=session.role,
                persona=session.persona,
                conversation_history=conversation_history,
                question_number=next_question_number
            )
            
            # Store the new question
            if session.questions is None:
                session.questions = []
            session.questions.append(next_q)
            
            save_session(ctx, session_key, session)
            
            # Send the next question immediately (natural flow)
            await ctx.send(sender, make_text_message(next_q))
        
        return

        # 2) If no TextContent, handle StartSession
        if start_items:
            if session.role is None and session.persona is None and not session.answers and not session.finished:
                session = SessionState(role=None, persona=None, question_index=0, finished=False, answers=[], evaluations=[], questions=[], conversation_history=[])
                save_session(ctx, session_key, session)
                # Initialize user history for new session
                reset_user_history(sender)
                await ctx.send(
                    sender,
                    make_text_message(
                        "Hi, I'm your AI interview coach.\n\n"
                        "We'll run a short mock interview for a Junior Data Analyst role and then give you detailed feedback on each answer.\n\n"
                        "Choose an interviewer avatar:\n\n"
                        "HR\n"
                        "Junior Developer\n"
                        "Senior Developer\n"
                        "Corporate Executive\n\n"
                        "Type your choice, or help for commands."
                    ),
                )
            else:
                ctx.logger.info(
                    f"Ignoring StartSessionContent for {sender} (already mid-session)."
                )

        # 3) Handle EndSession (optional)
        for _ in end_items:
            ctx.logger.info(f"Chat session ended with {sender}")
    
    except Exception as e:
        ctx.logger.error(f"Error handling chat message from {sender}: {e}", exc_info=True)
        # Try to send an error message to the user
        try:
            await ctx.send(
                sender,
                make_text_message(
                    "Sorry, I encountered an error processing your message. Please try again or type 'restart' to start over."
                ),
            )
        except:
            pass  # If we can't send error message, at least log it


# -------------------------------------------------------
# Acknowledgement Handler
# -------------------------------------------------------

@chat_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Received acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )


# -------------------------------------------------------
# EvaluationResponse Handler (from evaluator agent)
# -------------------------------------------------------

@eval_client_proto.on_message(EvaluationResponse)
async def on_evaluation_response(ctx: Context, sender: str, msg: EvaluationResponse):
    """
    Handle evaluation results coming back from the Evaluator Agent.
    Store evaluation silently - no feedback shown to user during interview.
    sender = evaluator agent address.
    msg.user_address = the original user who answered.
    """
    ctx.logger.info(f"Got EvaluationResponse from {sender}: {msg}")

    # Retrieve session key from storage
    session_key = ctx.storage.get(f"eval_session:{msg.user_address}")
    if not session_key:
        ctx.logger.warning(f"Could not find session key for user {msg.user_address}")
        # Fallback: try to construct session key
        session_key = f"session:sender:{msg.user_address}"

    # Load the session
    session = load_session(ctx, session_key)

    # Store evaluation data silently (no user feedback during interview)
    if session.evaluations is None:
        session.evaluations = []
    
    evaluation_data = {
        "question": msg.question,
        "answer": msg.answer,
        "clarity": msg.clarity,
        "specificity": msg.specificity,
        "confidence": msg.confidence,
        "overall_score": msg.overall_score,
        "feedback": msg.feedback,
        "improved_answer": msg.improved_answer,
    }
    session.evaluations.append(evaluation_data)
    
    # Log complete Q&A with evaluation to user history
    log_question_answer_evaluation(
        user_address=msg.user_address,
        question=msg.question,
        answer=msg.answer,
        clarity=msg.clarity,
        specificity=msg.specificity,
        confidence=msg.confidence,
        overall_score=msg.overall_score
    )
    
    # Save session with updated evaluations
    save_session(ctx, session_key, session)
    
    # If interview is finished, check if we should send the final report
    if session.finished:
        # Send report if we have evaluations (even if not all are complete, in case some failed)
        if session.evaluations and len(session.evaluations) > 0:
            # Check if this is likely the last evaluation (we have as many as questions answered)
            # or if we've been waiting and have at least some evaluations
            num_answers = len(session.answers) if session.answers else 0
            if len(session.evaluations) >= num_answers or len(session.evaluations) >= QUESTIONS_PER_SESSION:
                summary = generate_end_of_interview_summary(session)
                await ctx.send(msg.user_address, make_text_message(summary))
    
    # Note: We don't send any feedback to the user here - evaluations are stored silently
    # The interview flow continues naturally with questions, and all feedback is in the final report


agent.include(chat_proto, publish_manifest=True)
agent.include(eval_client_proto)

if __name__ == "__main__":
    agent.run()
