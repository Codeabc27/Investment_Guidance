def required_monthly_contribution(target, current, annual_return, years):
    months = int(round(years * 12))
    if months <= 0:
        return max(0, target-current)
    r = annual_return / 12
    future_current = current * ((1+r)**months)
    if r == 0:
        return max(0, (target-current)/months)
    payment = (target-future_current) * r / (((1+r)**months)-1)
    return max(0, payment)
