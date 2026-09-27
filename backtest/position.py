import math

def size_position(entry_price: float, stop_price: float,
                  max_risk_rupees: float, available_cash: float) -> int:
    risk_per_share = entry_price - stop_price
    if risk_per_share <= 0:
        return 0
    raw_qty = math.floor(max_risk_rupees / risk_per_share)
    max_affordable_qty = math.floor(available_cash / entry_price)
    return max(0, min(raw_qty, max_affordable_qty))
