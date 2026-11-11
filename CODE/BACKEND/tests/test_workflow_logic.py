import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BACKEND"))

# Fake Gemini so workflow logic can be tested without a real API key/network call.
class FakeGemini:
    def research(self, prompt, **kwargs):
        return '{"summary":"Demo summary","why_this_strategy":"Risk-aligned allocation and clear goal horizon.","key_risks":["Volatility","Inflation","Actual returns may differ"],"assumptions":["Illustrative scenario rates"],"data_freshness":"Demo grounded research","market_context":"Demo current market context"}'
    def generate(self, prompt, **kwargs):
        return "Demo chat response"

fake_service = types.ModuleType("app.services.gemini_service")
fake_service.gemini_service = FakeGemini()
sys.modules["app.services.gemini_service"] = fake_service

# Minimal LangGraph-compatible fake to execute the graph sequentially.
class FakeCompiled:
    def __init__(self, nodes):
        self.nodes = nodes
    def invoke(self, state):
        data = dict(state)
        for name, fn in self.nodes:
            data.update(fn(data))
        return data

class FakeStateGraph:
    def __init__(self, state_type):
        self.nodes = []
    def add_node(self, name, fn):
        self.nodes.append((name, fn))
    def add_edge(self, *args):
        pass
    def compile(self):
        return FakeCompiled(self.nodes)

fake_langgraph = types.ModuleType("langgraph.graph")
fake_langgraph.StateGraph = FakeStateGraph
fake_langgraph.START = "START"
fake_langgraph.END = "END"
sys.modules["langgraph.graph"] = fake_langgraph

from app.workflow.graph import investment_graph
from app.calculations.scenarios import calculate_scenarios
from app.calculations.risk import score_risk

state = {
    "user_id": 1,
    "goal": {
        "id": 1,
        "name": "House",
        "goal_type": "house",
        "target_amount": 2000000,
        "current_amount": 100000,
        "monthly_contribution": 20000,
        "horizon_years": 6,
    },
    "financial_profile": {
        "monthly_income": 60000,
        "monthly_expenses": 30000,
        "total_savings": 100000,
        "emergency_fund": 100000,
        "liabilities": 0,
        "existing_investments": 50000,
    },
    "risk_answers": {
        "investment_experience": "beginner",
        "risk_tolerance": "moderate",
        "loss_tolerance_percent": 15,
        "investment_horizon_years": 6,
        "emergency_reserve": "partly",
    },
    "risk_category": "Moderate",
    "market_symbol": "NIFTY 50",
}

result = investment_graph.invoke(state)
assert result["risk_profile"]["category"] == "Moderate"
assert sum(result["candidate_portfolio"]["allocation"].values()) == 100
assert set(result["scenarios"]) == {"pessimistic", "expected", "optimistic"}
assert result["validation_result"]["status"] == "PASS"
assert result["final_response"]["status"] == "complete"
assert result["final_response"]["explanation"]["summary"] == "Demo summary"

# Verify the core deterministic calculation independently.
sc = calculate_scenarios(20000, 6, 100000)
assert sc["expected"]["projected_value"] > 0
assert score_risk(state["risk_answers"], "Moderate")["category"] == "Moderate"

print("WORKFLOW LOGIC: PASS")
print("Risk:", result["risk_profile"])
print("Allocation:", result["candidate_portfolio"]["allocation"])
print("Scenarios:", result["scenarios"])
print("Validation:", result["validation_result"])
print("Final status:", result["final_response"]["status"])
