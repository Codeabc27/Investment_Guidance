import json

from app.services.gemini_service import gemini_service


def _fallback(state, reason):
    return {
        "status": "complete",
        "strategy": state.get("candidate_portfolio", {}),
        "scenarios": state.get("scenarios", {}),
        "explanation": {
            "summary": "The strategy and projections were calculated successfully. Gemini was unavailable for the explanatory summary.",
            "why_this_strategy": "The allocation follows the selected risk category and the projections use deterministic Python calculations.",
            "key_risks": ["Market volatility", "Inflation", "Actual returns may differ from assumptions"],
            "assumptions": ["Scenario returns are illustrative assumptions, not guarantees."],
            "data_freshness": "Current market research was unavailable for this run.",
        },
        "market_context": state.get("market_data", {}),
        "warning": reason,
        "disclaimer": "Educational decision support only. Not a guarantee or regulated financial advice.",
    }


def run(state):
    validation = state.get("validation_result", {})
    if validation.get("status") != "PASS":
        return {
            "final_response": {
                "status": "incomplete",
                "message": "Please correct the missing inputs.",
                "issues": validation.get("issues", []),
            }
        }

    goal = state.get("goal", {})
    profile = state.get("financial_profile", {})
    risk = state.get("risk_profile", {})
    portfolio = state.get("candidate_portfolio", {})
    scenarios = state.get("scenarios", {})
    market_request = state.get("market_data", {})

    prompt = f"""
You are the final explanation agent for a small student investment decision-support app.
Use the supplied facts and do ONE concise current-web research pass when useful.

Goal: {goal}
Financial context: {profile}
Risk profile: {risk}
Portfolio: {portfolio}
Python scenarios: {scenarios}
Market research request: {market_request}

Return ONLY JSON with this exact shape:
{{
  "summary": "2 short sentences",
  "why_this_strategy": "2-3 short reasons",
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "assumptions": ["assumption 1", "assumption 2"],
  "data_freshness": "brief statement about the research",
  "market_context": "brief current market context"
}}

Rules:
- Do not change Python scenario values.
- Do not invent prices or facts.
- Do not promise returns.
- Use educational language.
- Keep the response concise.
"""

    try:
        # One lightweight grounded call for the complete analysis explanation.
        raw = gemini_service.research(
            prompt,
            system_instruction=(
                "You are a concise financial education assistant. "
                "Explain uncertainty and never guarantee outcomes."
            ),
            max_output_tokens=900,
        )
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "", 1).replace("```", "", 1).strip()
        explanation = json.loads(cleaned)
        if not isinstance(explanation, dict):
            raise ValueError("Gemini did not return a JSON object")
        return {
            "final_response": {
                "status": "complete",
                "strategy": portfolio,
                "scenarios": scenarios,
                "explanation": explanation,
                "market_context": explanation.get("market_context", ""),
                "disclaimer": "Educational decision support only. Not a guarantee or regulated financial advice.",
            }
        }
    except Exception as exc:
        return {"final_response": _fallback(state, str(exc))}
