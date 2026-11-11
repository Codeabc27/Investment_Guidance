from langgraph.graph import StateGraph, START, END
from app.workflow.state import InvestmentState
from app.agents.goal_agent import run as goal
from app.agents.financial_agent import run as financial
from app.agents.market_agent import run as market
from app.agents.risk_agent import run as risk
from app.agents.portfolio_agent import run as portfolio
from app.agents.scenario_agent import run as scenario
from app.agents.critic_agent import run as critic
from app.agents.final_agent import run as final

def build_graph():
    graph = StateGraph(InvestmentState)
    graph.add_node("goal_agent", goal)
    graph.add_node("financial_agent", financial)
    graph.add_node("market_agent", market)
    graph.add_node("risk_agent", risk)
    graph.add_node("portfolio_agent", portfolio)
    graph.add_node("scenario_agent", scenario)
    graph.add_node("critic_agent", critic)
    graph.add_node("final_agent", final)
    graph.add_edge(START, "goal_agent")
    graph.add_edge(START, "financial_agent")
    graph.add_edge(START, "market_agent")
    graph.add_edge(START, "risk_agent")
    graph.add_edge(
        ["goal_agent", "financial_agent", "market_agent", "risk_agent"],
        "portfolio_agent",
    )
    graph.add_edge("portfolio_agent", "scenario_agent")
    graph.add_edge("scenario_agent", "critic_agent")
    graph.add_edge("critic_agent", "final_agent")
    graph.add_edge("final_agent", END)
    return graph.compile()

investment_graph = build_graph()
