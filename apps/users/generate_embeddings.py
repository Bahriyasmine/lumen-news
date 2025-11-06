# # apps/users/generate_embeddings.py
# from sentence_transformers import SentenceTransformer
# from apps.recommendations.models import Article, ArticleEmbedding

# print("Loading model...")
# model = SentenceTransformer("all-MiniLM-L6-v2")

# count = 0
# total = Article.objects.count()
# print(f"Processing {total} articles...")

# for article in Article.objects.all():
#     # Skip if embedding already exists
#     if ArticleEmbedding.objects.filter(article=article).exists():
#         continue

#     # Generate embedding
#     text = (article.text or "").strip()
#     if not text:
#         print(f"Skipping article {article.id}: empty text")
#         continue

#     embedding = model.encode(text, normalize_embeddings=True).tolist()

#     # Save
#     ArticleEmbedding.objects.create(article=article, embedding=embedding)
#     count += 1

#     if count % 10 == 0:
#         print(f"Progress: {count}/{total} embedded")

# print(f"Done! Generated {count} new embeddings.")
# apps/users/generate_embeddings.py
from sentence_transformers import SentenceTransformer
from apps.users.models import UserPreference
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

count = 0
total = UserPreference.objects.count()
print(f"Processing {total} users...")

for pref in UserPreference.objects.all():
    # Skip if embedding already exists
    if pref.embedding:
        continue

    # Generate embedding from preferences_text
    text = (pref.preferences_text or "").strip()
    if not text:
        print(f"Skipping user {pref.id}: empty preferences_text")
        continue

    embedding = model.encode(text, normalize_embeddings=True).tolist()

    # Save
    pref.embedding = embedding
    pref.save()
    count += 1

    if count % 10 == 0:
        print(f"Progress: {count}/{total} embedded")

print(f"Done! Generated {count} new embeddings.")