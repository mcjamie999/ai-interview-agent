from typing import Optional
import requests
import json
import re

from uagents import Agent, Context, Model, Protocol

# -------------------------------
# Message models for evaluation
# -------------------------------

class EvaluationRequest(Model):
    question: str
    answer: str
    persona: Optional[str] = None
    role: Optional[str] = None
    user_address: str  # address of the original chat user


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


# -------------------------------
# Protocol + agent setup
# -------------------------------

eval_proto = Protocol(name="interview-evaluation", version="1.0")
agent = Agent()  # Hosted on Agentverse


# -------------------------------
# ASI Cloud Configuration
# -------------------------------

# ASI Cloud API Configuration
# TODO: Move API key to environment variable for security
# import os
# ASI_API_KEY = os.getenv("ASI_API_KEY", "your-key-here")
ASI_API_KEY = "sk-FVoN14UREfvuUPIZugEWKiJGuxMROZ18Ahz4MT6L8TE"
ASI_API_URL = "https://inference.asicloud.cudos.org/v1/chat/completions"
ASI_MODEL = "asi1-mini"


# -------------------------------
# ASI Cloud evaluator
# -------------------------------

def evaluate_with_asi(req: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate interview answer using ASI Cloud API.
    Returns structured evaluation with scores and feedback.
    """
    # Build the evaluation prompt
    role_context = f" for a {req.role} position" if req.role else ""
    persona_context = f" The interviewer style is {req.persona}." if req.persona else ""
    
    prompt = f"""You are an expert interview coach evaluating a candidate's answer to an interview question.

Context:
- Role: {req.role or 'General'}
- Interviewer style: {req.persona or 'Standard'}

Question: {req.question}

Candidate's answer: {req.answer}

Evaluate this answer on three dimensions (score each 1-5):
1. Clarity: How clear, well-structured, and easy to understand is the answer?
2. Specificity: How many concrete examples, numbers, metrics, tools, or specific details are included?
3. Confidence: How confident, assertive, and decisive does the candidate sound?

Provide your evaluation in this exact JSON format:
{{
    "clarity": <integer 1-5>,
    "specificity": <integer 1-5>,
    "confidence": <integer 1-5>,
    "feedback": "<2-3 sentences of constructive feedback focusing on what to improve>",
    "improved_answer": "<A complete improved version of the answer with specific examples, numbers, and concrete details>"
}}

Be direct and honest in your evaluation. If the answer is generic or lacks specifics, point that out clearly."""

    try:
        # Call ASI Cloud API
        payload = {
            "model": ASI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,  # Lower temperature for more consistent evaluation
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
        # Try to extract JSON from the response (it might have markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', ai_response)
        if json_match:
            json_str = json_match.group(0)
            eval_data = json.loads(json_str)
        else:
            # Fallback: try to parse the whole response as JSON
            eval_data = json.loads(ai_response)
        
        # Extract scores and feedback
        clarity = int(eval_data.get("clarity", 3))
        specificity = int(eval_data.get("specificity", 2))
        confidence = int(eval_data.get("confidence", 3))
        feedback = eval_data.get("feedback", "No specific feedback provided.")
        improved_answer = eval_data.get("improved_answer", req.answer)
        
        # Clamp scores to valid range
        clarity = max(1, min(5, clarity))
        specificity = max(1, min(5, specificity))
        confidence = max(1, min(5, confidence))
        
        # Calculate overall score
        overall = round((clarity + specificity + confidence) / 3.0, 2)
        
    except requests.exceptions.RequestException as e:
        # API call failed - fallback to basic evaluation
        print(f"ASI API error: {e}")
        clarity = 3
        specificity = 2
        confidence = 3
        overall = round((clarity + specificity + confidence) / 3.0, 2)
        feedback = "Unable to get detailed evaluation. Please ensure your answer includes specific examples and concrete details."
        improved_answer = f"{req.answer}\n\n(Add specific examples with numbers, tools, and measurable outcomes to improve this answer.)"
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # JSON parsing failed - fallback to basic evaluation
        print(f"Error parsing ASI response: {e}")
        print(f"Raw response: {ai_response if 'ai_response' in locals() else 'No response'}")
        clarity = 3
        specificity = 2
        confidence = 3
        overall = round((clarity + specificity + confidence) / 3.0, 2)
        feedback = "Evaluation completed. Focus on adding specific examples and concrete details to your answers."
        improved_answer = f"{req.answer}\n\n(Add specific examples with numbers, tools, and measurable outcomes to improve this answer.)"
    
    return EvaluationResponse(
        question=req.question,
        answer=req.answer,
        persona=req.persona,
        role=req.role,
        user_address=req.user_address,
        clarity=clarity,
        specificity=specificity,
        confidence=confidence,
        overall_score=overall,
        feedback=feedback,
        improved_answer=improved_answer,
    )


# -------------------------------
# Protocol handler
# -------------------------------

@eval_proto.on_message(EvaluationRequest)
async def handle_evaluation(ctx: Context, sender: str, msg: EvaluationRequest):
    ctx.logger.info(f"Received EvaluationRequest from {sender}: {msg}")

    result = evaluate_with_asi(msg)

    ctx.logger.info(
        f"Sending EvaluationResponse to {sender}: "
        f"overall={result.overall_score}, clarity={result.clarity}, "
        f"specificity={result.specificity}, confidence={result.confidence}"
    )

    await ctx.send(sender, result)


@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info("Evaluator agent started and ready to receive EvaluationRequest")


agent.include(eval_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
