import streamlit as st

# Inject custom CSS
with open("assets/style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Header Section ---
def show_header():
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1>Student Job Finder AI</h1>
        <p style='color: #aaa;'>Smart job recommendations powered by real-time AI search</p>
    </div>
    """, unsafe_allow_html=True)

# --- Filter Section ---
def show_filters():
    st.markdown("""
    <h3 style="margin: 2rem 0 1rem 0; text-align: center;">🔎 Customize Your Job Search</h3>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        job_types = st.multiselect("🎓 Job Type", ["Student", "Internship", "Junior"], default=["Student"])
    with col2:
        fields = st.multiselect("💻 Field", ["Software Engineer", "Data Analyst", "DevOps"], default=["Software Engineer"])
    with col3:
        regions = st.multiselect("📍 Region", ["Tel Aviv", "Remote", "All Israel"], default=["Tel Aviv"])

    return {"job_types": job_types, "fields": fields, "regions": regions}

# --- Results Section ---
def show_results(results):
    if not results:
        st.error("No results found. Try different filters.")
        return

    st.markdown("""
    <div style='margin-top: 3rem; margin-bottom: 2rem;'>
        <h2 style='text-align:center;'>📄 Matching Job Listings</h2>
    </div>
    """, unsafe_allow_html=True)

    for job in results:
        tags = []
        content_lower = job['content'].lower()
        if "urgent" in content_lower or "apply now" in content_lower:
            tags.append("🔥 Active")
        if "new" in content_lower or "just posted" in content_lower:
            tags.append("🆕 New")

        tag_html = " ".join(f"<span class='job-tag'>{tag}</span>" for tag in tags)

        st.markdown(f"""
        <div class="job-card">
            <div class="job-title" style="font-size: 1.8rem; font-weight: 800; color: var(--text-primary); margin-bottom: 0.5rem;">{job['title']}</div>
            <div class="job-company" style="font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.5rem;">🏢 {job['company']}</div>
            <div class="job-desc" style="font-size: 1.05rem; color: var(--text-primary); line-height: 1.6;">{job['content'][:300]}...</div>
            <div style="margin-top: 0.5rem;">{tag_html}</div>
            <div style="margin-top: 1rem;">
                <a class="button" href="{job['url']}" target="_blank">✨ Apply Now</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Footer Section ---
def show_footer():
    st.markdown("""
    <hr style='border: none; border-top: 1px solid #333;'>
    <div style='text-align: center; padding: 1rem; color: #777;'>
        Built with ❤️ by Gaya Gur | 2025
    </div>
    """, unsafe_allow_html=True)
