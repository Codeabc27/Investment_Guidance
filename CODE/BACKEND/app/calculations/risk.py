VALID_CATEGORIES = {"Conservative", "Moderate", "Growth", "Aggressive"}


def score_risk(answers, selected_category=None):
    """Return a stable risk result.

    The UI's explicit risk selection is preferred. Numeric answers are only used
    as a fallback, preventing text fields such as 'beginner' from distorting the score.
    """
    category = str(selected_category or "").strip().title()
    if category in VALID_CATEGORIES:
        numeric = []
        for key in ("loss_tolerance_score", "horizon_score"):
            try:
                numeric.append(float((answers or {}).get(key)))
            except (TypeError, ValueError):
                pass
        score = sum(numeric) / len(numeric) if numeric else 3.0
        return {"score": round(score, 2), "category": category}

    total = 0.0
    count = 0
    for value in (answers or {}).values():
        try:
            total += float(value)
            count += 1
        except (TypeError, ValueError):
            continue

    score = total / count if count else 3.0
    if score >= 4:
        category = "Aggressive"
    elif score >= 3:
        category = "Growth"
    elif score >= 2:
        category = "Moderate"
    else:
        category = "Conservative"
    return {"score": round(score, 2), "category": category}
