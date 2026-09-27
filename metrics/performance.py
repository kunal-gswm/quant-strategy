import pandas as pd

def compute_core_metrics(ledger: pd.DataFrame) -> dict:
    if len(ledger) == 0:
        return {}
    wins = ledger[ledger["net_pnl"] > 0]
    losses = ledger[ledger["net_pnl"] <= 0]
    
    gross_profit = wins["net_pnl"].sum()
    gross_loss = losses["net_pnl"].sum()  # negative
    
    win_rate = len(wins) / len(ledger) if len(ledger) else float("nan")
    avg_win = wins["net_pnl"].mean() if len(wins) else 0.0
    avg_loss = losses["net_pnl"].mean() if len(losses) else 0.0
    
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else float("inf")
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    
    return {
        "total_trades": len(ledger),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pnl": ledger["net_pnl"].sum(),
    }
