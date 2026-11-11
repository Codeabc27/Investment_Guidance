from app.calculations.scenarios import calculate_scenarios


def run(state):
    goal = state.get("goal", {})
    scenarios = calculate_scenarios(
        float(goal.get("monthly_contribution") or 0),
        float(goal.get("horizon_years") or 1),
        float(goal.get("current_amount") or 0),
    )
    return {"scenarios": scenarios}
