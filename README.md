# 🎓 Student Job Finder

A lightning-fast, visually polished job search web app built with streamlit.  
Designed for students and junior developers in Israel, this app finds **real, direct job links** — not just job boards.

---

## 🚀 Live Demo

🌐 **Try it here → [getajob-gg.streamlit.app](https://getajob-gg.streamlit.app)**

---

## 🎯 Features

- 🔍 **Smart parallel job search** across major Israeli job platforms (JobMaster, LinkedIn, Drushim, AllJobs)
- 💡 **AI-powered content filtering** to show only real job postings (not category pages)
- 🌐 **Supports Hebrew and English**
- ⚙️ Filter by job type, field, and region
- 🎨 Stylish modern UI with dark mode and glowing buttons
- ⚡ Very fast results using `asyncio` + `ThreadPoolExecutor`

---

## 🧪 Technologies Used

- Python 3.10+
- Streamlit
- Tavily API (for AI-enhanced search and extraction)
- `aiohttp`, `requests`, `re`, `concurrent.futures`

---

## 🔐 Secrets

This app requires a `TAVILY_API_KEY` to work.  
You must add it via **Streamlit Cloud > Settings > Secrets**:

```toml
TAVILY_API_KEY = "your-api-key"
