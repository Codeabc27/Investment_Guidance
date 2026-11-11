from .sip import future_value

DEFAULT_SCENARIOS = {
    "pessimistic": 0.04,
    "expected": 0.08,
    "optimistic": 0.12,
}

def calculate_scenarios(monthly_contribution, years, current_amount=0, rates=None):
    rates = rates or DEFAULT_SCENARIOS
    return {
        name: {
            "annual_return": rate,
            "projected_value": round(future_value(monthly_contribution, rate, years, current_amount), 2),
        }
        for name, rate in rates.items()
    }
