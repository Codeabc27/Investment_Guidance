from pydantic import BaseModel, Field
from typing import Optional
class ProfileCreate(BaseModel):
    full_name: Optional[str] = None
    monthly_income: float = Field(default=0, ge=0)
    monthly_expenses: float = Field(default=0, ge=0)
    total_savings: float = Field(default=0, ge=0)
    emergency_fund: float = Field(default=0, ge=0)
    liabilities: float = Field(default=0, ge=0)
    existing_investments: float = Field(default=0, ge=0)
