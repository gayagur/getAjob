# utils/search_engine.py
import re
import hashlib
from datetime import datetime
import concurrent.futures
import streamlit as st
from tavily import TavilyClient

class JobSearchEngine:
    def __init__(self):
        self.client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

    def search(self, filters):
        queries = self.build_queries(filters)
        all_results = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_query = {executor.submit(self.client.search, query=q, max_results=10): q for q in queries}
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    response = future.result()
                    results = response.get("results", [])
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error fetching search results: {e}")

        jobs = self.clean_and_rank(all_results)
        return jobs

    def build_queries(self, filters):
        base_queries = []
        for job_type in filters["job_types"]:
            for field in filters["fields"]:
                for region in filters["regions"]:
                    base_queries.append(f"{job_type} {field} {region} site:linkedin.com OR site:alljobs.co.il")
        return base_queries[:20]

    def clean_and_rank(self, results):
        unique_urls = set()
        ranked = []
        for r in results:
            url = r.get("url")
            if not url or url in unique_urls:
                continue
            unique_urls.add(url)
            content = re.sub(r'<[^>]+>', '', r.get("content", ""))
            score = self.score_job(content)
            ranked.append({
                "title": r.get("title", "Job"),
                "url": url,
                "company": r.get("source", "Unknown"),
                "content": content[:300] + "...",
                "score": score
            })
        return sorted(ranked, key=lambda x: x["score"], reverse=True)

    def score_job(self, content):
        keywords = ["apply", "responsibilities", "requirements", "join our team", "דרישות", "תיאור"]
        score = sum(1 for kw in keywords if kw.lower() in content.lower())
        return score
