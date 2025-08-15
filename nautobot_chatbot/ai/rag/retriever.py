"""
RAG retrieval system for Nautobot documentation.
"""

# Standard library imports
import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

# Third-party imports
import requests

# Local imports
from ..config import AIConfig
from .vectorstore import Document, SimpleVectorStore, chunk_text

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Retrieval-Augmented Generation system for Nautobot documentation.

    This system indexes documentation and provides relevant context
    for AI responses based on user queries.
    """

    def __init__(self, vector_store: Optional[SimpleVectorStore] = None):
        """
        Initialize RAG retriever.

        Args:
            vector_store: Optional vector store instance. If not provided, creates a new one.
        """
        self.config = AIConfig.get_rag_config()

        if vector_store:
            self.vector_store = vector_store
        else:
            storage_path = self.config.get("vector_store_path", "/tmp/nautobot_vectors")
            self.vector_store = SimpleVectorStore(storage_path)

        self.is_initialized = len(self.vector_store.documents) > 0

        if not self.is_initialized:
            logger.info(
                "RAG system not initialized. Run initialize_documents() to index documentation."
            )

    def retrieve(self, query: str, k: Optional[int] = None) -> str:
        """
        Retrieve relevant documentation context for a query.

        Args:
            query: User query
            k: Number of chunks to retrieve

        Returns:
            Formatted context string
        """
        if not self.config.get("enabled", True):
            return ""

        if not self.is_initialized:
            logger.warning("RAG system not initialized. No context available.")
            return ""

        k = k or self.config.get("max_context_chunks", 5)

        # Retrieve similar documents
        results = self.vector_store.search(query, k=k, score_threshold=0.1)

        if not results:
            return ""

        # Format context
        context_parts = []
        for doc, score in results:
            metadata = doc.metadata
            source_info = ""

            if metadata.get("title"):
                source_info = f"[{metadata['title']}]"
            elif metadata.get("source"):
                source_info = f"[{metadata['source']}]"

            context_parts.append(f"{source_info} {doc.content}")

        return "\n\n".join(context_parts)

    def initialize_documents(self):
        """
        Initialize the RAG system by indexing documentation.

        This method will:
        1. Download Nautobot documentation
        2. Process and chunk the content
        3. Generate embeddings and store in vector database
        """
        logger.info("Initializing RAG system with documentation...")

        documents = []

        # Add sample Nautobot documentation
        documents.extend(self._get_sample_nautobot_docs())

        # Try to fetch online documentation if configured
        if self.config.get("doc_sources", {}).get("nautobot_docs"):
            try:
                online_docs = self._fetch_online_documentation()
                documents.extend(online_docs)
            except Exception as e:
                logger.warning(f"Failed to fetch online documentation: {e}")

        # Add custom documentation if path is provided
        custom_docs_path = self.config.get("doc_sources", {}).get("custom_docs")
        if custom_docs_path and os.path.exists(custom_docs_path):
            try:
                custom_docs = self._load_custom_documentation(custom_docs_path)
                documents.extend(custom_docs)
            except Exception as e:
                logger.warning(f"Failed to load custom documentation: {e}")

        if documents:
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            self.is_initialized = True
            logger.info(f"RAG system initialized with {len(documents)} document chunks")
        else:
            logger.warning("No documentation found to initialize RAG system")

    def _get_sample_nautobot_docs(self) -> List[Document]:
        """Get sample Nautobot documentation for basic functionality."""

        sample_docs = [
            {
                "title": "Nautobot Overview",
                "content": """
                Nautobot is a network automation platform that provides a single source of truth
                for network infrastructure data. It helps network engineers manage devices, circuits,
                IP addresses, and other network resources through a web interface and REST API.
                
                Key features include:
                - Device inventory management
                - IP Address Management (IPAM)
                - Circuit tracking
                - Cable management
                - Virtualization support
                - Custom fields and relationships
                - Extensible plugin system
                """,
                "source": "sample_docs",
            },
            {
                "title": "Device Management",
                "content": """
                Nautobot's device management system allows you to track network devices including
                routers, switches, servers, and other equipment. You can organize devices by:
                
                - Sites and locations
                - Device types and roles
                - Manufacturers and models
                - Physical rack positions
                - Device connections and cables
                
                To view devices, navigate to Organization > Devices in the main menu.
                To add a new device, click the + button and fill in the device details.
                """,
                "source": "sample_docs",
            },
            {
                "title": "IP Address Management (IPAM)",
                "content": """
                Nautobot's IPAM system helps you manage IP addresses, prefixes, and VLANs.
                Key IPAM features include:
                
                - Prefix hierarchy and allocation
                - IP address assignment tracking
                - VLAN management
                - VRF (Virtual Routing and Forwarding) support
                - Automatic IP discovery
                - Available IP address calculation
                
                To access IPAM features, use the IPAM menu in the navigation bar.
                You can view prefixes, IP addresses, and VLANs from their respective sections.
                """,
                "source": "sample_docs",
            },
            {
                "title": "Circuit Management",
                "content": """
                Nautobot helps track provider circuits and connections. Circuit management includes:
                
                - Provider and circuit type tracking
                - Circuit termination points
                - Bandwidth and commitment tracking
                - Circuit status monitoring
                - Integration with device interfaces
                
                To view circuits, navigate to Circuits > Circuits in the main menu.
                Circuit types can be managed under Circuits > Circuit Types.
                """,
                "source": "sample_docs",
            },
            {
                "title": "Navigation and Interface",
                "content": """
                The Nautobot interface is organized with the following main sections:
                
                - Organization: Sites, locations, racks, devices
                - IPAM: IP addresses, prefixes, VLANs
                - Circuits: Provider circuits and types
                - Extras: Custom fields, tags, webhooks
                - Admin: User management and system settings
                
                Each section provides list views, detail views, and forms for creating/editing objects.
                Use the search bar to quickly find specific items.
                The + button allows you to create new objects in most sections.
                """,
                "source": "sample_docs",
            },
            {
                "title": "REST API Usage",
                "content": """
                Nautobot provides a comprehensive REST API for programmatic access to all data.
                The API follows RESTful conventions and supports:
                
                - GET requests for retrieving data
                - POST requests for creating objects
                - PATCH/PUT requests for updating objects
                - DELETE requests for removing objects
                - Filtering and pagination
                - Authentication via API tokens
                
                API documentation is available at /api/docs/ in your Nautobot instance.
                Base API URL is typically http://your-nautobot-host/api/
                """,
                "source": "sample_docs",
            },
        ]

        documents = []
        chunk_size = self.config.get("chunk_size", 512)
        chunk_overlap = self.config.get("chunk_overlap", 50)

        for doc_data in sample_docs:
            # Chunk the content
            chunks = chunk_text(doc_data["content"], chunk_size, chunk_overlap)

            for i, chunk in enumerate(chunks):
                doc = Document(
                    content=chunk.strip(),
                    metadata={
                        "title": doc_data["title"],
                        "source": doc_data["source"],
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                    },
                )
                documents.append(doc)

        return documents

    def _fetch_online_documentation(self) -> List[Document]:
        """
        Fetch documentation from online sources.

        Note: This is a placeholder implementation.
        In a real deployment, you would implement web scraping
        or API calls to fetch actual documentation.
        """
        documents = []

        # This would typically involve:
        # 1. Crawling the Nautobot documentation site
        # 2. Extracting text content from HTML pages
        # 3. Chunking the content appropriately
        # 4. Creating Document objects with proper metadata

        # For now, return empty list since we have sample docs
        logger.info("Online documentation fetching not implemented. Using sample docs.")

        return documents

    def _load_custom_documentation(self, docs_path: str) -> List[Document]:
        """
        Load custom documentation from local files.

        Args:
            docs_path: Path to directory containing documentation files

        Returns:
            List of Document objects
        """
        documents = []
        chunk_size = self.config.get("chunk_size", 512)
        chunk_overlap = self.config.get("chunk_overlap", 50)

        try:
            for root, dirs, files in os.walk(docs_path):
                for file in files:
                    if file.endswith((".txt", ".md", ".rst")):
                        file_path = os.path.join(root, file)

                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            # Chunk the content
                            chunks = chunk_text(content, chunk_size, chunk_overlap)

                            for i, chunk in enumerate(chunks):
                                doc = Document(
                                    content=chunk.strip(),
                                    metadata={
                                        "title": file,
                                        "source": file_path,
                                        "chunk_id": i,
                                        "total_chunks": len(chunks),
                                    },
                                )
                                documents.append(doc)

                        except Exception as e:
                            logger.warning(f"Failed to load {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to load custom documentation from {docs_path}: {e}")

        return documents

    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a single document to the RAG system.

        Args:
            content: Document content
            metadata: Optional metadata dict
        """
        chunk_size = self.config.get("chunk_size", 512)
        chunk_overlap = self.config.get("chunk_overlap", 50)

        chunks = chunk_text(content, chunk_size, chunk_overlap)
        documents = []

        for i, chunk in enumerate(chunks):
            doc_metadata = (metadata or {}).copy()
            doc_metadata.update({"chunk_id": i, "total_chunks": len(chunks)})

            doc = Document(content=chunk.strip(), metadata=doc_metadata)
            documents.append(doc)

        self.vector_store.add_documents(documents)

        if not self.is_initialized and len(self.vector_store.documents) > 0:
            self.is_initialized = True

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        stats = self.vector_store.get_stats()
        stats.update({"is_initialized": self.is_initialized, "config": self.config})
        return stats
