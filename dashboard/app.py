import streamlit as st
import pandas as pd
from dashboard.data_loader import DataLoader
from forward.engine import RESULTS_DIR
from dashboard import components

def main():
    st.set_page_config(page_title="TPQSE Dashboard", layout="wide", page_icon="📈")
    
    # Minimal custom CSS for simple design
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            border: 1px solid #333;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
        }
        .metric-label {
            font-size: 1rem;
            color: #888;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("TPQSE Forward Strategy Engine")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Refresh Data"):
            st.rerun()
            
    dl = DataLoader(str(RESULTS_DIR), "./results/historical")
    
    tabs = st.tabs(["Today's Signals", "Open Positions", "Strategy Health", "Failure Conditions", "Historical Research", "System Health"])
    
    with tabs[0]:
        components.render_todays_signals(dl)
        
    with tabs[1]:
        components.render_open_positions(dl)
        
    with tabs[2]:
        components.render_strategy_health(dl)
        
    with tabs[3]:
        components.render_failure_conditions(dl)
        
    with tabs[4]:
        components.render_historical_research(dl)
        
    with tabs[5]:
        components.render_system_health(dl)

if __name__ == "__main__":
    main()
