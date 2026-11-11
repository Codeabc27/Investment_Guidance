from app.calculations.risk import score_risk


def run(state):
    return {
        "risk_profile": score_risk(
            state.get("risk_answers", {}),
            state.get("risk_category"),
        )
    }
