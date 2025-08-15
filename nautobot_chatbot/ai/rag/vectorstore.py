"""
Vector storage and retrieval for RAG system.
Supports multiple storage backends with automatic fallbacks.
"""

# Standard library imports
import json
import logging
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
import numpy as np

# Local imports
from .embeddings import EmbeddingCache, EmbeddingProvider

logger = logging.getLogger(__name__)


class Document:
    """Represents a document chunk in the vector store."""

    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a document.

        Args:
            content: The text content of the document
            metadata: Additional metadata (title, source, section, etc.)
        """
        self.content = content
        self.metadata = metadata or {}
        self.id = metadata.get("id") if metadata else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for serialization."""
        return {"content": self.content, "metadata": self.metadata, "id": self.id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary."""
        doc = cls(data["content"], data.get("metadata", {}))
        doc.id = data.get("id")
        return doc


class SimpleVectorStore:
    """
    Simple file-based vector store implementation.

    This is a lightweight implementation that doesn't require external
    dependencies. For production use with large datasets, consider
    using ChromaDB, FAISS, or other specialized vector databases.
    """

    def __init__(self, storage_path: str):
        """
        Initialize vector store.

        Args:
            storage_path: Path to store vector data
        """
        self.storage_path = storage_path
        self.documents: List[Document] = []
        self.embeddings: np.ndarray = np.array([])
        self.embedding_provider = EmbeddingProvider()
        self.embedding_cache = EmbeddingCache()

        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)

        # Load existing data
        self._load_data()

    def add_documents(self, documents: List[Document], batch_size: int = 32):
        """
        Add documents to the vector store.

        Args:
            documents: List of documents to add
            batch_size: Number of documents to process at once
        """
        if not documents:
            return

        logger.info(f"Adding {len(documents)} documents to vector store")

        # Generate embeddings in batches
        new_embeddings = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            texts = [doc.content for doc in batch]

            # Check cache first
            batch_embeddings = []
            uncached_texts = []
            uncached_indices = []

            for j, text in enumerate(texts):
                cached_embedding = self.embedding_cache.get(text)
                if cached_embedding is not None:
                    batch_embeddings.append(cached_embedding)
                else:
                    batch_embeddings.append(None)
                    uncached_texts.append(text)
                    uncached_indices.append(j)

            # Generate embeddings for uncached texts
            if uncached_texts:
                uncached_embeddings = self.embedding_provider.encode(uncached_texts)

                # Fill in the uncached embeddings and cache them
                for idx, embedding in zip(uncached_indices, uncached_embeddings):
                    batch_embeddings[idx] = embedding
                    self.embedding_cache.put(texts[idx], embedding)

            new_embeddings.extend(batch_embeddings)

        # Add documents and embeddings to store
        self.documents.extend(documents)

        if len(new_embeddings) > 0:
            new_embeddings_array = np.array(new_embeddings)
            if self.embeddings.size == 0:
                self.embeddings = new_embeddings_array
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings_array])

        # Save updated data
        self._save_data()

        logger.info(f"Vector store now contains {len(self.documents)} documents")

    def search(
        self, query: str, k: int = 5, score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.

        Args:
            query: Query text
            k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of (document, similarity_score) tuples
        """
        if len(self.documents) == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_provider.encode([query])[0]

        # Calculate similarities
        similarities = self._cosine_similarity(query_embedding, self.embeddings)

        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score >= score_threshold:
                results.append((self.documents[idx], float(score)))

        return results

    def _cosine_similarity(
        self, query_embedding: np.ndarray, doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate cosine similarity between query and document embeddings."""
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # Handle zero norms
        doc_norms = np.nan_to_num(doc_norms, 0)
        query_norm = np.nan_to_num(query_norm, 0)

        # Calculate cosine similarity
        similarities = np.dot(doc_norms, query_norm)
        return similarities

    def _save_data(self):
        """Save documents and embeddings to disk."""
        try:
            # Save documents
            docs_path = os.path.join(self.storage_path, "documents.json")
            with open(docs_path, "w", encoding="utf-8") as f:
                docs_data = [doc.to_dict() for doc in self.documents]
                json.dump(docs_data, f, ensure_ascii=False, indent=2)

            # Save embeddings
            embeddings_path = os.path.join(self.storage_path, "embeddings.npy")
            if self.embeddings.size > 0:
                np.save(embeddings_path, self.embeddings)

            # Save metadata
            metadata_path = os.path.join(self.storage_path, "metadata.json")
            metadata = {
                "document_count": len(self.documents),
                "embedding_provider": self.embedding_provider.get_provider_info(),
                "version": "1.0",
            }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save vector store data: {e}")

    def _load_data(self):
        """Load documents and embeddings from disk."""
        try:
            # Load documents
            docs_path = os.path.join(self.storage_path, "documents.json")
            if os.path.exists(docs_path):
                with open(docs_path, "r", encoding="utf-8") as f:
                    docs_data = json.load(f)
                    self.documents = [Document.from_dict(doc_data) for doc_data in docs_data]

            # Load embeddings
            embeddings_path = os.path.join(self.storage_path, "embeddings.npy")
            if os.path.exists(embeddings_path):
                self.embeddings = np.load(embeddings_path)

            # Load and log metadata
            metadata_path = os.path.join(self.storage_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    logger.info(
                        f"Loaded vector store: {metadata.get('document_count', 0)} documents"
                    )

        except Exception as e:
            logger.warning(f"Failed to load vector store data: {e}. Starting with empty store.")
            self.documents = []
            self.embeddings = np.array([])

    def clear(self):
        """Clear all documents and embeddings."""
        self.documents.clear()
        self.embeddings = np.array([])
        self.embedding_cache.clear()
        self._save_data()
        logger.info("Vector store cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "document_count": len(self.documents),
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings.size > 0 else 0,
            "storage_path": self.storage_path,
            "embedding_provider": self.embedding_provider.get_provider_info(),
        }


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.

    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        chunk_overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at word boundaries
        if end < len(text):
            # Find the last space before the chunk_size limit
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position, accounting for overlap
        start = end - chunk_overlap
        if start <= 0:
            start = end

    return chunks
