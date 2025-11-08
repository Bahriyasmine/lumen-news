import json
import feedparser
import logging
import os
from datetime import datetime
from newspaper import Article as NewspaperArticle

from apps.scraper.utils.cleaner import clean_text
from apps.scraper.utils.api_fetcher import fetch_newsapi_articles

# ---------------------------
# 1️⃣ SETUP DIRECTORIES & LOGGING
# ---------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "logs", "scraper.log")
RSS_PATH = os.path.join(BASE_DIR, "feeds", "rss_sources.json")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------
# 2️⃣ LOAD RSS SOURCES
# ---------------------------

def load_sources():
    try:
        with open(RSS_PATH, "r", encoding="utf-8") as f:
            sources = json.load(f)
        logging.info("RSS sources loaded successfully.")
        return sources
    except Exception as e:
        logging.error(f"Error loading rss_sources.json: {e}")
        return {}

# ---------------------------
# 3️⃣ FETCH & CLEAN FULL ARTICLES
# ---------------------------

def fetch_full_article(url):
    try:
        article = NewspaperArticle(url)
        article.download()
        article.parse()
        return article.text.strip()
    except Exception as e:
        logging.warning(f"Failed to fetch article from {url}: {e}")
        return None

# ---------------------------
# 4️⃣ FETCH ARTICLES FROM RSS & API
# ---------------------------

def fetch_articles():
    """
    Returns a list of article dicts with keys:
    title, text, url, source, category, published_at
    """
    all_articles = []
    sources = load_sources()

    for category, feeds in sources.items():
        logging.info(f"Scraping category: {category}")
        for feed in feeds:
            source_name = feed.get("source")
            url = feed.get("url")
            try:
                parsed_feed = feedparser.parse(url)
                for entry in parsed_feed.entries:
                    link = entry.get("link", "")
                     # Extract summary if available
                    summary = entry.get("summary") or entry.get("description")
                    if not summary and "content" in entry:
                        summary = entry["content"][0].get("value") if entry["content"] else None
                    summary = clean_text(summary or "")

                    text = fetch_full_article(link) or summary
                    text = clean_text(text)
                    if not text:
                        continue

                    article = {
                        "title": entry.get("title", ""),
                        "text": text,
                        "url": link,
                        "source": source_name,
                        "summary": summary,
                        "category": category,
                        "published_at": entry.get("published", "")
                    }
                    all_articles.append(article)
            except Exception as e:
                logging.error(f"Error parsing feed {url}: {e}")

    # Fetch from NewsAPI
    api_articles = fetch_newsapi_articles()
    if api_articles:
        for a in api_articles:
            text = clean_text(a.get("content", ""))
            summary = clean_text(a.get("description", ""))  # Use description as summary
            if not text:
                continue
            a["text"] = text
            a["summary"] = summary
            all_articles.append(a)

    logging.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles
