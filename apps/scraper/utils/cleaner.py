from bs4 import BeautifulSoup
import re

def clean_text(text: str) -> str:
    """Remove HTML tags, scripts, and normalize whitespace"""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
