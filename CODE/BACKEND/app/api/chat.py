import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_db
from app.schemas.analysis import ChatRequest
from app.services.security import get_current_user
from app.services.gemini_service import gemini_service


router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


def _safe_json(value: Any) -> dict:
    """Convert database JSON text into a dictionary safely."""
    if not value:
        return {}

    if isinstance(value, dict):
        return value

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _number(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _money(value: Any) -> str:
    amount = _number(value)
    return f"₹{amount:,.0f}"


def _extract_risks(analysis: dict) -> str | None:
    """Find risk information from different analysis response structures."""

    final_response = _safe_json(analysis.get("final_response"))
    explanation = _safe_json(
        final_response.get("explanation") or analysis.get("explanation")
    )

    risks = (
        final_response.get("key_risks")
        or final_response.get("risks")
        or explanation.get("key_risks")
        or explanation.get("risks")
    )

    if isinstance(risks, list):
        return " ".join(str(item) for item in risks)

    if risks:
        return str(risks)

    return None


def _extract_assumptions(analysis: dict) -> str | None:
    """Find assumption information from the latest analysis."""

    final_response = _safe_json(analysis.get("final_response"))
    explanation = _safe_json(
        final_response.get("explanation") or analysis.get("explanation")
    )

    assumptions = final_response.get("assumptions") or explanation.get("assumptions")

    if isinstance(assumptions, list):
        return " ".join(str(item) for item in assumptions)

    if assumptions:
        return str(assumptions)

    return None


def _extract_strategy(analysis: dict) -> dict:
    """Find the recommended portfolio from the latest analysis."""

    final_response = _safe_json(analysis.get("final_response"))

    portfolio = (
        final_response.get("candidate_portfolio")
        or final_response.get("portfolio")
        or final_response.get("strategy")
    )

    return portfolio if isinstance(portfolio, dict) else {}


def _extract_summary(analysis: dict) -> str | None:
    final_response = _safe_json(analysis.get("final_response"))
    explanation = _safe_json(
        final_response.get("explanation") or analysis.get("explanation")
    )

    summary = (
        final_response.get("summary")
        or final_response.get("recommendation")
        or explanation.get("summary")
    )

    if summary:
        return str(summary)

    return None


def _local_chat_answer(
    message: str,
    goal: dict,
    profile: dict,
    analysis: dict,
) -> str | None:
    """
    Answer common questions directly from existing application data.

    This avoids unnecessary Gemini calls and makes the chat responsive
    even when Gemini is temporarily unavailable.
    """

    text = message.lower().strip()

    # ---------------------------------------------------------
    # Greetings
    # ---------------------------------------------------------
    greetings = {
        "hi",
        "hello",
        "hey",
        "hai",
        "good morning",
        "good afternoon",
        "good evening",
    }

    if text in greetings or len(text) <= 2:
        return (
            "Hello. I'm InvestWise AI. I can help you understand your "
            "investment goal, recommended allocation, major risks, "
            "assumptions, and ways to reach your goal faster."
        )

    # ---------------------------------------------------------
    # Major risks
    # ---------------------------------------------------------
    if (
        "major risk" in text
        or "main risk" in text
        or "key risk" in text
        or "risks" in text
        or "risk involved" in text
        or "risk are" in text
    ):
        risks = _extract_risks(analysis)

        if risks:
            return (
                f"The major risks identified in your current plan are: "
                f"{risks} "
                "These are educational considerations, not guarantees of "
                "future performance."
            )

        return (
            "The main risks to consider are market volatility, inflation, "
            "changes in expected returns, and the possibility that actual "
            "investment performance may differ from assumptions."
        )

    # ---------------------------------------------------------
    # Assumptions
    # ---------------------------------------------------------
    if (
        "assumption" in text
        or "assumptions" in text
        or "what did you assume" in text
        or "what was assumed" in text
    ):
        assumptions = _extract_assumptions(analysis)

        if assumptions:
            return (
                f"The current analysis uses these assumptions: "
                f"{assumptions} "
                "These values are illustrative and are not guaranteed returns."
            )

        return (
            "The analysis uses assumptions about expected returns, investment "
            "duration, contribution amount, and market conditions. Actual "
            "results can differ significantly."
        )

    # ---------------------------------------------------------
    # Current strategy / recommendation
    # ---------------------------------------------------------
    if (
        "why was this strategy" in text
        or "why this strategy" in text
        or "why recommended" in text
        or "recommendation" in text
        or "recommended strategy" in text
        or "recommended plan" in text
    ):
        summary = _extract_summary(analysis)

        if summary:
            return f"The current recommendation is based on your stated goal, financial profile, and risk considerations. {summary}"

        return (
            "The strategy is designed around your investment goal, time "
            "horizon, financial profile, and risk level. The allocation is "
            "intended as educational guidance rather than a guaranteed outcome."
        )

    # ---------------------------------------------------------
    # Goal faster
    # ---------------------------------------------------------
    if (
        "reach my goal faster" in text
        or "achieve my goal faster" in text
        or "reach goal faster" in text
        or "achieve goal faster" in text
        or "faster" in text
    ):
        monthly = _number(
            goal.get("monthly_contribution")
            or goal.get("monthly_investment")
            or goal.get("monthly_amount")
        )

        target = _number(
            goal.get("target_amount") or goal.get("target") or goal.get("goal_amount")
        )

        if monthly > 0:
            return (
                f"To reach your goal faster, consider increasing your regular "
                f"contribution from {_money(monthly)} when your budget allows. "
                "You can also review your investment horizon and risk level, "
                "but higher expected returns generally come with higher risk. "
                "Avoid increasing risk only to reach the goal faster."
            )

        if target > 0:
            return (
                f"Your current target is approximately {_money(target)}. "
                "A higher regular contribution, a longer investment horizon, "
                "or reviewing the investment strategy may help, but higher "
                "returns are not guaranteed."
            )

        return (
            "The safest way to accelerate a financial goal is usually to "
            "increase regular contributions when affordable and review the "
            "time horizon. Taking additional investment risk does not "
            "guarantee faster results."
        )

    # ---------------------------------------------------------
    # Goal amount
    # ---------------------------------------------------------
    if (
        "goal amount" in text
        or "target amount" in text
        or "my target" in text
        or "my goal" in text
    ):
        target = _number(
            goal.get("target_amount") or goal.get("target") or goal.get("goal_amount")
        )

        if target > 0:
            return (
                f"Your current investment goal target is {_money(target)}. "
                "The recommendation is designed around this target and the "
                "other information provided in your profile."
            )

    # ---------------------------------------------------------
    # Monthly investment / SIP
    # ---------------------------------------------------------
    if (
        "monthly investment" in text
        or "monthly contribution" in text
        or "sip" in text
        or "invest every month" in text
    ):
        monthly = _number(
            goal.get("monthly_contribution")
            or goal.get("monthly_investment")
            or goal.get("monthly_amount")
        )

        if monthly > 0:
            return (
                f"Your current planned monthly contribution is "
                f"{_money(monthly)}. Increasing this amount, if financially "
                "comfortable, can help improve the probability of reaching "
                "your goal earlier."
            )

        return (
            "Your monthly contribution is part of the goal calculation. "
            "A consistent contribution is important for long-term planning."
        )

    # ---------------------------------------------------------
    # Portfolio / allocation
    # ---------------------------------------------------------
    if (
        "allocation" in text
        or "portfolio" in text
        or "where should i invest" in text
        or "where am i investing" in text
    ):
        strategy = _extract_strategy(analysis)

        allocation = (
            strategy.get("allocation")
            or strategy.get("asset_allocation")
            or strategy.get("allocations")
        )

        if isinstance(allocation, dict) and allocation:
            parts = []

            for name, value in allocation.items():
                number_value = _number(value)

                if number_value > 0:
                    parts.append(f"{name}: {number_value:.0f}%")

            if parts:
                return (
                    "Your current recommended allocation is: "
                    + ", ".join(parts)
                    + ". This allocation is educational and should be "
                    "reviewed as your financial situation changes."
                )

        return (
            "The recommended portfolio is based on your goal, time horizon, "
            "and risk profile. Open the Recommendation page to see the "
            "current allocation."
        )

    # ---------------------------------------------------------
    # If the question is not a simple known question,
    # return None so Gemini can handle it.
    # ---------------------------------------------------------
    return None


@router.post("")
def chat(req: ChatRequest, user_id=Depends(get_current_user)):

    # ---------------------------------------------------------
    # Load user's goal/profile/latest analysis
    # ---------------------------------------------------------
    with get_db() as db:
        goal = db.execute(
            "SELECT * FROM goals WHERE id=? AND user_id=?",
            (req.goal_id, user_id),
        ).fetchone()

        profile = db.execute(
            "SELECT * FROM user_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()

        analysis = db.execute(
            """
            SELECT final_response
            FROM analyses
            WHERE goal_id=? AND user_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (req.goal_id, user_id),
        ).fetchone()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal_data = dict(goal)
    profile_data = dict(profile) if profile else {}

    final_response = {}

    if analysis and analysis["final_response"]:
        try:
            final_response = json.loads(analysis["final_response"])

            if not isinstance(final_response, dict):
                final_response = {}

        except json.JSONDecodeError:
            final_response = {"raw": analysis["final_response"]}

    analysis_data = {"final_response": final_response}

    # ---------------------------------------------------------
    # FIRST: Try local answer.
    #
    # This means simple questions do NOT call Gemini.
    # ---------------------------------------------------------
    local_answer = _local_chat_answer(
        req.message,
        goal_data,
        profile_data,
        analysis_data,
    )

    if local_answer:
        return {
            "message": local_answer,
            "goal_id": req.goal_id,
            "provider": "InvestWise AI",
        }

    # ---------------------------------------------------------
    # Gemini only for questions that actually need AI.
    # ---------------------------------------------------------
    prompt = f"""
You are the AI assistant for a student investment-planning application.

Answer the user's question briefly using only the supplied context.

Goal:
{goal_data}

Financial profile:
{profile_data}

Latest investment analysis:
{final_response}

User question:
{req.message}

Rules:
- Educational guidance only.
- Do not guarantee returns.
- Do not invent current prices or current market facts.
- Do not claim to execute trades.
- Do not provide personalized financial advice as a guaranteed result.
- If the user asks for current market information, explain that current
  information should be verified using current market research.
- Keep the answer below 120 words.
"""

    try:
        answer = gemini_service.generate(
            prompt,
            system_instruction=(
                "You are InvestWise AI, a concise and cautious educational "
                "investment assistant. Never guarantee investment outcomes."
            ),
            temperature=0.2,
            max_output_tokens=220,
        )

        if answer:
            return {
                "message": answer,
                "goal_id": req.goal_id,
                "provider": "Gemini",
            }

    except Exception:
        # Do NOT expose the Gemini error to the user.
        # Return a useful fallback instead.
        pass

    # ---------------------------------------------------------
    # Gemini unavailable fallback
    # ---------------------------------------------------------
    return {
        "message": (
            "I can still help with your current investment plan. "
            "Gemini is temporarily unavailable, but you can ask me about "
            "your major risks, assumptions, recommended allocation, goal "
            "amount, monthly contribution, or ways to reach your goal faster."
        ),
        "goal_id": req.goal_id,
        "provider": "InvestWise AI",
    }
