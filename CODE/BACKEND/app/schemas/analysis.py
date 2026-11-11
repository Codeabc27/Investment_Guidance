from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RiskRequest(BaseModel):
    answers: Dict[str, Any] = {}
class AnalysisRequest(BaseModel):
    goal_id: int
class WhatIfRequest(BaseModel):
    goal_id: int
    monthly_contribution: Optional[float] = Field(default=None, ge=0)
    horizon_years: Optional[float] = Field(default=None, gt=0)
class ChatRequest(BaseModel):
    goal_id: int
    message: str = Field(min_length=1, max_length=4000)
