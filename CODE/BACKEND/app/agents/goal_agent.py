def run(state):
    goal = state.get("goal", {})
    return {
        "goal_analysis": {
            "goal_type": goal.get("goal_type"),
            "target_amount": goal.get("target_amount"),
            "horizon_years": goal.get("horizon_years"),
            "monthly_contribution": goal.get("monthly_contribution"),
            "summary": f"Goal: {goal.get('name', 'Investment Goal')}",
        }
    }
