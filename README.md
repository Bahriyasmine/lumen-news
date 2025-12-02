# Lumen News – Real-Time AI News Platform
Lumen News is an end-to-end AI-powered news platform that integrates real-time news scraping, large-scale vector indexing, retrieval-augmented question answering, automated debate agents for credibility analysis, multilingual summarization, translation, and personalized recommendations. The system is developed using Django REST Framework, PostgreSQL, and pgvector, providing a unified orchestration of scraping, embeddings, retrieval, debate, and recommendation modules.

## Real-Time Scraping Pipeline
The platform includes an automated scraping pipeline that continuously collects fresh articles. It performs URL-based deduplication to prevent storing duplicates, extracts key metadata (title, content, publish date, author, category), and applies text-cleaning procedures to remove noise such as repeated blocks, ads, or HTML artifacts. All validated articles are automatically ingested into PostgreSQL using Django ORM.

## Vector Indexing with BERT and pgvector
Each article is encoded using BERT embeddings and stored inside PostgreSQL using pgvector. This enables fast and accurate semantic search through cosine similarity. The embedding pipeline supports both real-time and batch indexing, ensuring scalability as the number of articles grows.

## Retrieval-Augmented Chatbot (Llama 3.3 70B)
The RAG chatbot answers user questions strictly using the articles stored in the database. It relies on hybrid retrieval that combines BM25 lexical search with pgvector semantic retrieval. Retrieved passages are used to build an optimized prompt for Llama 3.3 70B – Versatile, ensuring grounded responses that rely solely on stored information.

## Automated Debate System (CrewAI)
A multi-agent debate framework is integrated to evaluate article credibility.  
- The Defender Agent (Llama 3.1) argues in favor of the article.  
- The Opposer Agent (Llama 3.3) critiques the article and exposes weaknesses.  
- The Judge Agent synthesizes both viewpoints and provides a credibility verdict.

This system enables structured evaluation and supports detection of misinformation and biased content.

## Summarization and Translation Module
The platform provides automatic summarization using BART (facebook/bart-large-cnn) to generate concise article summaries. A translation module built on Helsinki-NLP models supports English-to-French and English-to-Arabic translations, enabling multilingual content accessibility.

## Personalized Recommendation Engine
User-specific recommendations are generated based on embedding similarity, interaction history, and sentiment analysis. The recommendation pipeline ranks articles dynamically to match user interests and reading patterns.

## Backend Architecture
The platform is fully implemented using Django REST Framework connected to PostgreSQL and pgvector. All functional components—scraping, embedding generation, RAG retrieval, debate processing, summarization, translation, and recommendations—are orchestrated through a single cohesive backend.
