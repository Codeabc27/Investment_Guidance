def future_value(monthly_contribution, annual_return, years, initial_amount=0):
    months = max(0, int(round(years * 12)))
    if months == 0:
        return float(initial_amount)
    r = annual_return / 12
    if r == 0:
        return initial_amount + monthly_contribution * months
    return initial_amount * (1+r)**months + monthly_contribution * (((1+r)**months - 1) / r)
