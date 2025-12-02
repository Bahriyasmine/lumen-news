Lumen News – Real-Time AI News Platform
1. Overview

Lumen News is an end-to-end AI-driven news platform combining real-time scraping, semantic indexing, RAG-based question answering, automated debate agents for credibility analysis, multilingual summarization, translation, and personalized recommendations.
The entire system is orchestrated through Django REST Framework with PostgreSQL and pgvector.

2. Real-Time Scraping Pipeline

Automated ingestion system designed to collect and store fresh articles efficiently.

Features

Real-time scraping with scheduling and retry logic.

URL-based deduplication to prevent duplicates.

Extraction of: title, content, author, publication date, category.

Cleaning: removal of repeated text, ads, and HTML noise.

Automatic ingestion into PostgreSQL using Django ORM pipelines.

3. Large-Scale Vector Indexing (pgvector + BERT)

All articles are embedded to allow semantic retrieval.

Features

BERT embeddings computed for each article.

Storage of vectors in PostgreSQL using pgvector.

Fast semantic search using cosine similarity.

Hybrid indexing strategy allowing batch indexing for new articles.

4. Retrieval-Augmented Generation Chatbot (Llama 3.3 70B)

A custom RAG pipeline answering questions strictly from the stored articles.

Features

Hybrid search (BM25 + semantic search).

Top-k passage retrieval from PostgreSQL + pgvector.

Context construction optimized for Llama 3.3 70B – Versatile.

Answers grounded only on database content.

5. Automated Debate System (CrewAI)

A multi-agent system analyzing article credibility.

Agents

Defender Agent (Llama 3.1): defends the article’s claims.

Opposer Agent (Llama 3.3): challenges the article and exposes weak points.

Judge Agent: evaluates both sides and produces a credibility score or verdict.

Capabilities

Fake news detection through argumentation.

Multi-perspective analysis of controversial content.

Structured reasoning including claims, counterclaims, and evidence.

6. Summarization and Translation Pipeline

Efficient content generation to support multilingual access.

Features

Summaries generated using BART (facebook/bart-large-cnn).

High-quality translation (en → fr, en → ar) using Helsinki-NLP transformers.

Support for article previews, condensed summaries, and cross-language search.

7. Personalized Recommendation Engine

A recommendation pipeline built on user preferences and embedding similarity.

Features

Recommendations based on vector similarity between user history and new articles.

Integration of sentiment analysis to refine relevance.

Dynamic ranking model adapting to user interactions.

8. Full Backend Architecture (Django + PostgreSQL + pgvector)

A unified API orchestrating all modules.

Components

Django REST Framework for API endpoints.

PostgreSQL for relational storage.

pgvector for semantic indexing.

Integration of scraping, embeddings, RAG, debate, and recommendations into a single pipeline.
