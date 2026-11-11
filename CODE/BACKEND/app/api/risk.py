import json

from fastapi import APIRouter, Depends

from app.database.database import get_db
from app.services.security import get_current_user
from app.calculations.risk import score_risk

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.get("")
def get_risk(user_id=Depends(get_current_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT score, category, answers_json, created_at FROM risk_profiles WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return {"score": None, "category": None, "answers": {}}
    try:
        answers = json.loads(row["answers_json"]) if row["answers_json"] else {}
    except json.JSONDecodeError:
        answers = {}
    return {"score": row["score"], "category": row["category"], "answers": answers, "created_at": row["created_at"]}


@router.post("")
def save_risk(payload: dict, user_id=Depends(get_current_user)):
    answers = payload.get("answers") or {}
    calculated = score_risk(answers)
    # If the UI explicitly selected a category, preserve it only when valid.
    requested = str(payload.get("category") or "").lower()
    category = requested if requested in {"conservative", "moderate", "growth", "aggressive"} else calculated["category"]

    with get_db() as db:
        db.execute(
            "INSERT INTO risk_profiles(user_id,score,category,answers_json) VALUES(?,?,?,?)",
            (user_id, calculated["score"], category, json.dumps(answers)),
        )

    return {"score": calculated["score"], "category": category, "answers": answers}
