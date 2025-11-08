import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from apps.scraper.utils.cleaner import clean_text
from dotenv import load_dotenv

# load_dotenv(dotenv_path="apps/scraper/.env")

NEWSAPI_KEY = os.getenv("NEWS_API_KEY")
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/top-headlines"


def fetch_full_article_text(url):
    """Fetch and extract full article text from a URL."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text(strip=True) for p in paragraphs])
        return clean_text(text) if len(text) > 200 else None
    except Exception:
        return None


def fetch_newsapi_articles(categories=None, language="en"):
    """Fetch articles from NewsAPI + scrape full text and summary"""
    from logging import getLogger
    logger = getLogger(__name__)

    if categories is None:
        categories = ["politics", "technology", "health", "sports"]

    articles = []

    if not NEWSAPI_KEY:
        logger.error("❌ NEWSAPI_KEY not found in environment variables.")
        return articles

    for category in categories:
        params = {
            "apiKey": NEWSAPI_KEY,
            "category": category,
            "language": language,
            "pageSize": 10
        }
        logger.info(f"🔍 Fetching {category} news from NewsAPI...")

        try:
            response = requests.get(NEWSAPI_ENDPOINT, params=params)
            if response.status_code != 200:
                logger.warning(f"⚠️ NewsAPI returned status {response.status_code} for category '{category}'.")
                continue

            data = response.json()
            if not data.get("articles"):
                logger.info(f"ℹ️ No articles found for {category}.")
                continue

            for item in data["articles"]:
                url = item.get("url")
                title = clean_text(item.get("title", ""))
                source = item.get("source", {}).get("name", "Unknown")

                # Summary first
                summary = clean_text(item.get("description", "") or item.get("content", ""))

                # Then full article
                full_content = fetch_full_article_text(url)
                if not full_content:
                    full_content = summary
                if not full_content:
                    continue

                articles.append({
                    "source": source,
                    "title": title,
                    "summary": summary or "",  # new field
                    "content": full_content,
                    "text": full_content,  # for consistency
                    "url": url,
                    "published_at": item.get("publishedAt", datetime.utcnow().isoformat()),
                    "category": category
                })

            logger.info(f"✅ Collected {len(articles)} total articles so far (category: {category})")

        except Exception as e:
            logger.error(f"❌ Error fetching {category} news: {e}")

    return articles
