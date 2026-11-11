import json

from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_db
from app.services.security import get_current_user
from app.workflow.graph import investment_graph
from app.workflow.state import InvestmentState

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/{goal_id}")
def analyze(goal_id: int, user_id=Depends(get_current_user)):
    with get_db() as db:
        goal = db.execute(
            "SELECT * FROM goals WHERE id=? AND user_id=?",
            (goal_id, user_id),
        ).fetchone()
        profile = db.execute(
            "SELECT * FROM user_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()
        risk = db.execute(
            "SELECT score, category, answers_json FROM risk_profiles WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    if not goal:
        raise HTTPException(404, "Goal not found")

    try:
        risk_answers = json.loads(risk["answers_json"]) if risk and risk["answers_json"] else {}
    except json.JSONDecodeError:
        risk_answers = {}

    state: InvestmentState = {
        "user_id": user_id,
        "goal": dict(goal),
        "financial_profile": dict(profile) if profile else {},
        "risk_answers": risk_answers,
        "risk_category": risk["category"].title() if risk and risk["category"] else None,
        "market_symbol": "NIFTY 50",
    }

    try:
        result = investment_graph.invoke(state)
    except Exception as exc:
        raise HTTPException(503, f"Analysis workflow failed: {exc}") from exc

    final_response = result.get("final_response", {})
    validation = result.get("validation_result", {})
    status = "completed" if final_response.get("status") == "complete" else "incomplete"

    with get_db() as db:
        cur = db.execute(
            """INSERT INTO analyses(user_id,goal_id,status,final_response,validation_status,completed_at)
               VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)""",
            (user_id, goal_id, status, json.dumps(final_response), validation.get("status")),
        )
        analysis_id = cur.lastrowid

        portfolio = result.get("candidate_portfolio", {})
        if portfolio:
            db.execute(
                """INSERT INTO portfolios(analysis_id,strategy_name,allocation_json,expected_return,risk_level)
                   VALUES(?,?,?,?,?)""",
                (
                    analysis_id,
                    portfolio.get("strategy_name"),
                    json.dumps(portfolio.get("allocation", {})),
                    None,
                    portfolio.get("risk_level"),
                ),
            )

        for name, scenario in result.get("scenarios", {}).items():
            db.execute(
                """INSERT INTO scenarios(analysis_id,scenario_name,projected_value,assumed_return,assumptions_json)
                   VALUES(?,?,?,?,?)""",
                (
                    analysis_id,
                    name,
                    scenario.get("projected_value"),
                    scenario.get("annual_return"),
                    json.dumps({"source": "Python deterministic calculation"}),
                ),
            )

        for agent_name, output in [
            ("goal_agent", result.get("goal_analysis")),
            ("financial_agent", result.get("financial_analysis")),
            ("market_agent", result.get("market_data")),
            ("risk_agent", result.get("risk_profile")),
            ("portfolio_agent", result.get("candidate_portfolio")),
            ("scenario_agent", result.get("scenarios")),
            ("critic_agent", result.get("validation_result")),
            ("final_agent", result.get("final_response")),
        ]:
            db.execute(
                """INSERT INTO agent_logs(analysis_id,agent_name,status,input_summary,output_summary)
                   VALUES(?,?,?,?,?)""",
                (
                    analysis_id,
                    agent_name,
                    "completed" if output is not None else "skipped",
                    None,
                    json.dumps(output)[:10000] if output is not None else None,
                ),
            )

    return {"analysis_id": analysis_id, **result}


@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, user_id=Depends(get_current_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM analyses WHERE id=? AND user_id=?",
            (analysis_id, user_id),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Analysis not found")
    data = dict(row)
    if data.get("final_response"):
        try:
            data["final_response"] = json.loads(data["final_response"])
        except Exception:
            pass
    return data
