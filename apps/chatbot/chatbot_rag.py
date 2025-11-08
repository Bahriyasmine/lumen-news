# # apps/chatbot/chatbot_rag.py - SIMPLIFIED VERSION

# from pathlib import Path
# from typing import List, Dict, Optional
# from datetime import datetime

# import psycopg
# from decouple import config
# from rank_bm25 import BM25Okapi

# from langchain_groq import ChatGroq
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema import Document
# from langchain_huggingface import HuggingFaceEmbeddings


# class LumenNewsRAG:
#     """
#     Simplified RAG Chatbot:
#     - Reads from YOUR specific database structure
#     - Uses scraper's pre-computed embeddings
#     - Hybrid search (BM25 + Semantic)
#     """

#     def __init__(self):
#         self.base_dir = Path(__file__).parent
#         self.audio_dir = self.base_dir / "audio_cache"
#         self.audio_dir.mkdir(exist_ok=True)

#         # Env
#         self.groq_api_key = config("GROQ_API_KEY", default="")
#         self.groq_model = config("GROQ_MODEL", default="llama-3.3-70b-versatile")
#         self.temperature = float(config("GROQ_TEMPERATURE", default="0.3"))

#         # PostgreSQL connection
#         self.pg_connection = self._build_pg_connection()

#         # Components
#         self.llm = None
#         self.embeddings = None
#         self.bm25 = None
#         self.documents: List[Document] = []
#         self.embedding_cache: Dict[str, List[float]] = {}

#         self._setup()

#     def _build_pg_connection(self) -> str:
#         user = config("POSTGRES_USER", default="postgres")
#         password = config("POSTGRES_PASSWORD", default="postgres")
#         host = config("POSTGRES_HOST", default="db")
#         port = config("POSTGRES_PORT", default="5432")
#         database = config("POSTGRES_DB", default="lumen_news")
#         return f"postgresql://{user}:{password}@{host}:{port}/{database}"

#     def _setup(self):
#         # Embeddings model (for encoding user QUESTIONS only)
#         self.embeddings = HuggingFaceEmbeddings(
#             model_name="sentence-transformers/all-MiniLM-L6-v2",
#             model_kwargs={"device": "cpu"},
#             encode_kwargs={"normalize_embeddings": True},
#         )

#         # Load articles + their embeddings from database
#         self.documents = self._load_news_from_database()

#         # Initialize BM25 for keyword search
#         self._initialize_bm25()

#     def _ensure_llm(self):
#         if self.llm is None:
#             if not self.groq_api_key:
#                 raise RuntimeError("GROQ_API_KEY is missing in .env file")
#             self.llm = ChatGroq(
#                 api_key=self.groq_api_key,
#                 model=self.groq_model,
#                 temperature=self.temperature,
#             )

#     # ==================== LOAD FROM DATABASE ====================

#     def _load_news_from_database(self) -> List[Document]:
#         """
#         Simple version - we KNOW your database structure!
#         No column detection needed.
#         """
#         try:
#             conn = psycopg.connect(self.pg_connection)
#             cur = conn.cursor()

#             # Check if table has data
#             cur.execute("SELECT COUNT(*) FROM scraper_article;")
#             if cur.fetchone()[0] == 0:
#                 cur.close()
#                 conn.close()
#                 print("⚠️ No articles in database")
#                 return []

#             # Simple SQL - we KNOW your column names!
#             sql = """
#                 SELECT 
#                     a.id,
#                     a.title,
#                     a.text,
#                     a.category,
#                     a.source,
#                     a.url,
#                     a.published_at,
#                     a.scraped_at,
#                     e.embedding
#                 FROM scraper_article a
#                 LEFT JOIN scraper_articleembedding e ON a.id = e.article_id
#                 WHERE a.text IS NOT NULL AND a.text <> ''
#                 ORDER BY a.published_at DESC NULLS LAST
#                 LIMIT 1000;
#             """

#             cur.execute(sql)
#             rows = cur.fetchall()

#             docs: List[Document] = []
#             for row in rows:
#                 article_id = str(row[0])
#                 title = (row[1] or "").strip()
#                 text = (row[2] or "").strip()
#                 category = (row[3] or "general").strip()
#                 source = (row[4] or "Unknown").strip()
#                 url = (row[5] or "").strip()
#                 published_at = row[6]
#                 scraped_at = row[7]
#                 embedding = row[8]  # From scraper

#                 # Store scraper's embedding
#                 if embedding:
#                     # Convert pgvector array to Python list of floats
#                     try:
#                         self.embedding_cache[article_id] = [float(x) for x in embedding]
#                     except (ValueError, TypeError) as e:
#                         print(f"⚠️ Skipping invalid embedding for article {article_id}: {e}")

#                 # Format date
#                 def fmt_date(dt):
#                     try:
#                         if isinstance(dt, str):
#                             return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%Y-%m-%d")
#                         return dt.strftime("%Y-%m-%d") if dt else "N/A"
#                     except:
#                         return "N/A"

#                 # Create document
#                 content = (
#                     f"Title: {title}\n"
#                     f"Category: {category}\n"
#                     f"Date: {fmt_date(published_at)}\n"
#                     f"Source: {source}\n"
#                     f"Content: {text}"
#                 )

#                 docs.append(
#                     Document(
#                         page_content=content,
#                         metadata={
#                             "id": article_id,
#                             "title": title,
#                             "category": category,
#                             "date": fmt_date(published_at),
#                             "source": source,
#                             "url": url,
#                         }
#                     )
#                 )

#             cur.close()
#             conn.close()

#             print(f"✅ Loaded {len(docs)} articles ({len(self.embedding_cache)} with embeddings)")
#             return docs

#         except Exception as e:
#             print(f"❌ Database error: {e}")
#             return []

#     # ==================== SEARCH ====================

#     def _initialize_bm25(self):
#         """Keyword search (finds exact words like "Apple", "iPhone")"""
#         if not self.documents:
#             self.bm25 = None
#             return
#         tokenized = [d.page_content.lower().split() for d in self.documents]
#         self.bm25 = BM25Okapi(tokenized)

#     def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
#         """Compare two vectors (how similar are they?)"""
#         import math
        
#         # Ensure both vectors are float arrays (fix type issues)
#         try:
#             vec1 = [float(x) for x in vec1]
#             vec2 = [float(x) for x in vec2]
#         except (ValueError, TypeError):
#             return 0.0
        
#         # Check same dimensions
#         if len(vec1) != len(vec2):
#             return 0.0
        
#         dot = sum(a * b for a, b in zip(vec1, vec2))
#         mag1 = math.sqrt(sum(a * a for a in vec1))
#         mag2 = math.sqrt(sum(b * b for b in vec2))
#         return dot / (mag1 * mag2) if mag1 and mag2 else 0.0

#     def _semantic_search(self, query: str, k: int = 3) -> List[Document]:
#         """
#         Meaning-based search using scraper's embeddings
#         Finds articles similar in MEANING, not just exact words
#         """
#         if not self.embedding_cache:
#             return []

#         # Convert user question to vector
#         query_vector = self.embeddings.embed_query(query)

#         # Compare with all article vectors (from scraper)
#         scores = []
#         for doc in self.documents:
#             doc_id = doc.metadata.get("id")
#             if doc_id in self.embedding_cache:
#                 article_vector = self.embedding_cache[doc_id]
#                 similarity = self._cosine_similarity(query_vector, article_vector)
#                 scores.append((similarity, doc))

#         # Return top matches
#         scores.sort(reverse=True)
#         return [doc for _, doc in scores[:k]]

#     def _hybrid_search(self, query: str, k: int = 3) -> List[Document]:
#         """
#         Combined search:
#         1. BM25 finds exact word matches
#         2. Semantic finds similar meanings
#         3. Merge results
#         """
#         results = []
#         seen = set()

#         # 1. Keyword search (BM25)
#         if self.bm25:
#             tokens = query.lower().split()
#             bm25_scores = self.bm25.get_scores(tokens)
#             top_indices = sorted(range(len(bm25_scores)), 
#                                key=lambda i: bm25_scores[i], 
#                                reverse=True)[:k]
            
#             for idx in top_indices:
#                 doc = self.documents[idx]
#                 doc_id = doc.metadata.get("id")
#                 if doc_id not in seen:
#                     results.append(doc)
#                     seen.add(doc_id)

#         # 2. Semantic search (embeddings)
#         semantic_results = self._semantic_search(query, k=k)
#         for doc in semantic_results:
#             doc_id = doc.metadata.get("id")
#             if doc_id not in seen:
#                 results.append(doc)
#                 seen.add(doc_id)

#         return results[:k]

#     def _detect_category(self, question: str) -> Optional[str]:
#         """Detect if question is about specific category"""
#         q = question.lower()
#         tech = ["tech", "ai", "artificial intelligence", "gpt", "openai", "apple", "quantum", "ar", "vr"]
#         health = ["health", "vaccine", "malaria", "cancer", "alzheimer", "medical", "who", "clinic"]
#         sports = ["sport", "football", "soccer", "nba", "olympic", "gymnast", "ballon", "fifa", "lebron", "biles", "messi"]
#         politics = ["politic", "un", "european union", "eu", "summit", "climate", "net-zero", "treaty", "cbdc", "alliance"]

#         def any_in(words): return any(w in q for w in words)
#         if any_in(tech): return "technology"
#         if any_in(health): return "health"
#         if any_in(sports): return "sports"
#         if any_in(politics): return "politics"
#         return None

#     def _latest_by_category(self, category: str, limit: int = 3) -> List[Document]:
#         """Get latest articles in a specific category"""
#         subset = [d for d in self.documents if (d.metadata.get("category") or "").lower() == category.lower()]

#         def parse_date(s):
#             try:
#                 return datetime.strptime(s, "%Y-%m-%d")
#             except:
#                 return datetime.min

#         subset.sort(key=lambda d: parse_date(d.metadata.get("date", "")), reverse=True)
#         return subset[:limit]

#     # ==================== CHAT ====================

#     def chat(self, user_question: str) -> Dict:
#         """Answer user questions using retrieved articles"""
#         self._ensure_llm()

#         q = user_question.strip()

#         if not self.documents:
#             return {
#                 "success": True,
#                 "response": "No articles in database yet. Please run the scraper first!",
#                 "sources": [],
#             }

#         # Find relevant articles (hybrid search)
#         relevant = self._hybrid_search(q, k=3)

#         # Category-specific boost
#         cat = self._detect_category(q)
#         if cat:
#             latest = self._latest_by_category(cat, limit=3)
#             seen = {d.metadata.get("id") for d in relevant}
#             for d in latest:
#                 if d.metadata.get("id") not in seen:
#                     relevant.append(d)
#                     seen.add(d.metadata.get("id"))

#         if not relevant:
#             return {
#                 "success": True,
#                 "response": "I don't have information about that in my current news database. Try asking about technology, health, politics, or sports.",
#                 "sources": [],
#             }

#         # Build context from articles
#         context_parts = []
#         for i, doc in enumerate(relevant[:3], 1):
#             m = doc.metadata
#             context_parts.append(
#                 f"[Article {i}]\n"
#                 f"Source: {m['source']}\n"
#                 f"Title: {m['title']}\n"
#                 f"Category: {m['category']}\n"
#                 f"Date: {m['date']}\n"
#                 f"Content: {doc.page_content}\n"
#             )
#         context = "\n\n".join(context_parts)

#         # Ask LLM
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", """You are an intelligent news assistant. Answer STRICTLY from the provided articles.

# STRICT RULES:
# 1. ONLY use information from the provided articles - never invent or assume.
# 2. ALWAYS cite sources naturally in your response (e.g., "According to Reuters..." or "The Guardian reports that...").
# 3. Include specific details: dates, names, numbers, locations when mentioned.
# 4. If the answer is not in the articles, clearly say: "I don't have information about that in my current news database."
# 5. Never make up or infer information not explicitly stated.
# 6. Be conversational but precise.
# 7. If multiple articles are relevant, synthesize information from 2–3 sources naturally.
# 8. When mentioning statistics or facts, reference the source.

# Available news articles:
# {context}"""),
#             ("human", "{question}"),
#         ])

#         chain = prompt | self.llm
#         response = chain.invoke({"context": context, "question": q})

#         # Return answer + sources
#         sources = [
#             {
#                 "title": d.metadata["title"],
#                 "category": d.metadata["category"],
#                 "date": d.metadata["date"],
#                 "source": d.metadata["source"],
#                 "url": d.metadata["url"],
#             }
#             for d in relevant[:3]
#         ]

#         return {
#             "success": True,
#             "response": response.content.strip(),
#             "sources": sources,
#         }

#     def refresh_articles(self):
#         """Reload articles and embeddings from database"""
#         self.documents = self._load_news_from_database()
#         self._initialize_bm25()
#         return len(self.documents)

#     # ==================== AUDIO (STT/TTS) ====================

#     def speech_to_text(self, audio_file_path: str) -> Dict:
#         """
#         Convert speech to text using Groq Whisper API
#         """
#         try:
#             from groq import Groq
            
#             if not self.groq_api_key:
#                 return {
#                     "success": False,
#                     "error": "GROQ_API_KEY not configured"
#                 }
            
#             client = Groq(api_key=self.groq_api_key)
            
#             with open(audio_file_path, "rb") as audio_file:
#                 transcription = client.audio.transcriptions.create(
#                     file=audio_file,
#                     model="whisper-large-v3",
#                     response_format="text"
#                 )
            
#             return {
#                 "success": True,
#                 "text": transcription
#             }
            
#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": str(e)
#             }

#     def text_to_speech(self, text: str, language: str = "en", slow: bool = False) -> Dict:
#         """
#         Convert text to speech using gTTS (used by /api/tts and chat_voice_api).
#         Accepts language and slow flags; falls back to English if the language code is unsupported.
#         Returns path to generated audio file.
#         """
#         try:
#             from gtts import gTTS
#             import uuid

#             # Guardrails
#             text = (text or "").strip()
#             if not text:
#                 return {"success": False, "error": "Empty text for TTS"}

#             # Ensure output folder exists
#             self.audio_dir.mkdir(parents=True, exist_ok=True)

#             # Unique filename
#             audio_filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
#             audio_path = self.audio_dir / audio_filename

#             # Try requested language, else fallback to 'en'
#             try:
#                 tts = gTTS(text=text, lang=(language or "en"), slow=bool(slow))
#                 tts.save(str(audio_path))
#             except ValueError:
#                 tts = gTTS(text=text, lang="en", slow=bool(slow))
#                 tts.save(str(audio_path))

#             return {
#                 "success": True,
#                 "audio_path": str(audio_path),
#                 "audio_filename": audio_filename
#             }

#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": str(e)
#             }

#     def get_stats(self) -> Dict:
#         """Get chatbot statistics"""
#         categories = {}
#         for d in self.documents:
#             cat = d.metadata.get("category", "unknown")
#             categories[cat] = categories.get(cat, 0) + 1

#         return {
#             "total_articles": len(self.documents),
#             "articles_with_embeddings": len(self.embedding_cache),
#             "categories": categories,
#             "model": self.groq_model,
#             "features": ["Real-time Database", "Hybrid Search", "Scraper Pre-computed Embeddings"],
#             "search_method": "hybrid (BM25 + semantic using scraper embeddings)",
#             "embedding_model": "all-MiniLM-L6-v2 (same as scraper)",
#             "status": "active" if self.documents else "empty",
#         }


# # Singleton instance
# _chatbot = None

# def get_chatbot():
#     global _chatbot
#     if _chatbot is None:
#         _chatbot = LumenNewsRAG()
#     return _chatbot




# apps/chatbot/chatbot_rag.py - LAZY LOADING VERSION

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Keep only basic imports at module level
import psycopg
from decouple import config

# REMOVE these from top - will load lazily:
# from rank_bm25 import BM25Okapi
# from langchain_groq import ChatGroq
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema import Document
# from langchain_huggingface import HuggingFaceEmbeddings


class LumenNewsRAG:
    """
    Simplified RAG Chatbot with LAZY LOADING
    """

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.audio_dir = self.base_dir / "audio_cache"
        self.audio_dir.mkdir(exist_ok=True)

        # Env
        self.groq_api_key = config("GROQ_API_KEY", default="")
        self.groq_model = config("GROQ_MODEL", default="llama-3.3-70b-versatile")
        self.temperature = float(config("GROQ_TEMPERATURE", default="0.3"))

        # PostgreSQL connection
        self.pg_connection = self._build_pg_connection()

        # Components - initialize as None, load lazily
        self.llm = None
        self.embeddings = None
        self.bm25 = None
        self.documents: List = []  # Changed from List[Document]
        self.embedding_cache: Dict[str, List[float]] = {}
        
        # Don't call _setup() here - it will be called lazily

    def _build_pg_connection(self) -> str:
        user = config("POSTGRES_USER", default="postgres")
        password = config("POSTGRES_PASSWORD", default="postgres")
        host = config("POSTGRES_HOST", default="db")
        port = config("POSTGRES_PORT", default="5432")
        database = config("POSTGRES_DB", default="lumen_news")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _ensure_setup(self):
        """Lazy initialization - only runs when chatbot is actually used"""
        if self.embeddings is not None:
            return  # Already initialized
        
        print("🔄 Initializing chatbot (lazy loading)...")
        
        # Import HERE, not at module level
        from langchain_huggingface import HuggingFaceEmbeddings
        
        # Embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Load articles
        self.documents = self._load_news_from_database()

        # Initialize BM25
        self._initialize_bm25()
        
        print("✅ Chatbot initialized!")

    def _ensure_llm(self):
        """Lazy load LLM"""
        if self.llm is not None:
            return
        
        from langchain_groq import ChatGroq
        
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is missing in .env file")
        
        self.llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.groq_model,
            temperature=self.temperature,
        )

    def _load_news_from_database(self) -> List:
        """Load articles - imports Document lazily"""
        from langchain_core.documents import Document  # Import here
        
        try:
            conn = psycopg.connect(self.pg_connection)
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM scraper_article;")
            if cur.fetchone()[0] == 0:
                cur.close()
                conn.close()
                print("⚠️ No articles in database")
                return []

            sql = """
                SELECT 
                    a.id, a.title, a.text, a.category, a.source,
                    a.url, a.published_at, a.scraped_at, e.embedding
                FROM scraper_article a
                LEFT JOIN scraper_articleembedding e ON a.id = e.article_id
                WHERE a.text IS NOT NULL AND a.text <> ''
                ORDER BY a.published_at DESC NULLS LAST
                LIMIT 1000;
            """

            cur.execute(sql)
            rows = cur.fetchall()

            docs: List = []
            for row in rows:
                article_id = str(row[0])
                title = (row[1] or "").strip()
                text = (row[2] or "").strip()
                category = (row[3] or "general").strip()
                source = (row[4] or "Unknown").strip()
                url = (row[5] or "").strip()
                published_at = row[6]
                scraped_at = row[7]
                embedding = row[8]

                if embedding:
                    try:
                        self.embedding_cache[article_id] = [float(x) for x in embedding]
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Invalid embedding for article {article_id}: {e}")

                def fmt_date(dt):
                    try:
                        if isinstance(dt, str):
                            return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                        return dt.strftime("%Y-%m-%d") if dt else "N/A"
                    except:
                        return "N/A"

                content = (
                    f"Title: {title}\n"
                    f"Category: {category}\n"
                    f"Date: {fmt_date(published_at)}\n"
                    f"Source: {source}\n"
                    f"Content: {text}"
                )

                docs.append(
                    Document(
                        page_content=content,
                        metadata={
                            "id": article_id,
                            "title": title,
                            "category": category,
                            "date": fmt_date(published_at),
                            "source": source,
                            "url": url,
                        }
                    )
                )

            cur.close()
            conn.close()

            print(f"✅ Loaded {len(docs)} articles ({len(self.embedding_cache)} with embeddings)")
            return docs

        except Exception as e:
            print(f"❌ Database error: {e}")
            return []

    def _initialize_bm25(self):
        """Lazy load BM25"""
        from rank_bm25 import BM25Okapi  # Import here
        
        if not self.documents:
            self.bm25 = None
            return
        tokenized = [d.page_content.lower().split() for d in self.documents]
        self.bm25 = BM25Okapi(tokenized)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        import math
        
        try:
            vec1 = [float(x) for x in vec1]
            vec2 = [float(x) for x in vec2]
        except (ValueError, TypeError):
            return 0.0
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        return dot / (mag1 * mag2) if mag1 and mag2 else 0.0

    def _semantic_search(self, query: str, k: int = 3) -> List:
        if not self.embedding_cache:
            return []

        query_vector = self.embeddings.embed_query(query)

        scores = []
        for doc in self.documents:
            doc_id = doc.metadata.get("id")
            if doc_id in self.embedding_cache:
                article_vector = self.embedding_cache[doc_id]
                similarity = self._cosine_similarity(query_vector, article_vector)
                scores.append((similarity, doc))

        scores.sort(reverse=True)
        return [doc for _, doc in scores[:k]]

    def _hybrid_search(self, query: str, k: int = 3) -> List:
        results = []
        seen = set()

        if self.bm25:
            tokens = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokens)
            top_indices = sorted(range(len(bm25_scores)), 
                               key=lambda i: bm25_scores[i], 
                               reverse=True)[:k]
            
            for idx in top_indices:
                doc = self.documents[idx]
                doc_id = doc.metadata.get("id")
                if doc_id not in seen:
                    results.append(doc)
                    seen.add(doc_id)

        semantic_results = self._semantic_search(query, k=k)
        for doc in semantic_results:
            doc_id = doc.metadata.get("id")
            if doc_id not in seen:
                results.append(doc)
                seen.add(doc_id)

        return results[:k]

    def _detect_category(self, question: str) -> Optional[str]:
        q = question.lower()
        tech = ["tech", "ai", "artificial intelligence", "gpt", "openai", "apple", "quantum"]
        health = ["health", "vaccine", "malaria", "cancer", "alzheimer", "medical"]
        sports = ["sport", "football", "soccer", "nba", "olympic", "gymnast"]
        politics = ["politic", "un", "european union", "summit", "climate", "treaty"]

        def any_in(words): return any(w in q for w in words)
        if any_in(tech): return "technology"
        if any_in(health): return "health"
        if any_in(sports): return "sports"
        if any_in(politics): return "politics"
        return None

    def _latest_by_category(self, category: str, limit: int = 3) -> List:
        subset = [d for d in self.documents if (d.metadata.get("category") or "").lower() == category.lower()]

        def parse_date(s):
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except:
                return datetime.min

        subset.sort(key=lambda d: parse_date(d.metadata.get("date", "")), reverse=True)
        return subset[:limit]

    def chat(self, user_question: str) -> Dict:
        """Answer user questions - lazy loads everything on first call"""
        # Ensure setup before chatting
        self._ensure_setup()
        self._ensure_llm()
        
        # Import prompt template lazily
        from langchain_core.prompts import ChatPromptTemplate

        q = user_question.strip()

        if not self.documents:
            return {
                "success": True,
                "response": "No articles in database yet. Please run the scraper first!",
                "sources": [],
            }

        relevant = self._hybrid_search(q, k=3)

        cat = self._detect_category(q)
        if cat:
            latest = self._latest_by_category(cat, limit=3)
            seen = {d.metadata.get("id") for d in relevant}
            for d in latest:
                if d.metadata.get("id") not in seen:
                    relevant.append(d)
                    seen.add(d.metadata.get("id"))

        if not relevant:
            return {
                "success": True,
                "response": "I don't have information about that in my current news database.",
                "sources": [],
            }

        context_parts = []
        for i, doc in enumerate(relevant[:3], 1):
            m = doc.metadata
            context_parts.append(
                f"[Article {i}]\n"
                f"Source: {m['source']}\n"
                f"Title: {m['title']}\n"
                f"Content: {doc.page_content}\n"
            )
        context = "\n\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent news assistant. Answer STRICTLY from the provided articles.
STRICT RULES:
1. ONLY use information from the provided articles.
2. ALWAYS cite sources naturally.
3. Include specific details when mentioned.
4. If answer not in articles, say so clearly.
5. Never make up information.

Available news articles:
{context}"""),
            ("human", "{question}"),
        ])

        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": q})

        sources = [
            {
                "title": d.metadata["title"],
                "category": d.metadata["category"],
                "date": d.metadata["date"],
                "source": d.metadata["source"],
                "url": d.metadata["url"],
            }
            for d in relevant[:3]
        ]

        return {
            "success": True,
            "response": response.content.strip(),
            "sources": sources,
        }

    def refresh_articles(self):
        """Reload articles"""
        self._ensure_setup()
        self.documents = self._load_news_from_database()
        self._initialize_bm25()
        return len(self.documents)

    def speech_to_text(self, audio_file_path: str) -> Dict:
        """Convert speech to text"""
        try:
            from groq import Groq  # Lazy import
            
            if not self.groq_api_key:
                return {"success": False, "error": "GROQ_API_KEY not configured"}
            
            client = Groq(api_key=self.groq_api_key)
            
            with open(audio_file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    response_format="text"
                )
            
            return {"success": True, "text": transcription}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def text_to_speech(self, text: str, language: str = "en", slow: bool = False) -> Dict:
        """Convert text to speech"""
        try:
            from gtts import gTTS  # Lazy import
            import uuid

            text = (text or "").strip()
            if not text:
                return {"success": False, "error": "Empty text"}

            self.audio_dir.mkdir(parents=True, exist_ok=True)

            audio_filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = self.audio_dir / audio_filename

            try:
                tts = gTTS(text=text, lang=(language or "en"), slow=bool(slow))
                tts.save(str(audio_path))
            except ValueError:
                tts = gTTS(text=text, lang="en", slow=bool(slow))
                tts.save(str(audio_path))

            return {
                "success": True,
                "audio_path": str(audio_path),
                "audio_filename": audio_filename
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict:
        """Get statistics - ensures setup first"""
        self._ensure_setup()
        
        categories = {}
        for d in self.documents:
            cat = d.metadata.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_articles": len(self.documents),
            "articles_with_embeddings": len(self.embedding_cache),
            "categories": categories,
            "model": self.groq_model,
            "status": "active" if self.documents else "empty",
        }


# Singleton with lazy initialization
_chatbot = None

def get_chatbot():
    """Get chatbot instance - creates on first call"""
    global _chatbot
    if _chatbot is None:
        print("🔄 Creating chatbot instance...")
        _chatbot = LumenNewsRAG()
        print("✅ Chatbot instance created (not yet initialized)")
    return _chatbot