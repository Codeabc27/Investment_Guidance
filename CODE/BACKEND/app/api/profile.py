from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.services.security import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Financial Profile"])


class ProfileRequest(BaseModel):
    full_name: Optional[str] = None
    monthly_income: float = Field(default=0, ge=0)
    monthly_expenses: float = Field(default=0, ge=0)
    total_savings: float = Field(default=0, ge=0)
    emergency_fund: float = Field(default=0, ge=0)
    liabilities: float = Field(default=0, ge=0)
    existing_investments: float = Field(default=0, ge=0)


@router.get("")
def get_profile(user_id=Depends(get_current_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM user_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else {"user_id": user_id}


@router.post("")
def save_profile(payload: ProfileRequest, user_id=Depends(get_current_user)):
    values = (
        payload.full_name,
        payload.monthly_income,
        payload.monthly_expenses,
        payload.total_savings,
        payload.emergency_fund,
        payload.liabilities,
        payload.existing_investments,
    )
    with get_db() as db:
        exists = db.execute(
            "SELECT id FROM user_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if exists:
            db.execute(
                """UPDATE user_profiles SET full_name=?, monthly_income=?, monthly_expenses=?,
                   total_savings=?, emergency_fund=?, liabilities=?, existing_investments=?,
                   updated_at=CURRENT_TIMESTAMP WHERE user_id=?""",
                (*values, user_id),
            )
        else:
            db.execute(
                """INSERT INTO user_profiles(user_id,full_name,monthly_income,monthly_expenses,
                   total_savings,emergency_fund,liabilities,existing_investments)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (user_id, *values),
            )
        row = db.execute(
            "SELECT * FROM user_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()
    return dict(row)
