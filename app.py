import streamlit as st

# ✅ Page config must be first Streamlit command
st.set_page_config(page_title="🎓 Job Finder AI", layout="wide")

# ✅ Load custom CSS (only AFTER set_page_config)
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import other components
from utils.search_engine import JobSearchEngine
from utils.ui_components import show_header, show_filters, show_results, show_footer
from utils.analytics import log_search_event

# --- HEADER ---
show_header()

# --- FILTERS ---
filters = show_filters()

# --- BUTTON ---
if st.button("🔎 Find My Dream Job", use_container_width=True):
    search_engine = JobSearchEngine()
    with st.spinner("Analyzing web for best matches using AI ✨"):
        results = search_engine.search(filters)
        log_search_event(filters, results)
        show_results(results)

# --- FOOTER ---
show_footer()
