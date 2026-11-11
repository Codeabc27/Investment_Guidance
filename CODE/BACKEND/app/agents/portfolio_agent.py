"""Deterministic portfolio construction for the student MVP.

This avoids spending Gemini tokens on a task that is better represented by
simple, auditable allocation rules. Gemini explains the result later.
"""


ALLOCATIONS = {
    "Conservative": {"Equity": 30, "Debt": 60, "Cash": 10},
    "Moderate": {"Equity": 50, "Debt": 40, "Cash": 10},
    "Growth": {"Equity": 70, "Debt": 25, "Cash": 5},
    "Aggressive": {"Equity": 85, "Debt": 10, "Cash": 5},
}


def run(state):
    category = state.get("risk_profile", {}).get("category", "Moderate").title()
    allocation = ALLOCATIONS.get(category, ALLOCATIONS["Moderate"])
    return {
        "candidate_portfolio": {
            "strategy_name": f"{category} Goal Strategy",
            "risk_level": category,
            "allocation": allocation,
            "rationale": "Allocation is selected from the user's risk category and kept auditable for the student MVP.",
            "risks": [
                "Market volatility",
                "Inflation",
                "Actual returns may differ from scenario assumptions",
            ],
            "llm_status": "deterministic",
        }
    }
