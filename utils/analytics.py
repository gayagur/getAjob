# utils/analytics.py
import streamlit as st
from datetime import datetime

def log_search_event(filters, results):
    if 'search_log' not in st.session_state:
        st.session_state.search_log = []

    st.session_state.search_log.append({
        "timestamp": datetime.now().isoformat(),
        "filters": filters,
        "results_count": len(results)
    })
