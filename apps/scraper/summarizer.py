import torch
from transformers import BartForConditionalGeneration, BartTokenizer
from apps.scraper.models import Article


def chunk_text_chars(text, tokenizer, max_chars=1000):
    chunks = []
    for i in range(0, len(text), max_chars):
        chunk = text[i:i + max_chars]
        tokens = tokenizer(chunk, add_special_tokens=False, return_tensors="pt")["input_ids"][0]
        if len(tokens) <= 1024:
            chunks.append(chunk)
        else:
            trimmed_chunk = chunk[:max_chars]
            last_space = trimmed_chunk.rfind(' ')
            if last_space > 0:
                trimmed_chunk = trimmed_chunk[:last_space]
            chunks.append(trimmed_chunk)
    return chunks


def summarize_text(text, model, tokenizer, max_total_chars=400, device="cpu"):
    chunks = chunk_text_chars(text, tokenizer, max_chars=1000)
    summaries = []
    max_chars_per_chunk = max_total_chars // max(1, len(chunks)) if chunks else 50
    max_tokens_per_chunk = max_chars_per_chunk // 4 + 5
    for chunk in chunks:
        inputs = tokenizer(chunk, max_length=1024, truncation=True, return_tensors="pt").to(device)
        summary_ids = model.generate(**inputs, max_length=max_tokens_per_chunk, num_beams=4, early_stopping=True)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append(summary)
    return " ".join(summaries)


def summarize_article_by_id(article_id):
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        print(f"❌ Article with id {article_id} not found.")
        return None

    if article.summary:
        return article.summary

    # Generate summary...
    summary = summarize_text(article.text, model, tokenizer)
    article.summary = summary
    article.save()
    return summary

# def summarize_all_articles(limit=5):
#     """Summarize all articles that don't yet have summaries."""
#     tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
#     model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn").to("cpu")

#     articles = Article.objects.filter(summary__isnull=True)[:limit]
#     for article in articles:
#         print(f"📰 Summarizing {article.title[:60]}...")
#         summary = summarize_text(article.text, model, tokenizer)
#         article.summary = summary
#         article.save()
#         print(f"✅ Saved summary for: {article.title}")
