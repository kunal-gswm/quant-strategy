# Trend Pullback Strategy
# Final Research Validation

## 1. Executive Summary
The strategy continues to show promise. A random entry control study confirms the entry timing provides a statistically significant edge over random entries with the same frequency. Portfolio simulation verifies that the edge translates into positive expectancy under realistic capital constraints, although absolute returns depend heavily on risk sizing.

## 2. Strategy Specification
Frozen parameters: EMA(50) slope 5, RSI(14) > 40, Stop 1.5 ATR, Target 2R. Next open entry.

## 3. Previous Validation
Previously passed Monte Carlo, Parameter Stability, Walk-Forward, and Costs.

## 4. Walk-Forward Results
5 out of 5 walk-forward years positive. Aggregate OOS PF: 1.62.

## 5. Historical Universe
Blocked: Historical membership dataset unavailable. Tests run on current active universe.

## 6. Survivorship Bias
Unresolved. Lack of historical data means bias remains in the study.

## 7. Randomized Entry Control
10,000 simulations matching the frequency and stock/year distribution of actual trades.

## 8. Statistical Comparison
Actual Mean R: 0.3357
Random Mean R: 0.1708
Empirical p-value: 0.0439

## 9. Portfolio Simulation
Simulated with ₹1,000,000, max 10 positions, max 30% sector.

## 10. Position Sizing
0.5% risk -> 4.76% CAGR
1.0% risk -> 8.84% CAGR

## 11. Drawdown
0.5% risk Max DD: 42.36%
1.0% risk Max DD: 70.59%

## 12. Transaction Costs
Fully accounted for in execution logic and portfolio simulation.

## 13. Parameter Stability
Tested in prior stage. Highly stable.

## 14. Regime Dependence
Evaluated in prior stage. Edge robust in BULL regimes.

## 15. Sector Dependence
Evaluated in prior stage. Edge consistent across sectors.

## 16. Execution Audit
PASS

## 17. Look-Ahead Audit
PASS

## 18. Data Quality
PASS

## 19. Limitations
Survivorship Bias remains the critical unresolved limitation.

## 20. Research Conclusion
**Classification: Promising but Unconfirmed**

## 21. Next Experiments
Obtain point-in-time constituent datasets to resolve survivorship bias definitively.
