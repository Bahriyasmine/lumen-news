# tasks.py
from celery import shared_task
from django.db import connection
from .scraper import fetch_articles
from .models import Article, ArticleEmbedding
from .utils.embeddings import get_embedding_batch
from dateutil.parser import parse as parse_date
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, time_limit=900, soft_time_limit=840)
def scrape_news_fast(self):
    """Scrape articles - fast, no embeddings"""
    logger.info("=== Starting fast news scraping ===")
    
    try:
        articles = fetch_articles()
        logger.info(f"📥 Fetched {len(articles)} articles")
    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        raise
    
    if not articles:
        return {"new": 0, "updated": 0}
    
    saved_count = 0
    updated_count = 0
    
    for i, a in enumerate(articles, start=1):
        title = a.get("title") or "[No title]"
        url = a.get("url")
        text = a.get("text") or ""
        category = a.get("category") or ""
        source = a.get("source") or ""
        summary = a.get("summary") or text[:300]
        published_at_raw = a.get("published_at")
        
        published_at = None
        if published_at_raw:
            try:
                published_at = parse_date(published_at_raw)
            except Exception:
                pass
        
        if not url:
            continue
        
        try:
            obj, created = Article.objects.update_or_create(
                url=url,
                defaults={
                    "title": title,
                    "text": text,
                    "category": category,
                    "source": source,
                    "summary": summary,
                    "published_at": published_at,
                    "status": "pending",
                }
            )
            
            if created:
                saved_count += 1
                logger.info(f"[{i}] ✅ NEW: {title[:60]}")
            else:
                updated_count += 1
        
        except Exception as e:
            logger.error(f"[{i}] ❌ Error: {e}")
    
    connection.close()
    
    logger.info(f"✅ Scraping complete: {saved_count} new, {updated_count} updated")
    
    return {
        "new": saved_count,
        "updated": updated_count,
        "total": len(articles)
    }


@shared_task(bind=True, time_limit=1800)
def generate_embeddings(self, batch_size=100):
    logger.info("=== Starting embedding generation ===")
    
    try:
        # Force queryset evaluation
        articles_without_embeddings = list(
            Article.objects.filter(embedding_data__isnull=True)
        )[:batch_size]

        count = len(articles_without_embeddings)
        if count == 0:
            logger.info("✅ All articles have embeddings")
            return {"processed": 0}
        
        logger.info(f"📝 Found {count} articles needing embeddings")
        
        # Collect texts
        texts_to_embed = []
        valid_articles = []

        for article in articles_without_embeddings:
            text = article.summary or article.text
            if text and len(text.strip()) >= 50:
                texts_to_embed.append(text)
                valid_articles.append(article)

        if not texts_to_embed:
            logger.info("No valid texts")
            return {"processed": 0}

        # Process in chunks
        chunk_size = 50
        processed = 0

        for i in range(0, len(texts_to_embed), chunk_size):
            chunk_texts = texts_to_embed[i:i + chunk_size]
            chunk_articles = valid_articles[i:i + chunk_size]

            logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk_texts)} articles)...")
            
            try:
                embeddings = get_embedding_batch(chunk_texts)
                if not embeddings or len(embeddings) != len(chunk_texts):
                    logger.error(f"Embedding mismatch")
                    continue
                
                # Use update_or_create to avoid conflicts
                for article, emb in zip(chunk_articles, embeddings):
                    ArticleEmbedding.objects.update_or_create(
                        article=article,
                        defaults={"embedding": emb}
                    )
                    processed += 1

                logger.info(f"✅ Chunk complete: {len(embeddings)} saved")

            except Exception as e:
                logger.error(f"❌ Chunk failed: {e}", exc_info=True)
                continue
        
        connection.close()
        remaining = Article.objects.filter(embedding_data__isnull=True).count()
        logger.info(f"✅ Processed {processed} embeddings, {remaining} remaining")
        return {"processed": processed, "remaining": remaining}

    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        connection.close()
        raise




@shared_task
def search_similar_articles(query_text, k=10):
    """Search for similar articles using embeddings"""
    from .utils.embeddings import get_embedding
    
    # Generate embedding for query
    query_embedding = get_embedding(query_text)
    
    if not query_embedding:
        return []
    
    # Use pgvector's similarity search (cosine distance)
    similar = ArticleEmbedding.objects.order_by(
        ArticleEmbedding.embedding.cosine_distance(query_embedding)
    )[:k]
    
    results = []
    for emb_obj in similar:
        article = emb_obj.article
        results.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "summary": article.summary[:200],
        })
    
    return results