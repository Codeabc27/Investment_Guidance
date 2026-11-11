from fastapi import APIRouter, Depends

from app.services.security import get_current_user

router = APIRouter(prefix="/api/market", tags=["Market"])


@router.get("/{symbol}")
def market(symbol: str, user_id=Depends(get_current_user)):
    return {
        "symbol": symbol.upper(),
        "status": "available_during_analysis",
        "message": "Current market research is performed inside the lightweight Gemini analysis workflow.",
    }
