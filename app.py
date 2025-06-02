import streamlit as st
import requests
import re
import time
from urllib.parse import urlparse
from tavily import TavilyClient

# --- Page config ---
st.set_page_config(page_title="Student Job Finder", page_icon="🎓", layout="wide")

# --- API key from secrets ---
try:
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
    client = TavilyClient(api_key=TAVILY_API_KEY)
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
        <p class="subtitle">🔍 Find direct links to actual job postings</p>
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

# --- Cache for API calls ---
if 'search_cache' not in st.session_state:
    st.session_state.search_cache = {}


# --- Specific job search function ---
def search_direct_job_postings(job_types, fields, regions):
    """Search for direct job posting links, not job search sites"""

    all_job_postings = []

    for job_type in job_types[:2]:  # Limit for performance
        for field in fields[:2]:
            for region in regions[:1]:  # Focus on one region at a time

                # Location mapping
                location_map = {
                    "South": "באר שבע אשדוד נגב",
                    "Center": "תל אביב רמת גן פתח תקווה הרצליה הוד השרון",
                    "North": "חיפה נצרת עפולה טבריה",
                    "All of Israel": "Israel ישראל"
                }
                location = location_map.get(region, "Israel")

                # Very specific queries that should return actual job postings
                specific_queries = [
                    # LinkedIn specific job postings
                    f'site:linkedin.com/jobs/view "{job_type}" "{field}" Israel',
                    f'site:linkedin.com/jobs/view "{field}" student intern Israel',

                    # Exact job title searches
                    f'"{field} {job_type}" {location} "apply now"',
                    f'"{field} analyst student" {location}',
                    f'"software engineer intern" {location}',

                    # Company career pages
                    f'"{job_type}" "{field}" {location} site:*.com/careers',
                    f'"{job_type}" "{field}" {location} site:*.co.il',

                    # Specific job board URLs
                    f'site:jobmaster.co.il/job "{field}" {job_type}',
                    f'site:drushim.co.il/job "{job_type}" {field}',

                    # Hebrew searches
                    f'"{field}" סטודנט משרה {location}',
                    f'מפתח תוכנה סטודנט {location}'
                ]

                for query in specific_queries[:6]:  # Limit queries per combination
                    try:
                        # Check cache first
                        cache_key = f"{query}_direct"
                        if cache_key in st.session_state.search_cache:
                            results = st.session_state.search_cache[cache_key]
                        else:
                            response = client.search(
                                query=query,
                                search_depth="advanced",
                                max_results=6
                            )
                            results = response.get("results", [])
                            st.session_state.search_cache[cache_key] = results

                        # Filter for actual job postings
                        for result in results:
                            if is_actual_job_posting(result):
                                all_job_postings.append(result)

                        time.sleep(0.3)  # Rate limiting

                    except Exception as e:
                        continue

    return all_job_postings


def is_actual_job_posting(result):
    """Check if this is a direct job posting, not a search page"""
    url = result.get('url', '').lower()
    title = result.get('title', '').lower()
    content = result.get('content', '').lower()

    # LinkedIn job view URLs are always job postings
    if '/jobs/view/' in url and 'linkedin.com' in url:
        return True

    # Job board specific patterns
    job_board_patterns = [
        r'jobmaster\.co\.il/job/\d+',
        r'drushim\.co\.il/job/\d+',
        r'alljobs\.co\.il.*jobnum=\d+',
        r'/careers/.*\d+',
        r'/job/\d+'
    ]

    if any(re.search(pattern, url) for pattern in job_board_patterns):
        return True

    # Positive indicators for job postings
    job_posting_indicators = [
        'apply now', 'apply here', 'submit application',
        'job description', 'requirements', 'qualifications',
        'responsibilities', 'what you will do',
        'הגש מועמדות', 'שלח קורות חיים', 'דרישות התפקיד'
    ]

    # Negative indicators (search pages, category pages)
    exclude_indicators = [
        '/search?', '/search/', '/jobs?', '/browse',
        '/categories', '/companies', '/results',
        'job search', 'find jobs', 'browse jobs'
    ]

    # Check for exclusions first
    if any(indicator in url or indicator in title for indicator in exclude_indicators):
        return False

    # Count positive indicators
    positive_score = sum(1 for indicator in job_posting_indicators
                         if indicator in title or indicator in content)

    return positive_score >= 2


def extract_company_name(url, title):
    """Extract company name from URL or title"""
    try:
        domain = urlparse(url).netloc.lower()

        # LinkedIn special handling
        if 'linkedin.com' in domain:
            if ' at ' in title:
                company = title.split(' at ')[-1].strip()
                # Clean up common suffixes
                company = re.sub(r'\s*\|.*$', '', company)
                return company
            else:
                return "LinkedIn Job"

        # Other job sites
        company_map = {
            'jobmaster.co.il': 'JobMaster',
            'drushim.co.il': 'Drushim',
            'alljobs.co.il': 'AllJobs',
            'jobs.co.il': 'Jobs.co.il'
        }

        for domain_key, company_name in company_map.items():
            if domain_key in domain:
                return company_name

        # Extract from domain
        return domain.replace('www.', '').split('.')[0].title()

    except:
        return "Company"


def clean_job_description(content):
    """Clean and format job description"""
    if not content:
        return "Job description not available"

    # Remove HTML tags
    content = re.sub(r'<[^>]+>', ' ', content)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)

    # Find relevant sentences
    sentences = content.split('.')
    relevant_sentences = []

    for sentence in sentences[:5]:
        if (len(sentence.strip()) > 30 and
                any(word in sentence.lower() for word in
                    ['job', 'position', 'require', 'responsible', 'candidate', 'משרה', 'דרוש'])):
            relevant_sentences.append(sentence.strip())

        if len(relevant_sentences) >= 2:
            break

    result = '. '.join(relevant_sentences)
    if len(result) > 300:
        result = result[:300] + '...'

    return result if result else content[:250] + '...'


def create_tags_fast(title, content):
    """Fast tag creation"""
    text = (title + ' ' + content).lower()
    tags = []

    tag_keywords = {
        'Student': ['student', 'סטודנט'],
        'Internship': ['intern', 'internship', 'סטאז'],
        'Remote': ['remote', 'work from home', 'מהבית'],
        'Full Time': ['full time', 'full-time', 'מלאה'],
        'Part Time': ['part time', 'part-time', 'חלקית'],
        'Junior': ['junior', 'entry level', 'התחלה'],
        'Senior': ['senior', 'experienced', 'בכיר']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)

    return tags[:4]


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
                <div class="stat-label">Different Companies</div>
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
def search_jobs(job_types, fields, regions):
    """Main job search function"""

    # Progress tracking
    progress_container = st.container()
    with progress_container:
        progress_text = st.empty()
        progress_bar = st.progress(0)

    try:
        # Step 1: Search for job postings
        progress_text.text("🔍 Searching for direct job postings...")
        progress_bar.progress(30)

        raw_results = search_direct_job_postings(job_types, fields, regions)

        # Step 2: Process results
        progress_text.text("📊 Processing job postings...")
        progress_bar.progress(60)

        job_results = []
        seen_urls = set()

        for result in raw_results:
            url = result.get('url', '')

            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Process job data
            title = result.get('title', 'No Title')
            content = clean_job_description(result.get('content', ''))
            company = extract_company_name(url, title)

            job_results.append({
                'title': title,
                'url': url,
                'content': content,
                'company': company
            })

        # Step 3: Sort by relevance
        progress_text.text("⚡ Finalizing results...")
        progress_bar.progress(90)

        # Sort by LinkedIn jobs first (usually better quality)
        job_results.sort(key=lambda x: 0 if 'linkedin.com' in x['url'] else 1)

        progress_bar.progress(100)
        progress_text.text("✅ Search completed!")

        # Clear progress
        time.sleep(1)
        progress_container.empty()

        return job_results[:12]  # Return top 12

    except Exception as e:
        progress_container.empty()
        st.error(f"Search failed: {str(e)}")
        return []


# --- Search Interface ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Validation
    if not job_types:
        st.warning("⚠️ Please select at least one job type")
    elif not fields:
        st.warning("⚠️ Please select at least one field")
    elif not regions:
        st.warning("⚠️ Please select at least one region")
    elif st.button("🔍 Search Jobs", type="primary", use_container_width=True):
        start_time = time.time()

        # Execute search
        job_results = search_jobs(job_types, fields, regions)

        search_time = time.time() - start_time

        # Show results
        if job_results:
            st.success(f"🎉 Found {len(job_results)} job postings in {search_time:.1f} seconds!")
            show_job_cards(job_results)
        else:
            st.warning(f"No results found in {search_time:.1f} seconds")

# --- Footer ---
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🎯 Lightning-fast student job finder | Gaya Gur</p>
    </div>
""", unsafe_allow_html=True)
