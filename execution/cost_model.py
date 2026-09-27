def compute_trade_costs(trade_value_buy: float, trade_value_sell: float, cfg) -> float:
    def leg_cost(value, is_buy_leg: bool) -> float:
        brokerage = value * (cfg.brokerage_value / 100.0) if cfg.brokerage_type == "percentage" else cfg.brokerage_value
        exch = value * cfg.exchange_transaction_charge_pct / 100.0
        stt = value * cfg.stt_pct_delivery / 100.0
        sebi = value * cfg.sebi_charges_per_crore / 1e7
        stamp = value * cfg.stamp_duty_pct_buy_leg / 100.0 if is_buy_leg else 0.0
        gst_base = brokerage + exch + sebi
        gst = gst_base * cfg.gst_pct / 100.0
        return brokerage + exch + stt + sebi + stamp + gst
        
    return leg_cost(trade_value_buy, True) + leg_cost(trade_value_sell, False)
