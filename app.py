import streamlit as st
import requests
import re
import time
import json
from urllib.parse import urlparse, urljoin
from tavily import TavilyClient
from datetime import datetime, timedelta
import concurrent.futures
from typing import List, Dict, Tuple, Optional
import hashlib
import html

# Install required packages
try:
    import serpapi
except ImportError:
    st.warning("📦 SerpAPI not installed. Install with: pip install google-search-results")
    serpapi = None

# --- Page config ---
st.set_page_config(page_title="Student Job Finder", page_icon="🎓", layout="wide")

# --- API keys from secrets ---
try:
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
    client = TavilyClient(api_key=TAVILY_API_KEY)

    # SerpAPI for Google Jobs and search results
    SERP_API_KEY = st.secrets.get("SERP_API_KEY", None)
    if SERP_API_KEY and serpapi:
        serp_client = serpapi.GoogleSearch({"api_key": SERP_API_KEY})
    else:
        serp_client = None

except Exception as e:
    st.error("🔑 Missing TAVILY_API_KEY in Streamlit secrets.")
    st.stop()

# --- Enhanced CSS Styling ---
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
            max-width: 1200px;
            margin: 0 auto;
        }

        .stApp > header {
            display: none;
        }

        .main > div:first-child {
            padding-top: 0;
        }

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
        }

        .subtitle {
            font-size: 1.2rem;
            color: #b8b8b8;
            font-weight: 300;
            margin-bottom: 2rem;
        }

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

        .stMultiSelect > div > div {
            background: rgba(50, 50, 60, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
        }

        .stMultiSelect > div > div > div {
            color: #ffffff !important;
        }

        .stMultiSelect [data-baseweb="tag"] {
            background: linear-gradient(135deg, #ff6b9d, #4ecdc4) !important;
            color: white !important;
            border: none !important;
            margin: 2px !important;
        }

        .stMultiSelect [role="option"] {
            background: rgba(40, 40, 50, 0.9) !important;
            color: #ffffff !important;
        }

        .stMultiSelect [role="option"]:hover {
            background: rgba(60, 60, 70, 0.9) !important;
        }

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

        .job-tag-active {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .job-tag-fresh {
            background: rgba(99, 102, 241, 0.2);
            color: #6366f1;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(99, 102, 241, 0.3);
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
            margin-right: 1rem;
        }

        .apply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(78, 205, 196, 0.4);
            color: #000000;
            text-decoration: none;
        }

        .save-btn {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            padding: 0.8rem 1.5rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .save-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            text-decoration: none;
        }

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

        .quality-high {
            background: rgba(34, 197, 94, 0.1);
            border-left: 4px solid #22c55e;
        }

        .quality-medium {
            background: rgba(234, 179, 8, 0.1);
            border-left: 4px solid #eab308;
        }

        .search-source {
            font-size: 0.7rem;
            color: #888;
            margin-top: 0.5rem;
        }

        .salary-info {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

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
        <p class="subtitle">🔍 Professional job search platform for students and graduates</p>
    </div>
""", unsafe_allow_html=True)

# Show search engines status
search_engines_status = "🔍 Active Search Engines: Tavily"
if serp_client:
    search_engines_status += " + SerpAPI"

st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background: rgba(40, 40, 50, 0.3); border-radius: 10px;">
        <p style="color: #4ecdc4; margin: 0;">{search_engines_status}</p>
    </div>
""", unsafe_allow_html=True)

# --- Enhanced Filters ---
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
st.markdown("### ⚙️ Search Filters")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    job_types = st.multiselect(
        "💼 Job Types",
        ["Student", "Internship", "Part-time", "Graduate", "Entry Level", "Junior", "Co-op", "Freelance"],
        default=["Student", "Internship"]
    )
with col2:
    fields = st.multiselect(
        "💻 Fields",
        ["Software Engineer", "Data Scientist", "DevOps", "QA Engineer", "Product Manager", "UX/UI Designer",
         "Marketing", "Business Intelligence", "Cybersecurity", "Mobile Developer", "Full Stack"],
        default=["Software Engineer"]
    )
with col3:
    regions = st.multiselect(
        "📍 Regions",
        ["Tel Aviv", "Jerusalem", "Haifa", "Beer Sheva", "Herzliya", "Ra'anana", "Petah Tikva", "Netanya", "Remote",
         "All Israel"],
        default=["Tel Aviv", "All Israel"]
    )
with col4:
    search_depth = st.selectbox(
        "🔍 Search Depth",
        ["basic", "advanced"],
        index=1,
        help="Advanced search finds more results but takes longer"
    )
with col5:
    max_results = st.selectbox(
        "📊 Max Results",
        [10, 20, 30, 50],
        index=1,
        help="More results = longer search time"
    )

st.markdown('</div>', unsafe_allow_html=True)

# --- Enhanced Cache with TTL ---
if 'search_cache' not in st.session_state:
    st.session_state.search_cache = {}
if 'cache_timestamps' not in st.session_state:
    st.session_state.cache_timestamps = {}


def is_cache_valid(cache_key: str, ttl_hours: int = 1) -> bool:
    """Check if cache entry is still valid"""
    if cache_key not in st.session_state.cache_timestamps:
        return False

    cache_time = st.session_state.cache_timestamps[cache_key]
    return (datetime.now() - cache_time).total_seconds() < ttl_hours * 3600


# --- Enhanced Job Search Functions ---

class EnhancedJobSearchEngine:
    def __init__(self, tavily_client, serp_client=None):
        self.tavily_client = tavily_client
        self.serp_client = serp_client

        # Comprehensive Israeli job sites
        self.israeli_job_sites = [
            "jobmaster.co.il", "drushim.co.il", "alljobs.co.il", "jobinfo.co.il",
            "seek.co.il", "jobs.co.il", "glassdoor.co.il", "indeed.co.il",
            "jobnet.co.il", "joblookup.co.il", "jobiz.co.il"
        ]

        # International job sites
        self.intl_job_sites = [
            "linkedin.com", "glassdoor.com", "indeed.com", "stackoverflow.com/jobs",
            "wellfound.com", "startup-jobs.com", "jobstoday.world", "simplyhired.com"
        ]

        # Top Israeli tech companies for direct career page search
        self.israeli_tech_companies = [
            "mobileye.com", "wix.com", "monday.com", "paypal.com", "microsoft.com/en-il",
            "intel.com/content/www/us/en/jobs", "nvidia.com/en-us/about-nvidia/careers",
            "google.com/careers", "amazon.jobs", "meta.com/careers", "apple.com/careers",
            "salesforce.com/careers", "facebook.com/careers", "uber.com/careers",
            "airbnb.com/careers", "spotify.com/jobs", "dropbox.com/jobs",
            "fiverr.com/careers", "orclapex.com/careers", "cellebrite.com/careers",
            "ironnet.com/careers", "checkmarx.com/careers", "cyber-ark.com/careers",
            "guardicore.com/careers", "varonis.com/careers", "radware.com/careers"
        ]

    def safe_html_escape(self, text: str) -> str:
        """Safely escape HTML content"""
        if not text:
            return ""

        # Convert to string first
        text = str(text)

        # Remove or replace problematic characters
        text = re.sub(r'[<>"\']', ' ', text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Truncate if too long
        if len(text) > 500:
            text = text[:500] + "..."

        return text

    def extract_structured_data(self, url: str) -> Dict:
        """Extract structured job data using Tavily extract API"""
        try:
            response = self.tavily_client.extract(url=url)

            if response and 'results' in response:
                extracted_data = response['results'][0] if response['results'] else {}

                # Parse structured fields if available
                structured_info = {
                    'job_title': extracted_data.get('job_title', ''),
                    'company': extracted_data.get('company', ''),
                    'location': extracted_data.get('location', ''),
                    'date_posted': extracted_data.get('date_posted', ''),
                    'employment_type': extracted_data.get('employment_type', ''),
                    'salary_range': extracted_data.get('salary_range', ''),
                    'requirements': extracted_data.get('requirements', ''),
                    'description': extracted_data.get('description', ''),
                    'benefits': extracted_data.get('benefits', ''),
                    'industry': extracted_data.get('industry', ''),
                    'experience_level': extracted_data.get('experience_level', ''),
                    'remote_work': extracted_data.get('remote_work', False)
                }

                return structured_info

        except Exception as e:
            print(f"Extract API error for {url}: {e}")

        return {}

    def create_company_specific_queries(self, job_types: List[str], fields: List[str]) -> List[Dict]:
        """Create queries targeting specific company career pages"""
        company_queries = []

        # Hebrew terms for better local company search
        hebrew_terms = {
            "Student": "סטודנט",
            "Internship": "התמחות",
            "Software Engineer": "מהנדס תוכנה",
            "Data Scientist": "מדען נתונים",
            "DevOps": "דבאופס",
            "QA Engineer": "בודק תוכנה"
        }

        for company_domain in self.israeli_tech_companies[:10]:  # Limit to top companies
            for job_type in job_types[:2]:
                for field in fields[:2]:
                    # English queries
                    company_queries.extend([
                        {
                            "query": f'"{field}" "{job_type}" site:{company_domain} apply career',
                            "source": f"Company-{company_domain.split('.')[0]}",
                            "priority": 22,
                            "is_company_direct": True
                        },
                        {
                            "query": f'student intern "{field}" site:{company_domain} requirements',
                            "source": f"Company-{company_domain.split('.')[0]}",
                            "priority": 21,
                            "is_company_direct": True
                        }
                    ])

                    # Hebrew queries for Israeli companies
                    if any(israeli in company_domain for israeli in ['wix', 'monday', 'mobileye']):
                        hebrew_job = hebrew_terms.get(job_type, job_type)
                        hebrew_field = hebrew_terms.get(field, field)

                        company_queries.append({
                            "query": f'"{hebrew_field}" "{hebrew_job}" site:{company_domain} דרושים',
                            "source": f"Company-{company_domain.split('.')[0]}",
                            "priority": 20,
                            "is_company_direct": True
                        })

        return company_queries

    def create_comprehensive_queries(self, job_types: List[str], fields: List[str], regions: List[str]) -> List[Dict]:
        """Create comprehensive search queries including company-specific searches"""
        queries = []

        location_map = {
            "Tel Aviv": {"en": "Tel Aviv", "he": "תל אביב"},
            "Jerusalem": {"en": "Jerusalem", "he": "ירושלים"},
            "Haifa": {"en": "Haifa", "he": "חיפה"},
            "Beer Sheva": {"en": "Beer Sheva", "he": "באר שבע"},
            "Herzliya": {"en": "Herzliya", "he": "הרצליה"},
            "Ra'anana": {"en": "Ra'anana", "he": "רעננה"},
            "Petah Tikva": {"en": "Petah Tikva", "he": "פתח תקווה"},
            "Netanya": {"en": "Netanya", "he": "נתניה"},
            "Remote": {"en": "remote", "he": "מרחוק"},
            "All Israel": {"en": "Israel", "he": "ישראל"}
        }

        # Field translations for better Hebrew search
        field_translations = {
            "Software Engineer": "מהנדס תוכנה",
            "Data Scientist": "מדען נתונים",
            "DevOps": "דבאופס",
            "QA Engineer": "בודק תוכנה",
            "Product Manager": "מנהל מוצר",
            "UX/UI Designer": "מעצב UX/UI",
            "Full Stack": "מפתח פולסטאק"
        }

        # 1. Add company-specific queries (high priority)
        company_queries = self.create_company_specific_queries(job_types, fields)
        queries.extend(company_queries)

        # 2. Regular job site queries
        for job_type in job_types[:2]:
            for field in fields[:3]:
                for region in regions[:2]:
                    location_data = location_map.get(region, {"en": "Israel", "he": "ישראל"})
                    location_en = location_data["en"]
                    location_he = location_data["he"]
                    field_he = field_translations.get(field, field)

                    # High-priority LinkedIn queries
                    queries.extend([
                        {
                            "query": f'site:linkedin.com/jobs/view/ "{field}" "{job_type}" {location_en} requirements apply',
                            "source": "LinkedIn",
                            "priority": 20,
                            "needs_extraction": True
                        },
                        {
                            "query": f'inurl:linkedin.com/jobs/view "{field}" student {location_en} internship',
                            "source": "LinkedIn",
                            "priority": 18,
                            "needs_extraction": True
                        }
                    ])

                    # Israeli job sites - comprehensive coverage
                    for site in self.israeli_job_sites[:4]:
                        queries.extend([
                            {
                                "query": f'site:{site} "{field}" "{job_type}" {location_he} דרישות',
                                "source": f"Israeli-{site}",
                                "priority": 17,
                                "needs_extraction": True
                            },
                            {
                                "query": f'site:{site} "{field_he}" סטודנט {location_he}',
                                "source": f"Israeli-{site}",
                                "priority": 16,
                                "needs_extraction": True
                            }
                        ])

                    # Company career pages with better targeting
                    queries.extend([
                        {
                            "query": f'"{field}" "{job_type}" {location_en} inurl:careers "apply now" "requirements"',
                            "source": "Company Careers",
                            "priority": 15,
                            "needs_extraction": True
                        },
                        {
                            "query": f'hiring "{field}" {location_en} student intern "send cv" requirements',
                            "source": "Company Careers",
                            "priority": 14,
                            "needs_extraction": False
                        }
                    ])

        # Sort by priority and limit
        queries.sort(key=lambda x: x['priority'], reverse=True)
        return queries[:40]  # Increased for company queries

    def search_with_serpapi_enhanced(self, query: str, location: str = "Israel") -> List[Dict]:
        """Enhanced SerpAPI search with better error handling"""
        if not self.serp_client:
            return []

        results = []

        try:
            # Google Jobs search with more parameters
            jobs_params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "hl": "en",
                "gl": "il",
                "chips": "date_posted:today,date_posted:3days,date_posted:week"
            }

            jobs_search = serpapi.GoogleSearch(jobs_params)
            jobs_search.params_dict.update({"api_key": self.serp_client.params_dict["api_key"]})
            jobs_results = jobs_search.get_dict()

            if "jobs_results" in jobs_results:
                for job in jobs_results["jobs_results"][:15]:
                    apply_link = ""
                    if job.get("apply_options"):
                        apply_link = job["apply_options"][0].get("link", "")

                    # Build comprehensive description
                    description_parts = []
                    if job.get("description"):
                        description_parts.append(job["description"])
                    if job.get("company_name"):
                        description_parts.append(f"Company: {job['company_name']}")
                    if job.get("detected_extensions", {}).get("schedule_type"):
                        description_parts.append(f"Type: {job['detected_extensions']['schedule_type']}")

                    result = {
                        "title": job.get("title", ""),
                        "url": apply_link,
                        "content": " | ".join(description_parts),
                        "search_source": "SerpAPI",
                        "query_priority": 25,
                        "company": job.get("company_name", ""),
                        "location": job.get("location", ""),
                        "posted_date": job.get("detected_extensions", {}).get("posted_at", ""),
                        "salary_info": job.get("detected_extensions", {}).get("salary", ""),
                        "job_type": job.get("detected_extensions", {}).get("schedule_type", "")
                    }

                    if result["url"]:
                        results.append(result)

        except Exception as e:
            st.warning(f"Google Jobs search error: {e}")

        return results

    def is_high_quality_job(self, result: Dict) -> Tuple[bool, int, Dict]:
        """Enhanced job quality validation"""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()

        analysis = {
            'url_score': 0,
            'content_score': 0,
            'freshness_score': 0,
            'company_score': 0,
            'quality_indicators': [],
            'negative_indicators': []
        }

        # Skip obvious non-job pages
        skip_indicators = [
            '/search', '/browse', '/results', '?q=', 'search?', 'jobs?', '/categories',
            '/filters', 'page=', '/all-jobs', '/job-search', '/list', '/listing',
            'query=', 'keyword=', '/jobs-in', '/find-jobs'
        ]
        if any(indicator in url for indicator in skip_indicators):
            analysis['negative_indicators'].append('search_page')
            return False, 0, analysis

        # Skip expired/closed jobs - enhanced list
        dead_signs = [
            'no longer available', 'position filled', 'job expired', 'closed',
            'no longer accepting applications', 'application deadline passed',
            'position has been filled', 'this job is no longer active',
            'המשרה לא זמינה', 'המשרה נסגרה', 'לא פעיל', 'לא קיים',
            'המשרה מלאה', 'לא מקבלים מועמדויות', 'הגשת המועמדויות הסתיימה'
        ]
        if any(sign in title + content for sign in dead_signs):
            analysis['negative_indicators'].append('expired')
            return False, 0, analysis

        # Enhanced URL scoring
        url_scores = {
            'linkedin.com/jobs/view/': 20,
            'jobmaster.co.il/job/': 18,
            'drushim.co.il/job/': 18,
            'alljobs.co.il/job/': 16,
            'indeed.com/viewjob': 15,
            'glassdoor.com/job/': 15,
            'jobs.co.il/job/': 14,
            'seek.co.il/job/': 14,
            '/careers/': 12,
            '/jobs/': 10,
            '/position/': 10,
            '/opportunities/': 8
        }

        for indicator, score in url_scores.items():
            if indicator in url:
                analysis['url_score'] = max(analysis['url_score'], score)
                analysis['quality_indicators'].append(f'url_{indicator.replace("/", "_")}')
                break

        # Enhanced content analysis
        strong_job_indicators = {
            'requirements': 4, 'responsibilities': 4, 'qualifications': 3,
            'job description': 4, 'apply now': 5, 'send cv': 4,
            'דרישות': 4, 'תיאור התפקיד': 4, 'אחריות': 3,
            'הגש מועמדות': 5, 'שלח קורות חיים': 4,
            'we are looking for': 3, 'join our team': 3,
            'position available': 3, 'hiring': 3
        }

        for keyword, score in strong_job_indicators.items():
            if keyword in content:
                analysis['content_score'] += score
                analysis['quality_indicators'].append(f'content_{keyword.replace(" ", "_")}')

        # Company reputation boost
        reputable_companies = [
            'microsoft', 'google', 'amazon', 'meta', 'apple', 'intel', 'nvidia',
            'everysight', 'mobileye', 'wix', 'monday', 'paypal', 'salesforce'
        ]
        for company in reputable_companies:
            if company in content or company in title:
                analysis['company_score'] += 5
                analysis['quality_indicators'].append(f'company_{company}')
                break

        # Freshness indicators
        fresh_indicators = [
            'posted today', 'new', 'urgent', 'immediate', 'fresh', 'just posted',
            'פורסם היום', 'חדש', 'דחוף', 'זה עתה פורסם'
        ]
        for indicator in fresh_indicators:
            if indicator in content or indicator in title:
                analysis['freshness_score'] += 3
                analysis['quality_indicators'].append(f'fresh_{indicator.replace(" ", "_")}')

        # Skip generic titles
        generic_patterns = [
            'jobs in', 'search results', 'job search', 'find jobs',
            'career opportunities', 'job listings', 'employment opportunities'
        ]
        if any(pattern in title for pattern in generic_patterns):
            analysis['negative_indicators'].append('generic_title')
            return False, 0, analysis

        # Calculate total score
        total_score = (analysis['url_score'] + analysis['content_score'] +
                       analysis['freshness_score'] + analysis['company_score'])

        # Enhanced validation criteria
        has_good_url = analysis['url_score'] >= 8
        has_good_content = analysis['content_score'] >= 6
        is_valid = total_score >= 15 and has_good_url and has_good_content

        return is_valid, total_score, analysis

    def extract_comprehensive_job_info(self, result: Dict, analysis: Dict) -> Dict:
        """Extract comprehensive job information with better parsing"""
        title = result.get('title', 'Job Position')
        url = result.get('url', '')
        content = result.get('content', '')

        # Safe cleaning for all text fields
        title = self.safe_html_escape(title)
        content = self.safe_html_escape(content)

        # Enhanced company extraction
        company = "Unknown Company"
        domain = urlparse(url).netloc.lower()

        # First try to extract from content
        company_patterns = [
            r'(?:company|חברה):\s*([^|\n\r.]{2,50})',
            r'(?:at|ב)\s+([A-Z][a-zA-Z\s&]{2,30})',
            r'([A-Z][a-zA-Z\s&]{3,25})\s+(?:is hiring|מחפשת|דרושה)',
            r'join\s+([A-Z][a-zA-Z\s&]{3,25})',
            r'work\s+(?:at|with)\s+([A-Z][a-zA-Z\s&]{3,25})'
        ]

        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                potential_company = match.group(1).strip()
                if len(potential_company) > 2 and potential_company.lower() not in ['the', 'our', 'this', 'that']:
                    company = self.safe_html_escape(potential_company)
                    break

        # If still unknown, try URL and title
        if company == "Unknown Company":
            if 'linkedin.com' in domain:
                # Extract from LinkedIn URL pattern or title
                if ' at ' in title:
                    company = self.safe_html_escape(title.split(' at ')[-1].strip())
                elif 'company' in result:
                    company = self.safe_html_escape(result['company'])
            elif any(site in domain for site in ['jobmaster', 'drushim', 'alljobs']):
                # Try to extract from title
                title_patterns = [r'ב([^|]+)', r'at ([^|]+)', r'- ([^|]+)', r'@\s*([^|]+)']
                for pattern in title_patterns:
                    match = re.search(pattern, title)
                    if match:
                        company = self.safe_html_escape(match.group(1).strip())
                        break
            else:
                # Extract from domain
                domain_name = domain.replace('www.', '').split('.')[0]
                if domain_name not in ['linkedin', 'indeed', 'glassdoor', 'jobmaster']:
                    company = self.safe_html_escape(domain_name.title())

        # Clean title
        title = re.sub(r'\s*\|.*$', '', title)  # Remove everything after |
        title = re.sub(r'\s*-[^-]*$', '', title)  # Remove trailing - description
        title = title.strip()

        # Enhanced description extraction
        sentences = re.split(r'[.!?]', content)
        good_sentences = []

        # Filter and select best sentences
        skip_phrases = ['cookie', 'privacy', 'terms', 'website', 'browse', 'search']
        for sentence in sentences[:8]:
            sentence = sentence.strip()
            if (len(sentence) > 40 and len(sentence) < 300 and
                    not any(skip in sentence.lower() for skip in skip_phrases)):
                good_sentences.append(sentence)
            if len(good_sentences) >= 3:
                break

        description = '. '.join(good_sentences)
        if not description or len(description) < 80:
            # Fallback to truncated content
            description = content[:400] + "..." if len(content) > 400 else content

        # Enhanced tags extraction
        text_lower = (title + ' ' + content).lower()
        tags = []

        # Job type detection
        type_patterns = {
            'Student': ['student', 'סטודנט', 'undergraduate'],
            'Internship': ['intern', 'internship', 'סטאז', 'התמחות'],
            'Junior': ['junior', 'entry level', 'משרה ראשונה', 'beginning'],
            'Remote': ['remote', 'work from home', 'מרחוק', 'עבודה מהבית'],
            'Full-time': ['full time', 'full-time', 'משרה מלאה'],
            'Part-time': ['part time', 'part-time', 'משרה חלקית']
        }

        for tag, keywords in type_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)

        # Status indicators
        if any(word in text_lower for word in ['apply now', 'hiring now', 'urgent', 'דרוש עכשיו', 'דחוף']):
            tags.append('Active')

        if any(word in text_lower for word in ['new', 'fresh', 'posted today', 'חדש', 'פורסם היום']):
            tags.append('Fresh')

        # Platform tags
        if 'linkedin.com' in url:
            tags.append('LinkedIn')
        elif 'google' in result.get('search_source', '').lower():
            tags.append('Google Jobs')
        elif any(site in url for site in ['jobmaster', 'drushim', 'alljobs']):
            tags.append('Local')

        # Salary extraction with multiple patterns
        salary = None
        salary_patterns = [
            r'₪\s*(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,3}(?:,\d{3})*)\s*₪',
            r'salary.*?(\d{1,3}(?:,\d{3})*)',
            r'משכורת.*?(\d{1,3}(?:,\d{3})*)',
            r'\$(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,3}(?:,\d{3})*)\s*שקלים'
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                salary = match.group(1).replace(',', '')
                break

        return {
            'title': title,
            'url': url,
            'content': description,
            'company': company,
            'tags': tags[:8],
            'salary': salary,
            'posted_date': result.get('posted_date'),
            'location': result.get('location'),
            'quality_indicators': analysis.get('quality_indicators', []),
            'search_source': result.get('search_source', 'Unknown')
        }

    def parallel_search_enhanced(self, queries: List[Dict]) -> List[Dict]:
        """Enhanced parallel search with extraction for high-quality jobs"""
        all_results = []
        results_for_extraction = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_query = {}

            # Submit Tavily searches
            for query_data in queries:
                cache_key = hashlib.md5(f"tavily_{query_data['query']}".encode()).hexdigest()

                if is_cache_valid(cache_key, ttl_hours=2):
                    cached_results = st.session_state.search_cache[cache_key]
                    all_results.extend(cached_results)
                else:
                    future = executor.submit(self.search_with_tavily_sync, query_data)
                    future_to_query[future] = ("tavily", query_data, cache_key)

            # Submit SerpAPI searches if available
            if self.serp_client:
                unique_search_terms = set()
                for query_data in queries[:10]:
                    search_term = self.extract_search_term(query_data['query'])
                    if search_term not in unique_search_terms:
                        unique_search_terms.add(search_term)

                        cache_key = hashlib.md5(f"serp_{search_term}".encode()).hexdigest()
                        if is_cache_valid(cache_key, ttl_hours=2):
                            cached_results = st.session_state.search_cache[cache_key]
                            all_results.extend(cached_results)
                        else:
                            future = executor.submit(self.search_with_serpapi_enhanced, search_term, "Israel")
                            future_to_query[future] = ("serp", {"query": search_term}, cache_key)

            # Collect results
            for future in concurrent.futures.as_completed(future_to_query):
                search_type, query_data, cache_key = future_to_query[future]
                try:
                    results = future.result(timeout=15)
                    if results:
                        # Mark results that need extraction
                        for result in results:
                            if query_data.get('needs_extraction', False):
                                result['needs_extraction'] = True
                            if query_data.get('is_company_direct', False):
                                result['is_company_direct'] = True

                        all_results.extend(results)

                        # Cache results
                        st.session_state.search_cache[cache_key] = results
                        st.session_state.cache_timestamps[cache_key] = datetime.now()

                except Exception as e:
                    print(f"{search_type} search failed: {e}")
                    continue

        # Phase 2: Extract structured data for high-quality results
        high_quality_results = []
        extraction_futures = {}

        # Filter results that need extraction
        for result in all_results:
            is_valid, quality_score, analysis = self.is_high_quality_job(result)
            if is_valid and quality_score >= 18 and result.get('needs_extraction', False):
                results_for_extraction.append((result, quality_score, analysis))

        # Sort and limit extraction candidates
        results_for_extraction.sort(key=lambda x: x[1], reverse=True)
        extraction_candidates = results_for_extraction[:10]  # Extract only top 10

        if extraction_candidates:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as extract_executor:
                for result, quality_score, analysis in extraction_candidates:
                    url = result.get('url', '')
                    if url:
                        cache_key = hashlib.md5(f"extract_{url}".encode()).hexdigest()

                        if is_cache_valid(cache_key, ttl_hours=6):  # Cache extractions longer
                            cached_extraction = st.session_state.search_cache[cache_key]
                            result['extracted_data'] = cached_extraction
                            result['quality_score'] = quality_score
                            result['analysis'] = analysis
                            high_quality_results.append(result)
                        else:
                            future = extract_executor.submit(self.extract_structured_data, url)
                            extraction_futures[future] = (result, quality_score, analysis, cache_key)

                # Collect extraction results
                for future in concurrent.futures.as_completed(extraction_futures):
                    result, quality_score, analysis, cache_key = extraction_futures[future]
                    try:
                        extracted_data = future.result(timeout=10)
                        result['extracted_data'] = extracted_data
                        result['quality_score'] = quality_score
                        result['analysis'] = analysis

                        # Cache extraction
                        st.session_state.search_cache[cache_key] = extracted_data
                        st.session_state.cache_timestamps[cache_key] = datetime.now()

                        high_quality_results.append(result)

                    except Exception as e:
                        print(f"Extraction failed: {e}")
                        # Add without extraction
                        result['extracted_data'] = {}
                        result['quality_score'] = quality_score
                        result['analysis'] = analysis
                        high_quality_results.append(result)

        # Add remaining results without extraction
        remaining_results = []
        processed_urls = set(r.get('url', '') for r in high_quality_results)

        for result in all_results:
            url = result.get('url', '')
            if url not in processed_urls:
                is_valid, quality_score, analysis = self.is_high_quality_job(result)
                if is_valid:
                    result['extracted_data'] = {}
                    result['quality_score'] = quality_score
                    result['analysis'] = analysis
                    remaining_results.append(result)

        return high_quality_results + remaining_results

    def extract_search_term(self, query: str) -> str:
        """Extract main search term from complex query"""
        # Remove site: and other operators
        clean_query = re.sub(r'site:\S+', '', query)
        clean_query = re.sub(r'inurl:\S+', '', clean_query)
        clean_query = re.sub(r'"([^"]*)"', r'\1', clean_query)  # Remove quotes
        clean_query = ' '.join(clean_query.split())  # Normalize spaces
        return clean_query[:100]  # Limit length

    def search_with_tavily_sync(self, query_data: Dict) -> List[Dict]:
        """Synchronous Tavily search for ThreadPoolExecutor"""
        try:
            response = self.tavily_client.search(
                query=query_data['query'],
                search_depth="advanced",
                max_results=12,  # Increased for better coverage
                include_raw_content=True
            )
            results = response.get("results", [])

            for result in results:
                result['search_source'] = query_data['source']
                result['query_priority'] = query_data['priority']

            return results
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []


# Initialize enhanced search engine
search_engine = EnhancedJobSearchEngine(client, serp_client)


def search_jobs_comprehensive(job_types: List[str], fields: List[str], regions: List[str],
                              search_depth: str = "advanced", max_results: int = 20) -> List[Dict]:
    """Comprehensive job search with enhanced processing"""

    progress_text = st.empty()
    progress_bar = st.progress(0.0)

    try:
        progress_text.text("🔧 Initializing comprehensive search...")
        progress_bar.progress(0.05)

        # Test connection
        test_response = client.search(query="test job", max_results=1)
        if not test_response:
            raise Exception("Search service not responding")

        progress_text.text("🎯 Creating comprehensive query strategy...")
        progress_bar.progress(0.15)

        queries = search_engine.create_comprehensive_queries(job_types, fields, regions)

        progress_text.text(f"🔍 Executing {len(queries)} targeted searches...")
        if search_engine.serp_client:
            progress_text.text(f"🔍 Multi-engine search: Tavily + SerpAPI ({len(queries)} queries)")
        progress_bar.progress(0.25)

        progress_text.text("🧠 Analyzing, extracting structured data, and filtering results...")

        # Execute searches with extraction
        all_results = search_engine.parallel_search_enhanced(queries)

        progress_bar.progress(0.70)
        progress_text.text("🧠 Processing and ranking enhanced job data...")

        # Process and validate results
        processed_jobs = []
        seen_urls = set()

        for result in all_results:
            url = result.get('url', '')
            if not url or url in seen_urls:
                continue

            # Skip obvious non-job content
            title_lower = result.get('title', '').lower()
            if any(skip in title_lower for skip in
                   ['search results', 'jobs in', 'find jobs', 'job listings', 'browse jobs']):
                continue

            # Result already has quality score and analysis from parallel_search_enhanced
            quality_score = result.get('quality_score', 0)
            analysis = result.get('analysis', {})

            if quality_score < 12:
                continue

            seen_urls.add(url)
            job_data = search_engine.extract_comprehensive_job_info(result, analysis)
            job_data['quality_score'] = quality_score
            job_data['analysis'] = analysis

            processed_jobs.append(job_data)

        progress_text.text("🎯 Ranking and optimizing results...")
        progress_bar.progress(0.90)

        # Enhanced sorting algorithm with structured data boost
        def comprehensive_sort_key(job):
            score = job['quality_score']

            # Major boosts
            if job.get('has_structured_data'):
                score += 10  # Structured data available
            if job.get('is_company_direct'):
                score += 8  # Direct from company
            if any('Active' in tag for tag in job['tags']):
                score += 6  # Active jobs
            if any('Fresh' in tag for tag in job['tags']):
                score += 5  # Fresh jobs
            if job.get('search_source') == 'SerpAPI':
                score += 4  # SerpAPI results
            if any('LinkedIn' in tag for tag in job['tags']):
                score += 3  # LinkedIn
            if job.get('salary_range'):
                score += 3  # Has salary info

            # Company reputation boost
            company_lower = job['company'].lower()
            if any(rep_company in company_lower for rep_company in
                   ['microsoft', 'google', 'amazon', 'apple', 'intel', 'nvidia', 'mobileye', 'wix', 'monday']):
                score += 12

            return score

        processed_jobs.sort(key=comprehensive_sort_key, reverse=True)

        progress_text.text("✅ Search completed successfully!")
        progress_bar.progress(1.0)

        time.sleep(0.5)
        progress_text.empty()
        progress_bar.empty()

        return processed_jobs[:max_results]

    except Exception as e:
        progress_text.empty()
        progress_bar.empty()
        st.error(f"Comprehensive search failed: {str(e)}")
        return []


def show_comprehensive_results(results: List[Dict]):
    """Display comprehensive job results using pure Streamlit components"""
    if not results:
        st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #b8b8b8;">
                <h3>🔍 No Job Postings Found</h3>
                <p>Try expanding your search criteria or different keywords</p>
                <small>💡 Tip: Try broader job types or include more regions</small>
            </div>
        """, unsafe_allow_html=True)
        return

    # Professional statistics
    stats = {
        'total': len(results),
        'active': len([r for r in results if any('Active' in tag for tag in r['tags'])]),
        'fresh': len([r for r in results if any('Fresh' in tag for tag in r['tags'])]),
        'linkedin': len([r for r in results if any('LinkedIn' in tag for tag in r['tags'])]),
        'companies': len(set(r['company'] for r in results if r['company'] != 'Unknown Company'))
    }

    # Stats display using columns
    st.markdown("### 📊 Search Results Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Jobs", stats['total'])
    with col2:
        st.metric("Active", stats['active'])
    with col3:
        st.metric("Fresh", stats['fresh'])
    with col4:
        st.metric("LinkedIn", stats['linkedin'])
    with col5:
        st.metric("Companies", stats['companies'])

    st.markdown("---")

    # Display each job using pure Streamlit components
    for i, job in enumerate(results, 1):
        # Create container for each job
        with st.container():
            # Quality indicator
            quality_color = "🟢" if job['quality_score'] >= 25 else "🟡" if job['quality_score'] >= 18 else "🔴"

            # Main job info
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"## {quality_color} {job['title']}")
                st.markdown(f"**🏢 Company:** {job['company']}")

            with col2:
                st.metric("Quality Score", job['quality_score'])

            # Job description
            st.markdown("**📝 Description:**")
            st.write(job['content'])

            # Tags display
            if job['tags']:
                st.markdown("**🏷️ Tags:**")
                tag_cols = st.columns(min(len(job['tags']), 6))
                for idx, tag in enumerate(job['tags'][:6]):
                    with tag_cols[idx]:
                        if 'Active' in tag:
                            st.success(f"🟢 {tag}")
                        elif 'Fresh' in tag:
                            st.info(f"🆕 {tag}")
                        else:
                            st.write(f"🔖 {tag}")

            # Additional info
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                if job.get('location'):
                    st.write(f"📍 **Location:** {job['location']}")
            with info_col2:
                if job.get('posted_date'):
                    st.write(f"📅 **Posted:** {job['posted_date']}")

            # Action buttons
            button_col1, button_col2, button_col3 = st.columns([2, 2, 2])

            with button_col1:
                st.link_button("🚀 Apply Now", job['url'])

            with button_col2:
                if st.button("📋 Copy Link", key=f"copy_{i}"):
                    st.success("Link ready to copy!")
                    st.code(job['url'])

            with button_col3:
                st.caption(f"🔍 Source: {job['search_source']}")

            # Separator
            st.markdown("---")


# --- Enhanced Search Interface ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if not job_types:
        st.warning("⚠️ Please select at least one job type")
    elif not fields:
        st.warning("⚠️ Please select at least one field")
    elif not regions:
        st.warning("⚠️ Please select at least one region")
    elif st.button("🚀 Search Jobs", type="primary", use_container_width=True):
        start_time = time.time()

        # Periodic cache cleanup
        if len(st.session_state.search_cache) > 200:
            # Keep only recent entries
            cutoff_time = datetime.now() - timedelta(hours=6)
            keys_to_remove = [
                k for k, v in st.session_state.cache_timestamps.items()
                if v < cutoff_time
            ]
            for key in keys_to_remove:
                st.session_state.search_cache.pop(key, None)
                st.session_state.cache_timestamps.pop(key, None)

        results = search_jobs_comprehensive(
            job_types=job_types,
            fields=fields,
            regions=regions,
            search_depth=search_depth,
            max_results=max_results
        )

        search_time = time.time() - start_time

        if results:
            quality_jobs = len([r for r in results if r['quality_score'] >= 20])
            st.success(f"🎉 Found {len(results)} job postings ({quality_jobs} high-quality) in {search_time:.1f}s")
        else:
            st.warning(f"❌ No results found in {search_time:.1f}s. Try broader criteria or different keywords.")

        show_comprehensive_results(results)

# --- Debug and Maintenance ---
with st.expander("🔧 Advanced Options & Debug"):
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ Clear Cache"):
            st.session_state.search_cache.clear()
            st.session_state.cache_timestamps.clear()
            st.success("Cache cleared!")

    with col2:
        cache_size = len(st.session_state.search_cache)
        st.info(f"📦 Cache entries: {cache_size}")

    with col3:
        if st.button("🧪 Test APIs"):
            test_results = {}

            # Test Tavily
            try:
                test_response = client.search(query="software engineer test", max_results=1)
                test_results["Tavily"] = "✅ Working" if test_response else "❌ Failed"
            except Exception as e:
                test_results["Tavily"] = f"❌ Error: {str(e)[:50]}"

            # Test SerpAPI
            if serp_client:
                try:
                    test_params = {"engine": "google", "q": "test", "num": 1}
                    test_search = serpapi.GoogleSearch(test_params)
                    test_search.params_dict.update({"api_key": serp_client.params_dict["api_key"]})
                    test_serp = test_search.get_dict()
                    test_results["SerpAPI"] = "✅ Working" if test_serp else "❌ Failed"
                except Exception as e:
                    test_results["SerpAPI"] = f"❌ Error: {str(e)[:50]}"
            else:
                test_results["SerpAPI"] = "⚠️ Not configured"

            for api, status in test_results.items():
                st.write(f"**{api}:** {status}")

# --- Footer ---
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem; margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
        <p>🎓 Student Job Finder v3.0 | 
        <span style="color: #4ecdc4;">Multi-Engine AI Search</span> | 
        Built by Gaya Gur</p>
    </div>
""", unsafe_allow_html=True)