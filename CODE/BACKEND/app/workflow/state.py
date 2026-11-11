from collections.abc import Mapping
from typing import Annotated, Any, TypedDict


def merge_state(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    for key, value in right.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = merge_state(dict(existing), dict(value))
        else:
            merged[key] = value
    return merged


class InvestmentState(TypedDict, total=False):
    user_id: int
    goal: Annotated[dict[str, Any], merge_state]
    financial_profile: Annotated[dict[str, Any], merge_state]
    risk_answers: Annotated[dict[str, Any], merge_state]
    risk_category: str | None
    risk_profile: Annotated[dict[str, Any], merge_state]
    market_symbol: str
    market_data: Annotated[dict[str, Any], merge_state]
    financial_analysis: Annotated[dict[str, Any], merge_state]
    goal_analysis: Annotated[dict[str, Any], merge_state]
    candidate_portfolio: Annotated[dict[str, Any], merge_state]
    scenarios: Annotated[dict[str, Any], merge_state]
    validation_result: Annotated[dict[str, Any], merge_state]
    final_response: Annotated[dict[str, Any], merge_state]
    error: str
