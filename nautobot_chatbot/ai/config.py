"""
Configuration management for AI components.

This module provides configuration management for all AI features including:
- LLM providers (OpenAI, Anthropic, custom APIs)
- RAG systems (document retrieval and vectorization)
- MCP tools (Model Context Protocol for Nautobot integration)

Configuration can be provided through:
1. Django settings (PLUGINS_CONFIG)
2. Environment variables
3. Default values

Example Django configuration:
    PLUGINS_CONFIG = {
        "nautobot_chatbot": {
            "ai_config": {
                "enabled": True,
                "provider": "openai",  # or "anthropic", "generic", etc.
                "api_base_url": "https://api.openai.com/v1",
                "api_key": "your-api-key",
                "model_name": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "rag_config": {
                "enabled": True,
                "embedding_model": "text-embedding-ada-002",
                "chunk_size": 1000,
                "max_results": 5
            },
            "mcp_config": {
                "enabled": True,
                "nautobot_api_token": "your-nautobot-token"
            }
        }
    }
"""
import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class AIConfig:
    """
    Centralized configuration for AI components.
    Supports Django settings, environment variables, and defaults.
    """
    
    @staticmethod
    def get_ai_config() -> Dict[str, Any]:
        """
        Get AI configuration from Django settings, environment variables, or defaults.
        
        Configuration sources (in order of precedence):
        1. Django PLUGINS_CONFIG['nautobot_chatbot']['ai_config']
        2. Environment variables (AI_*)
        3. Default values
        
        Environment variables:
        - AI_PROVIDER_ENABLED: Enable/disable AI features
        - AI_API_ENDPOINT: API endpoint URL
        - AI_API_KEY: API authentication key
        - AI_MODEL_NAME: Model name to use
        - AI_TEMPERATURE: Model temperature (0.0-1.0)
        - AI_MAX_TOKENS: Maximum tokens per response
        - AI_REQUEST_TIMEOUT: Request timeout in seconds
        
        Returns:
            Dict containing AI configuration
        """
        # Get Django plugin config
        plugins_config = getattr(settings, 'PLUGINS_CONFIG', {})
        chatbot_config = plugins_config.get('nautobot_chatbot', {})
        django_ai_config = chatbot_config.get('ai_config', {})
        
        # Merge Django config with environment variables and defaults
        config = {
            'enabled': django_ai_config.get('enabled', 
                os.getenv('AI_PROVIDER_ENABLED', 'false').lower() == 'true'),
            'provider': django_ai_config.get('provider', 
                os.getenv('AI_PROVIDER', 'generic')),
            'api_base_url': django_ai_config.get('api_base_url', 
                os.getenv('AI_API_ENDPOINT', '')),
            'api_key': django_ai_config.get('api_key', 
                os.getenv('AI_API_KEY', '')),
            'model_name': django_ai_config.get('model_name', 
                os.getenv('AI_MODEL_NAME', 'default')),
            'temperature': django_ai_config.get('temperature', 
                float(os.getenv('AI_TEMPERATURE', '0.7'))),
            'max_tokens': django_ai_config.get('max_tokens', 
                int(os.getenv('AI_MAX_TOKENS', '2000'))),
            'timeout': django_ai_config.get('timeout', 
                int(os.getenv('AI_REQUEST_TIMEOUT', '30'))),
            'request_headers': django_ai_config.get('request_headers', {}),
            'custom_fields': django_ai_config.get('custom_fields', {})
        }
        
        # Add default headers if not provided
        if not config['request_headers']:
            config['request_headers'] = {
                'Content-Type': 'application/json',
                'User-Agent': 'Nautobot-Chatbot/1.0.0'
            }
            if config['api_key']:
                config['request_headers']['Authorization'] = f"Bearer {config['api_key']}"
        
        return config
    
    @staticmethod
    def get_rag_config() -> Dict[str, Any]:
        """
        Get RAG (Retrieval-Augmented Generation) configuration.
        
        Configuration sources (in order of precedence):
        1. Django PLUGINS_CONFIG['nautobot_chatbot']['rag_config']
        2. Environment variables (RAG_*)
        3. Default values
        
        Environment variables:
        - RAG_ENABLED: Enable/disable RAG features
        - RAG_EMBEDDING_MODEL: Embedding model to use
        - RAG_CHUNK_SIZE: Document chunk size
        - RAG_CHUNK_OVERLAP: Chunk overlap size
        - RAG_MAX_CHUNKS: Maximum chunks to retrieve
        - VECTOR_STORE_PATH: Path to store vector embeddings
        
        Returns:
            Dict containing RAG configuration
        """
        # Get Django plugin config
        plugins_config = getattr(settings, 'PLUGINS_CONFIG', {})
        chatbot_config = plugins_config.get('nautobot_chatbot', {})
        django_rag_config = chatbot_config.get('rag_config', {})
        
        # Get default paths
        base_path = os.path.dirname(__file__)
        default_docs_path = os.path.join(base_path, 'rag', 'documents')
        default_vector_path = os.path.join(base_path, 'rag', 'vector_store')
        
        return {
            'enabled': django_rag_config.get('enabled', 
                os.getenv('RAG_ENABLED', 'true').lower() == 'true'),
            'embedding_provider': django_rag_config.get('embedding_provider', 
                os.getenv('RAG_EMBEDDING_PROVIDER', 'sentence_transformers')),
            'embedding_model': django_rag_config.get('embedding_model', 
                os.getenv('RAG_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')),
            'chunk_size': django_rag_config.get('chunk_size', 
                int(os.getenv('RAG_CHUNK_SIZE', '1000'))),
            'chunk_overlap': django_rag_config.get('chunk_overlap', 
                int(os.getenv('RAG_CHUNK_OVERLAP', '200'))),
            'max_results': django_rag_config.get('max_results', 
                int(os.getenv('RAG_MAX_CHUNKS', '5'))),
            'similarity_threshold': django_rag_config.get('similarity_threshold', 
                float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.7'))),
            'documents_path': django_rag_config.get('documents_path', 
                os.getenv('RAG_DOCUMENTS_PATH', default_docs_path)),
            'vector_store_path': django_rag_config.get('vector_store_path', 
                os.getenv('VECTOR_STORE_PATH', default_vector_path)),
            
            # Documentation sources
            'doc_sources': django_rag_config.get('doc_sources', {
                'nautobot_docs': os.getenv('NAUTOBOT_DOCS_URL', 'https://docs.nautobot.com'),
                'custom_docs': os.getenv('CUSTOM_DOCS_PATH', ''),
            })
        }
    
    @staticmethod
    def get_mcp_config() -> Dict[str, Any]:
        """
        Get MCP (Model Context Protocol) tools configuration.
        
        Configuration sources (in order of precedence):
        1. Django PLUGINS_CONFIG['nautobot_chatbot']['mcp_config']
        2. Environment variables (MCP_*)
        3. Default values
        
        Environment variables:
        - MCP_TOOLS_ENABLED: Enable/disable MCP tools
        - MCP_NAVIGATION_ENABLED: Enable navigation tools
        - MCP_API_QUERIES_ENABLED: Enable API query tools
        - MCP_API_RATE_LIMIT: API rate limit (requests per minute)
        - NAUTOBOT_API_BASE: Nautobot API base URL
        - NAUTOBOT_API_TOKEN: Nautobot API token
        
        Returns:
            Dict containing MCP tools configuration
        """
        # Get Django plugin config
        plugins_config = getattr(settings, 'PLUGINS_CONFIG', {})
        chatbot_config = plugins_config.get('nautobot_chatbot', {})
        django_mcp_config = chatbot_config.get('mcp_config', {})
        
        return {
            'enabled': django_mcp_config.get('enabled', 
                os.getenv('MCP_TOOLS_ENABLED', 'true').lower() == 'true'),
            'enable_navigation': django_mcp_config.get('enable_navigation', 
                os.getenv('MCP_NAVIGATION_ENABLED', 'true').lower() == 'true'),
            'enable_api_queries': django_mcp_config.get('enable_api_queries', 
                os.getenv('MCP_API_QUERIES_ENABLED', 'true').lower() == 'true'),
            'api_rate_limit': django_mcp_config.get('api_rate_limit', 
                int(os.getenv('MCP_API_RATE_LIMIT', '10'))),
            'enabled_tools': django_mcp_config.get('enabled_tools', [
                'navigate_to_page', 'search_nautobot', 'create_object'
            ]),
            
            # Nautobot API configuration
            'nautobot_api_base': django_mcp_config.get('nautobot_api_base', 
                os.getenv('NAUTOBOT_API_BASE', 'http://localhost:8000/api')),
            'nautobot_api_token': django_mcp_config.get('nautobot_api_token', 
                os.getenv('NAUTOBOT_API_TOKEN', ''))
        }
    
    @staticmethod
    def is_ai_enabled() -> bool:
        """Check if AI features are enabled and properly configured."""
        config = AIConfig.get_ai_config()
        return (
            config['enabled'] and 
            config['api_base_url'] and
            config['model_name'] and config['model_name'] != 'default'
        )
    
    @staticmethod
    def validate_configuration() -> Dict[str, Any]:
        """
        Validate all AI configurations and return comprehensive status.
        
        Returns:
            Dict containing validation results for all components
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'ai_config': {},
            'rag_config': {},
            'mcp_config': {},
            'components_status': {}
        }
        
        try:
            # Validate AI config
            ai_config = AIConfig.get_ai_config()
            results['ai_config'] = ai_config
            
            if ai_config['enabled']:
                if not ai_config['api_base_url']:
                    results['errors'].append('AI enabled but no API base URL configured')
                if not ai_config['model_name'] or ai_config['model_name'] == 'default':
                    results['warnings'].append('AI enabled but using default model name')
                if ai_config['temperature'] < 0 or ai_config['temperature'] > 1:
                    results['warnings'].append('AI temperature should be between 0 and 1')
                if ai_config['max_tokens'] <= 0:
                    results['errors'].append('AI max_tokens must be positive')
            
            # Validate RAG config
            rag_config = AIConfig.get_rag_config()
            results['rag_config'] = rag_config
            
            if rag_config['enabled']:
                if not os.path.exists(rag_config['documents_path']):
                    results['warnings'].append(
                        f'RAG documents path does not exist: {rag_config["documents_path"]}'
                    )
                if rag_config['chunk_size'] <= 0:
                    results['errors'].append('RAG chunk_size must be positive')
                if rag_config['max_results'] <= 0:
                    results['errors'].append('RAG max_results must be positive')
            
            # Validate MCP config
            mcp_config = AIConfig.get_mcp_config()
            results['mcp_config'] = mcp_config
            
            if mcp_config['enabled']:
                if not mcp_config['nautobot_api_base']:
                    results['warnings'].append('MCP enabled but no Nautobot API base URL configured')
                if mcp_config['api_rate_limit'] <= 0:
                    results['errors'].append('MCP API rate limit must be positive')
            
            # Component status summary
            results['components_status'] = {
                'ai_enabled': ai_config['enabled'] and not any('AI' in error for error in results['errors']),
                'rag_enabled': rag_config['enabled'] and not any('RAG' in error for error in results['errors']),
                'mcp_enabled': mcp_config['enabled'] and not any('MCP' in error for error in results['errors']),
                'fully_configured': AIConfig.is_ai_enabled()
            }
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            results['errors'].append(f'Configuration validation failed: {str(e)}')
        
        # Set overall validity
        results['valid'] = len(results['errors']) == 0
        
        return results
    
    @staticmethod
    def get_configuration_help() -> str:
        """
        Get help text for configuring the AI features.
        
        Returns:
            String containing configuration instructions
        """
        return """
Nautobot Chatbot AI Configuration Help
=====================================

The chatbot supports three main AI components:
1. LLM Integration (OpenAI, Anthropic, custom APIs)
2. RAG System (document retrieval and vectorization)
3. MCP Tools (Model Context Protocol for Nautobot integration)

Configuration Methods:
---------------------

Method 1: Django Settings (Recommended)
Add to your nautobot_config.py:

    PLUGINS_CONFIG = {
        "nautobot_chatbot": {
            "ai_config": {
                "enabled": True,
                "provider": "openai",  # or "anthropic", "generic"
                "api_base_url": "https://api.openai.com/v1",
                "api_key": "your-api-key-here",
                "model_name": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.7,
                "timeout": 30
            },
            "rag_config": {
                "enabled": True,
                "embedding_model": "all-MiniLM-L6-v2",
                "chunk_size": 1000,
                "max_results": 5
            },
            "mcp_config": {
                "enabled": True,
                "nautobot_api_token": "your-nautobot-api-token"
            }
        }
    }

Method 2: Environment Variables
Set these environment variables:

    # AI Configuration
    AI_PROVIDER_ENABLED=true
    AI_API_ENDPOINT=https://api.openai.com/v1
    AI_API_KEY=your-api-key-here
    AI_MODEL_NAME=gpt-4
    AI_TEMPERATURE=0.7
    AI_MAX_TOKENS=1000

    # RAG Configuration
    RAG_ENABLED=true
    RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
    RAG_CHUNK_SIZE=1000

    # MCP Configuration
    MCP_TOOLS_ENABLED=true
    NAUTOBOT_API_TOKEN=your-nautobot-api-token

Quick Start:
-----------
1. For basic chatbot: No configuration needed
2. For AI features: Set AI_PROVIDER_ENABLED=true and configure API details
3. For full features: Configure all three components

Check Status:
------------
Visit /plugins/chatbot/api/status/ to see current configuration status.
        """