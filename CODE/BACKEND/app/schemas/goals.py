from pydantic import BaseModel, Field
from typing import Optional

class GoalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    goal_type: str
    target_amount: float = Field(gt=0)
    current_amount: float = Field(default=0, ge=0)
    monthly_contribution: float = Field(default=0, ge=0)
    horizon_years: float = Field(gt=0)
    description: Optional[str] = None

class GoalUpdate(GoalCreate):
    status: str = "active"

class GoalResponse(GoalCreate):
    id: int
    user_id: int
    status: str
