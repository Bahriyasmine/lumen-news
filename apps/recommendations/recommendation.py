import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch
from datetime import datetime
from apps.users.models import UserPreference
from apps.scraper.models import Article, ArticleEmbedding


# Load model once at import
DEVICE = "cpu"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)


def get_user_embedding(user_pref):
    """
    Compute a fallback embedding for a user if not stored in DB.
    Based on recent articles in preferred domains.
    """
    articles = Article.objects.filter(category__in=user_pref.domains)[:5]
    if not articles.exists():
        articles = Article.objects.all()[:5]

    embeddings = []
    for article in articles:
        text = article.text[:1000]
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(DEVICE)
        with torch.no_grad():
            outputs = model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        embeddings.append(emb)

    if not embeddings:
        return np.zeros(384)
    return np.mean(embeddings, axis=0)

def get_article_embedding(article_id):
    """
    Retrieve the embedding vector for a given Article ID.
    Returns a Python list of floats, or None if not found.
    """
    try:
        article_embedding = ArticleEmbedding.objects.get(article_id=article_id)
        return article_embedding.embedding  # This is a pgvector.Vector object (list-like)
    except ArticleEmbedding.DoesNotExist:
        print(f"⚠️ No embedding found for article_id={article_id}")
        return None


def generate_recommendations_for_user(user_id, top_n=20):
    """
    Generate personalized article recommendations for a given user from the database.
    """

    # Get user preferences
    try:
        user_pref = UserPreference.objects.get(
            user_profile__user_id=user_id
        )
    except UserPreference.DoesNotExist:
        raise ValueError(f"No preferences found for user ID {user_id}")

    domains = user_pref.domains or []
    mental_state = user_pref.mental_state or "neutral"
    min_sentiment = user_pref.min_sentiment or 0.5

    # Load articles
    articles = Article.objects.all()

    # Get user embedding (from DB or compute fallback)
    if user_pref.embedding is not None:
        user_embedding = np.array(user_pref.embedding, dtype=float)
    else:
        user_embedding = get_user_embedding(user_pref)

    recommendations = []

    for article in articles:
        # Skip articles if sentiment filter applies
        if mental_state == "stressed" and hasattr(article, "sentiment"):
            if article.sentiment is not None and article.sentiment < min_sentiment:
                continue

        # Use DB embedding if exists, otherwise compute
        article_embedding=get_article_embedding(article.id)
        if article_embedding is not None:
            article_emb = np.array(article_embedding, dtype=float)
        else:
            text = article.text[:1000]
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
                article_emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

        # Similarity
        emb_sim = cosine_similarity([user_embedding], [article_emb])[0][0]

        domain_score = 1.0 if article.category in domains else 0.2
        recency = np.exp(-((datetime.now().astimezone() - article.scraped_at).days / 30))
        sentiment_score = getattr(article, "sentiment", 0.5)

        # Weighted combination
        final_score = (
            0.50 * emb_sim +
            0.30 * domain_score +
            0.10 * recency +
            0.10 * sentiment_score
        )

        recommendations.append({
            "id": article.id,
            "title": article.title,
            "category": article.category,
            "domain": article.category,
            "score": round(final_score, 3),
            "sentiment": round(sentiment_score, 2),
            "scraped_at": article.scraped_at,
        })

    # Sort by score
    recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)[:]

    # Display for debugging
    print(f"\nRecommendations for user {user_id}")
    print("-" * 80)
    for rec in recommendations:
        print(f"[{rec['domain'].upper()}] {rec['title']} | Score: {rec['score']} | Sentiment: {rec['sentiment']}")

    return recommendations
