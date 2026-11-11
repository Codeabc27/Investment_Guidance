from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_db
from app.schemas.analysis import WhatIfRequest
from app.services.security import get_current_user
from app.calculations.scenarios import calculate_scenarios
router=APIRouter(prefix="/api/what-if",tags=["What-if"])

@router.post("")
def what_if(req:WhatIfRequest,user_id=Depends(get_current_user)):
    with get_db() as db: g=db.execute("SELECT * FROM goals WHERE id=? AND user_id=?",(req.goal_id,user_id)).fetchone()
    if not g: raise HTTPException(404,"Goal not found")
    g=dict(g); monthly=req.monthly_contribution if req.monthly_contribution is not None else g["monthly_contribution"]; years=req.horizon_years if req.horizon_years is not None else g["horizon_years"]
    return {"goal_id":req.goal_id,"monthly_contribution":monthly,"horizon_years":years,"scenarios":calculate_scenarios(monthly,years,g["current_amount"])}
