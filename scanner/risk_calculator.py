import math

class RiskCalculator:
    def __init__(self, risk_percent: float = 0.005):
        self.risk_percent = risk_percent

    def calculate_position(self, equity: float, entry: float, stop: float) -> dict:
        """
        Calculates position size based on risk parameters.
        Returns a dict with position_size, risk_amount, risk_per_share.
        """
        if equity <= 0:
            return {"position_size": 0, "risk_amount": 0, "risk_per_share": 0, "status": "INVALID: Insufficient capital"}
            
        risk_amount = equity * self.risk_percent
        risk_per_share = entry - stop
        
        if risk_per_share <= 0:
            return {"position_size": 0, "risk_amount": 0, "risk_per_share": 0, "status": "INVALID: Negative or zero risk distance"}
            
        quantity = math.floor(risk_amount / risk_per_share)
        
        if quantity <= 0:
            return {"position_size": 0, "risk_amount": risk_amount, "risk_per_share": risk_per_share, "status": "INVALID: Position size <= 0"}
            
        return {
            "position_size": quantity,
            "risk_amount": risk_amount,
            "risk_per_share": risk_per_share,
            "status": "VALID"
        }
