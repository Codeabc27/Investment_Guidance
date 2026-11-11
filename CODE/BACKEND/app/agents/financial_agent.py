def run(state):
    p = state.get("financial_profile", {})
    income = float(p.get("monthly_income") or 0)
    expenses = float(p.get("monthly_expenses") or 0)
    return {
        "financial_analysis": {
            "monthly_surplus": max(0, income - expenses),
            "savings": float(p.get("total_savings") or 0),
            "liabilities": float(p.get("liabilities") or 0),
            "emergency_fund": float(p.get("emergency_fund") or 0),
            "existing_investments": float(p.get("existing_investments") or 0),
        }
    }
