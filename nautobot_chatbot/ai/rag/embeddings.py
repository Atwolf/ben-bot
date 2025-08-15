"""
Embedding generation for RAG system.
Supports multiple embedding providers with fallback options.
"""

# Standard library imports
import logging
import os
from typing import List, Optional

# Third-party imports
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """
    Handles text embedding generation for RAG retrieval.
    Supports multiple providers with automatic fallbacks.
    """

    def __init__(self):
        """Initialize the embedding provider with the best available option."""
        self.provider = None
        self.model = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the best available embedding provider."""

        # Try sentence-transformers first (free, local, no API key needed)
        try:
            # Third-party imports
            from sentence_transformers import SentenceTransformer

            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.model = SentenceTransformer(model_name)
            self.provider = "sentence-transformers"
            logger.info(f"Using sentence-transformers with model: {model_name}")
            return
        except ImportError:
            logger.warning(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize sentence-transformers: {e}")

        # Fallback to simple TF-IDF vectorization
        try:
            # Third-party imports
            from sklearn.feature_extraction.text import TfidfVectorizer

            self.model = TfidfVectorizer(
                max_features=384,  # Match typical embedding dimension
                stop_words="english",
                ngram_range=(1, 2),
            )
            self.provider = "tfidf"
            self._tfidf_fitted = False
            logger.info("Using TF-IDF embeddings as fallback")
            return
        except ImportError:
            logger.warning("scikit-learn not available. Install with: pip install scikit-learn")

        # Final fallback: simple word counting (very basic)
        self.provider = "simple"
        logger.warning("Using simple word-based embeddings (limited functionality)")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])

        try:
            if self.provider == "sentence-transformers":
                return self._encode_sentence_transformers(texts)
            elif self.provider == "tfidf":
                return self._encode_tfidf(texts)
            else:  # simple fallback
                return self._encode_simple(texts)

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return random embeddings as last resort
            return np.random.rand(len(texts), 384)

    def _encode_sentence_transformers(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using sentence-transformers."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def _encode_tfidf(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using TF-IDF vectorization."""
        if not hasattr(self, "_tfidf_fitted") or not self._tfidf_fitted:
            # First time: fit the vectorizer
            try:
                # Try to load pre-fitted vectorizer from previous documents
                embeddings = self.model.fit_transform(texts).toarray()
                self._tfidf_fitted = True
                return embeddings
            except Exception:
                # If fitting fails, return zero embeddings
                return np.zeros((len(texts), 384))
        else:
            # Transform new texts
            try:
                embeddings = self.model.transform(texts).toarray()
                # Pad or truncate to consistent size
                if embeddings.shape[1] < 384:
                    padding = np.zeros((embeddings.shape[0], 384 - embeddings.shape[1]))
                    embeddings = np.hstack([embeddings, padding])
                elif embeddings.shape[1] > 384:
                    embeddings = embeddings[:, :384]
                return embeddings
            except Exception:
                return np.zeros((len(texts), 384))

    def _encode_simple(self, texts: List[str]) -> np.ndarray:
        """Generate simple word-based embeddings as final fallback."""
        embeddings = []

        for text in texts:
            # Simple word frequency embedding
            words = text.lower().split()
            # Create a basic 384-dimensional vector based on word characteristics
            embedding = np.zeros(384)

            # Fill embedding with basic text features
            if words:
                # Word count features
                embedding[0] = len(words)
                embedding[1] = len(set(words))  # unique words
                embedding[2] = sum(len(word) for word in words) / len(words)  # avg word length

                # Character-based features
                text_lower = text.lower()
                embedding[3] = text_lower.count("nautobot")
                embedding[4] = text_lower.count("device")
                embedding[5] = text_lower.count("circuit")
                embedding[6] = text_lower.count("ip")
                embedding[7] = text_lower.count("api")

                # Fill remaining dimensions with word hash features
                for i, word in enumerate(words[:50]):  # Use first 50 words
                    if i + 8 < 384:
                        embedding[i + 8] = hash(word) % 1000 / 1000.0

            embeddings.append(embedding)

        return np.array(embeddings)

    def get_provider_info(self) -> dict:
        """Get information about the current embedding provider."""
        return {
            "provider": self.provider,
            "model": getattr(self.model, "_model_name", str(type(self.model).__name__)),
            "dimension": 384,  # Standard dimension we use
            "description": {
                "sentence-transformers": "High-quality semantic embeddings using transformer models",
                "tfidf": "TF-IDF vectorization with keyword matching",
                "simple": "Basic word-based features (limited functionality)",
            }.get(self.provider, "Unknown provider"),
        }


class EmbeddingCache:
    """Simple in-memory cache for embeddings to avoid recomputing."""

    def __init__(self, max_size: int = 1000):
        """Initialize cache with maximum size."""
        self.cache = {}
        self.max_size = max_size
        self.access_order = []

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding for text."""
        if text in self.cache:
            # Move to end of access order (LRU)
            self.access_order.remove(text)
            self.access_order.append(text)
            return self.cache[text]
        return None

    def put(self, text: str, embedding: np.ndarray):
        """Cache embedding for text."""
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        self.cache[text] = embedding
        self.access_order.append(text)

    def clear(self):
        """Clear all cached embeddings."""
        self.cache.clear()
        self.access_order.clear()
