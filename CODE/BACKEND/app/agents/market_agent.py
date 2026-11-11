from datetime import datetime, timezone


def run(state):
    """Prepare a small market-research request.

    The actual current-web lookup is intentionally performed once by the final
    guidance step, keeping the whole analysis lightweight.
    """
    symbol = state.get("market_symbol") or "NIFTY 50"
    return {
        "market_data": {
            "status": "pending_grounded_lookup",
            "symbol": symbol,
            "query": f"Latest public market context relevant to {symbol} for a goal-oriented investor",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "provider": "Gemini Google Search grounding",
        }
    }
