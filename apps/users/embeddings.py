# apps/users/embeddings.py
import numpy as np
# Replace with your actual fine-tuned BERT model
# from apps.sentiment.bert_model import get_bert_model
from sentence_transformers import SentenceTransformer
from apps.users.models import UserPreference
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_user_embedding(text: str):
    """
    Generate 384-dim embedding using domain-specific fine-tuned BERT.
    In production, replace dummy with real model.
    """
    embedding = model.encode(text, normalize_embeddings=True).tolist()
    return embedding





