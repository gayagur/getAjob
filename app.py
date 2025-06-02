import streamlit as st
import requests
import re
import time
from urllib.parse import urlparse
from tavily import TavilyClient
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

# --- Page config ---
st.set_page_config(page_title="Student Job Finder", page_icon="🎓", layout="wide")

# --- API key from secrets ---
try:
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
    client = TavilyClient(TAVILY_API_KEY)
except Exception as e:
    st.error("🔑 Missing TAVILY_API_KEY in Streamlit secrets.")
    st.stop()

# --- CSS Styling: Modern Dark Mode ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff !important;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
        }

        .main .block-container {
            background: rgba(30, 30, 40, 0.9);
            backdrop-filter: blur(20px);
            padding: 2.5rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        /* Header Styling */
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .main-title {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ff6b9d, #4ecdc4, #45b7d1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        }

        .subtitle {
            font-size: 1.2rem;
            color: #b8b8b8;
            font-weight: 300;
            margin-bottom: 2rem;
        }

        /* Filter Section */
        .filter-section {
            background: rgba(40, 40, 50, 0.6);
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        h1, h2, h3, h4, h5, h6, label {
            color: #ffffff !important;
        }

        .stSelectbox > div > div {
            background: rgba(50, 50, 60, 0.8) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            backdrop-filter: blur(10px);
        }

        .stSelectbox > div > div:hover {
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.05);
        }

        /* Multiselect styling */
        .stMultiSelect > div > div {
            background: rgba(50, 50, 60, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
        }

        .stMultiSelect > div > div > div {
            color: #ffffff !important;
        }

        /* Selected tags in multiselect */
        .stMultiSelect [data-baseweb="tag"] {
            background: linear-gradient(135deg, #ff6b9d, #4ecdc4) !important;
            color: white !important;
            border: none !important;
            margin: 2px !important;
        }

        /* Dropdown options */
        .stMultiSelect [role="option"] {
            background: rgba(40, 40, 50, 0.9) !important;
            color: #ffffff !important;
        }

        .stMultiSelect [role="option"]:hover {
            background: rgba(60, 60, 70, 0.9) !important;
        }

        /* Search Button */
        .stButton > button {
            background: linear-gradient(135deg, #ff6b9d, #4ecdc4);
            color: white;
            font-weight: 600;
            border-radius: 50px;
            padding: 0.8rem 3rem;
            border: none;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(255, 107, 157, 0.3);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(255, 107, 157, 0.4);
        }

        /* Job Cards */
        .job-card {
            background: linear-gradient(135deg, rgba(40, 40, 50, 0.9), rgba(50, 50, 60, 0.8));
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            margin-bottom: 1.5rem;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .job-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #ff6b9d, #4ecdc4, #45b7d1);
        }

        .job-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .job-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 1rem;
            line-height: 1.4;
        }

        .job-description {
            color: #c0c0c0;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .job-meta {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .job-tag {
            background: rgba(78, 205, 196, 0.2);
            color: #4ecdc4;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(78, 205, 196, 0.3);
        }

        .apply-btn {
            background: linear-gradient(135deg, #4ecdc4, #45b7d1);
            color: #000000;
            padding: 0.8rem 2rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(78, 205, 196, 0.3);
        }

        .apply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(78, 205, 196, 0.4);
            color: #000000;
            text-decoration: none;
        }

        /* Stats Section */
        .stats-container {
            display: flex;
            gap: 1rem;
            margin: 1.5rem 0;
        }

        .stat-box {
            background: rgba(40, 40, 50, 0.6);
            padding: 1rem;
            border-radius: 10px;
            flex: 1;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stat-number {
            font-size: 1.5rem;
            font-weight: 700;
            color: #4ecdc4;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #b8b8b8;
        }

        /* Loading Animation */
        .stSpinner {
            color: #4ecdc4 !important;
        }

        /* Progress Bar */
        .progress-container {
            background: rgba(40, 40, 50, 0.6);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Warning/Error Messages */
        .stWarning {
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-radius: 10px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2rem;
            }

            .job-card {
                padding: 1.5rem;
            }

            .job-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🎓 Student Job Finder</h1>
        <p class="subtitle">🔍 Find direct links to actual job postings - not just job sites!</p>
    </div>
""", unsafe_allow_html=True)

# --- Filters in a styled container ---
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
st.markdown("### ⚙️ Select Your Filters")

col1, col2, col3 = st.columns(3)
with col1:
    job_types = st.multiselect(
        "💼 Job Types",
        ["Student", "Internship", "Part-time", "Graduate", "Entry Level"],
        default=["Student"]
    )
with col2:
    fields = st.multiselect(
        "🧠 Fields",
        ["Software", "Data", "BI", "DevOps", "QA", "Product", "Design", "Marketing"],
        default=["Software"]
    )
with col3:
    regions = st.multiselect(
        "🌍 Regions",
        ["South", "Center", "North", "All of Israel"],
        default=["All of Israel"]
    )

st.markdown('</div>', unsafe_allow_html=True)


# --- Fast parallel search functions ---
def create_fast_queries(job_types, fields, regions):
    """Create optimized queries for faster results"""
    queries = []

    # Most effective job sites with specific URL patterns
    base_queries = [
        'site:jobmaster.co.il/job/ student software developer',
        'site:linkedin.com/jobs/view/ intern Israel tech',
        'site:drushim.co.il student data analyst',
        'site:jobs.co.il "סטודנט" "פיתוח"',
        '"הגש מועמדות" "Junior" developer',
        '"שלח קו״ח" אנליסט data'
    ]

    # Add targeted queries based on selections
    for job_type in job_types[:2]:  # Limit to 2 job types for speed
        for field in fields[:2]:  # Limit to 2 fields for speed
            queries.extend([
                f'site:jobmaster.co.il/job/ "{job_type}" "{field}"',
                f'site:linkedin.com/jobs/view/ "{field}" Israel',
                f'"{job_type}" "{field}" דרוש apply'
            ])

    return base_queries + queries[:10]  # Total max 16 queries


def parallel_search(queries):
    """Execute multiple searches in parallel for speed"""
    results = []

    def search_single_query(query):
        try:
            response = client.search(
                query=query,
                search_depth="basic",  # Faster than advanced
                max_results=3,
                include_raw_content=True,
                include_domains=[
                    "jobmaster.co.il", "linkedin.com", "drushim.co.il",
                    "jobs.co.il", "alljobs.co.il"
                ]
            )
            return response.get("results", [])
        except Exception as e:
            return []

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(search_single_query, query) for query in queries]

        for future in futures:
            try:
                batch_results = future.result(timeout=10)  # 10 second timeout
                results.extend(batch_results)
            except Exception:
                continue

    return results


def extract_job_content(urls):
    """Use Tavily Extract for better content extraction"""
    if not urls:
        return {}

    try:
        # Split URLs into chunks for API limits
        url_chunks = [urls[i:i + 5] for i in range(0, len(urls), 5)]
        extracted_content = {}

        for chunk in url_chunks:
            try:
                response = client.extract(urls=chunk)
                for result in response.get("results", []):
                    url = result.get("url", "")
                    content = result.get("raw_content", "")
                    if url and content:
                        extracted_content[url] = content
            except Exception:
                continue

        return extracted_content
    except Exception:
        return {}


# --- Enhanced filtering with extracted content ---
def filter_job_links_fast(search_results, extracted_content=None):
    """Fast filtering with better content analysis"""
    if not search_results:
        return []

    job_links = []
    seen_urls = set()

    # Job URL patterns - more specific for speed
    job_patterns = [
        r'/job/\d{5,}',
        r'/jobs/view/\d{8,}',
        r'JobNum=\d{4,}',
        r'/position/\d+',
        r'job_id=\d+'
    ]

    # Quick exclude patterns
    exclude_patterns = [
        r'/search', r'/browse', r'/directory', r'/categories',
        r'page=\d+', r'/jobs/?$'
    ]

    for result in search_results:
        url = result.get("url", "")
        title = result.get("title", "")
        content = result.get("content", "")

        if not url or url in seen_urls:
            continue

        # Quick exclude check
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in exclude_patterns):
            continue

        # Use extracted content if available
        if extracted_content and url in extracted_content:
            content = extracted_content[url]

        # Quick job detection
        is_job_url = any(re.search(pattern, url, re.IGNORECASE) for pattern in job_patterns)

        # Fast content scoring
        job_keywords = ['apply', 'position', 'requirements', 'salary', 'הגש מועמדות', 'דרוש', 'משרה']
        content_score = sum(1 for keyword in job_keywords if keyword in (title + content).lower())

        if is_job_url or content_score >= 3:
            seen_urls.add(url)

            # Quick company extraction
            company = extract_company_fast(url)

            # Clean description
            clean_desc = clean_content_fast(content, title)

            job_links.append({
                "title": title,
                "url": url,
                "content": clean_desc,
                "company": company,
                "score": content_score
            })

    return sorted(job_links, key=lambda x: x['score'], reverse=True)[:12]


def extract_company_fast(url):
    """Fast company name extraction"""
    domain = urlparse(url).netloc.lower()
    company_map = {
        'jobmaster': 'JobMaster',
        'linkedin': 'LinkedIn',
        'drushim': 'Drushim',
        'jobs.co.il': 'Jobs.co.il',
        'alljobs': 'AllJobs'
    }

    for key, value in company_map.items():
        if key in domain:
            return value

    return domain.replace('www.', '').split('.')[0].title()


def clean_content_fast(content, title):
    """Fast content cleaning"""
    if not content:
        return "Job description not available"

    # Remove HTML quickly
    content = re.sub(r'<[^>]+>', ' ', content)
    content = re.sub(r'\s+', ' ', content).strip()

    # Take first relevant sentence
    sentences = content.split('.')[:3]
    relevant = []

    for sentence in sentences:
        if (len(sentence) > 20 and
                any(word in sentence.lower() for word in ['job', 'position', 'require', 'משרה', 'דרוש'])):
            relevant.append(sentence.strip())

    result = '. '.join(relevant) if relevant else content[:200]
    return result + ('...' if len(result) > 200 else '')


def create_tags_fast(title, content):
    """Fast tag creation"""
    text = (title + ' ' + content).lower()
    tags = []

    tag_keywords = {
        'Student': ['student', 'סטודנט'],
        'Internship': ['intern', 'סטאז'],
        'Remote': ['remote', 'מהבית'],
        'Full Time': ['full time', 'מלאה'],
        'Part Time': ['part time', 'חלקית']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)

    return tags


# --- Enhanced job card display ---
def show_job_cards(results):
    if not results:
        st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #b8b8b8;">
                <h3>🕵️‍♂️ No Direct Job Postings Found</h3>
                <p>Try adjusting your filters or searching for a different field</p>
            </div>
        """, unsafe_allow_html=True)
        return

    # Show stats
    st.markdown(f"""
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-number">{len(results)}</div>
                <div class="stat-label">Jobs Found</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(set(r['company'] for r in results))}</div>
                <div class="stat-label">Different Sites</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    for i, r in enumerate(results, 1):
        # Create tags
        tags = create_tags_fast(r['title'], r['content'])
        tags_html = ''.join(f'<span class="job-tag">{tag}</span>' for tag in tags)

        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{r['title']}</div>
            <div class="job-meta">
                <span class="job-tag">{r['company']}</span>
                {tags_html}
            </div>
            <div class="job-description">{r['content']}</div>
            <a class="apply-btn" href="{r['url']}" target="_blank">🚀 View Job</a>
        </div>
        """, unsafe_allow_html=True)


# --- Main search function ---
def fast_job_search(job_types, fields, regions):
    """Main fast search function"""

    # Step 1: Create optimized queries
    queries = create_fast_queries(job_types, fields, regions)

    # Step 2: Parallel search
    progress_text = st.empty()
    progress_text.text("🔍 Searching job sites...")

    search_results = parallel_search(queries)

    progress_text.text("📊 Analyzing results...")

    # Step 3: Filter for job URLs
    potential_jobs = filter_job_links_fast(search_results)

    # Step 4: Extract content for top results if needed
    if potential_jobs:
        top_urls = [job['url'] for job in potential_jobs[:8]]
        progress_text.text("📄 Extracting job details...")

        extracted_content = extract_job_content(top_urls)

        # Re-filter with extracted content
        final_jobs = filter_job_links_fast(search_results, extracted_content)
    else:
        final_jobs = potential_jobs

    progress_text.empty()
    return final_jobs


# --- Search Section ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Validation check
    if not job_types:
        st.warning("⚠️ Please select at least one job type")
    elif not fields:
        st.warning("⚠️ Please select at least one field")
    elif not regions:
        st.warning("⚠️ Please select at least one region")
    elif st.button("🔍 Search Jobs", use_container_width=True):
        start_time = time.time()

        with st.spinner("🚀 Fast searching in progress..."):
            # Fast search
            filtered_jobs = fast_job_search(job_types, fields, regions)

            search_time = time.time() - start_time

            if filtered_jobs:
                st.success(f"✅ Found {len(filtered_jobs)} job postings in {search_time:.1f} seconds!")
            else:
                st.info(f"📦 Search completed in {search_time:.1f} seconds - try different filters")

            # Display results
            show_job_cards(filtered_jobs)

# --- Footer ---
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🎯 Lightning-fast student job finder | Gaya Gur</p>
    </div>
""", unsafe_allow_html=True)