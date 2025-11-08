# test_scraper.py (anywhere in your project, e.g., inside scraper/)

from scraper import fetch_articles

def test_scraper():
    articles = fetch_articles()
    print(f"Total articles fetched: {len(articles)}\n")
    
    # Print first 5 articles as a quick check
    for i, article in enumerate(articles[:5], start=1):
        print(f"Article {i}:")
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Category: {article['category']}")
        print(f"URL: {article['url']}")
        print(f"Text snippet: {article['text'][:200]}...\n")
    
    return articles

if __name__ == "__main__":
    test_scraper()
