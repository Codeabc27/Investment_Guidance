def run(state):
    issues = []
    goal = state.get("goal", {})
    portfolio = state.get("candidate_portfolio", {})
    scenarios = state.get("scenarios", {})

    if float(goal.get("target_amount") or 0) <= 0:
        issues.append("Target amount is required.")
    if float(goal.get("horizon_years") or 0) <= 0:
        issues.append("Investment horizon is required.")
    if float(goal.get("monthly_contribution") or 0) < 0:
        issues.append("Monthly contribution cannot be negative.")

    allocation = portfolio.get("allocation", {})
    if allocation:
        total = sum(float(v) for v in allocation.values())
        if abs(total - 100) > 0.01:
            issues.append("Portfolio allocation must total 100%.")
    else:
        issues.append("Portfolio allocation is missing.")

    if not scenarios:
        issues.append("Scenario calculations are missing.")

    return {
        "validation_result": {
            "status": "REVISE" if issues else "PASS",
            "issues": issues,
            "warnings": [],
        }
    }
