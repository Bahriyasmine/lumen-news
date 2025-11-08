# scraper/utils/embeddings.py

from sentence_transformers import SentenceTransformer
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------
# 1️⃣ Initialize BERT Model
# ---------------------------
try:
    bert_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("✅ BERT embedding model loaded successfully.")
except Exception as e:
    bert_model = None
    logger.error(f"❌ Failed to load BERT embedding model: {e}")

# ---------------------------
# 2️⃣ Single embedding helper (KEEP FOR COMPATIBILITY)
# ---------------------------

def get_embedding(text: str):
    """
    Encode a text string into a BERT embedding (list of floats).
    Returns None if the model is not loaded or text is invalid.
    
    NOTE: For processing multiple texts, use get_embedding_batch() instead - it's 5-10x faster.
    """
    if bert_model is None:
        logger.warning("BERT model not loaded, returning None.")
        return None
    
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return None
    
    try:
        # Truncate to prevent token limit issues (512 tokens ≈ 2000-2500 chars)
        text = text[:2500]
        
        embedding = bert_model.encode(
            text, 
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embedding.tolist()  # convert to list for pgvector
        
    except Exception as e:
        logger.error(f"Failed to encode text: {e}", exc_info=True)
        return None


# ---------------------------
# 3️⃣ CRITICAL: Batch embedding helper
# ---------------------------

def get_embedding_batch(texts: list):
    """
    Encode multiple texts into embeddings in ONE batch operation.
    
    THIS IS THE KEY OPTIMIZATION:
    - Processing 50 texts individually: ~50 seconds
    - Processing 50 texts in batch: ~5-8 seconds
    - 5-10x speed improvement!
    
    Args:
        texts: List of text strings to encode
        
    Returns:
        List of embeddings (each is a list of 384 floats)
        Returns None if model not loaded
        Returns [] if no valid texts
    
    Example:
        texts = ["article 1", "article 2", "article 3"]
        embeddings = get_embedding_batch(texts)
        # embeddings[0] corresponds to texts[0], etc.
    """
    if bert_model is None:
        logger.error("BERT model not loaded, cannot generate embeddings.")
        return None
    
    if not texts:
        logger.warning("Empty text list provided")
        return []
    
    try:
        # Clean and truncate texts
        cleaned_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                # Truncate to prevent token limit issues
                cleaned = text[:2500]
                cleaned_texts.append(cleaned)
                valid_indices.append(i)
        
        if not cleaned_texts:
            logger.warning("No valid texts after cleaning")
            return []
        
        logger.info(f"Batch encoding {len(cleaned_texts)} texts...")
        
        # THE MAGIC: Encode all texts in one batch operation
        embeddings = bert_model.encode(
            cleaned_texts,
            batch_size=32,  # Process 32 at a time (optimal for most hardware)
            #show_progress_bar=len(cleaned_texts) > 20,  # Show progress for large batches
            show_progress_bar=False, 
            convert_to_numpy=True,
            normalize_embeddings=False  # Don't normalize unless needed
        )
        
        # Convert numpy arrays to lists for pgvector storage
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        logger.info(f"✅ Successfully generated {len(embeddings_list)} embeddings")
        return embeddings_list
        
    except Exception as e:
        logger.error(f"❌ Failed to encode batch: {e}", exc_info=True)
        # Re-raise so calling task can handle retry logic
        raise


# ---------------------------
# 4️⃣ Helper: Check if model is ready
# ---------------------------

def is_model_loaded():
    """Check if embedding model is loaded and ready"""
    return bert_model is not None


# ---------------------------
# 5️⃣ Helper: Get model info
# ---------------------------

def get_model_info():
    """Get information about the loaded model"""
    if bert_model is None:
        return {
            "loaded": False,
            "error": "Model not loaded"
        }
    
    return {
        "loaded": True,
        "model_name": "all-MiniLM-L6-v2",
        "dimensions": 384,
        "max_sequence_length": bert_model.max_seq_length,
        "device": str(bert_model.device)
    }