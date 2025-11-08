import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # scraper/
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
JSON_PATH = os.path.join(DATA_DIR, "embeddings.jsonl")
