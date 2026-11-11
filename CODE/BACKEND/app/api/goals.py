from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_db
from app.schemas.goals import GoalCreate, GoalUpdate
from app.services.security import get_current_user
router = APIRouter(prefix="/api/goals", tags=["Goals"])

@router.get("")
def list_goals(user_id=Depends(get_current_user)):
    with get_db() as db:
        return [dict(r) for r in db.execute("SELECT * FROM goals WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()]

@router.post("")
def create_goal(goal: GoalCreate, user_id=Depends(get_current_user)):
    with get_db() as db:
        cur=db.execute("""INSERT INTO goals(user_id,name,goal_type,target_amount,current_amount,monthly_contribution,horizon_years,description) VALUES(?,?,?,?,?,?,?,?)""",
                       (user_id,goal.name,goal.goal_type,goal.target_amount,goal.current_amount,goal.monthly_contribution,goal.horizon_years,goal.description))
        return dict(db.execute("SELECT * FROM goals WHERE id=?", (cur.lastrowid,)).fetchone())

@router.get("/{goal_id}")
def get_goal(goal_id:int, user_id=Depends(get_current_user)):
    with get_db() as db: row=db.execute("SELECT * FROM goals WHERE id=? AND user_id=?", (goal_id,user_id)).fetchone()
    if not row: raise HTTPException(404,"Goal not found")
    return dict(row)

@router.put("/{goal_id}")
def update_goal(goal_id:int, goal:GoalUpdate, user_id=Depends(get_current_user)):
    with get_db() as db:
        if not db.execute("SELECT id FROM goals WHERE id=? AND user_id=?", (goal_id,user_id)).fetchone(): raise HTTPException(404,"Goal not found")
        db.execute("""UPDATE goals SET name=?,goal_type=?,target_amount=?,current_amount=?,monthly_contribution=?,horizon_years=?,description=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?""",
                   (goal.name,goal.goal_type,goal.target_amount,goal.current_amount,goal.monthly_contribution,goal.horizon_years,goal.description,goal.status,goal_id,user_id))
        return dict(db.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone())

@router.delete("/{goal_id}")
def delete_goal(goal_id:int, user_id=Depends(get_current_user)):
    with get_db() as db:
        cur=db.execute("DELETE FROM goals WHERE id=? AND user_id=?", (goal_id,user_id))
        if cur.rowcount==0: raise HTTPException(404,"Goal not found")
    return {"message":"Goal deleted"}
