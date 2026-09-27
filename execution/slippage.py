def apply_slippage(price: float, side: str, slippage_type: str, slippage_value: float) -> float:
    if slippage_type == "percentage":
        adjustment = price * (slippage_value / 100.0)
    elif slippage_type == "bps":
        adjustment = price * (slippage_value / 10000.0)
    elif slippage_type == "fixed":
        adjustment = slippage_value
    else:
        adjustment = 0.0
        
    if side == "buy":
        return price + adjustment
    else:
        return price - adjustment
