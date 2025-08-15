"""
Generic LLM client for any third-party AI provider.
Users can implement this interface to work with their preferred AI service.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from .config import AIConfig

logger = logging.getLogger(__name__)


class GenericLLMClient:
    """
    Generic LLM client that can be adapted to work with any AI provider.
    
    This client provides a template that users can customize for their specific
    AI service by modifying the request format and response parsing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM client with configuration.
        
        Args:
            config: Optional configuration dict. If not provided, uses AIConfig.
        """
        self.config = config or AIConfig.get_ai_config()
        self.session = requests.Session()
        
        # Set up session headers
        if self.config.get('custom_headers'):
            self.session.headers.update(self.config['custom_headers'])
    
    def is_available(self) -> bool:
        """Check if the AI service is available and configured."""
        return (
            self.config.get('enabled', False) and
            self.config.get('api_endpoint') and
            self.config.get('model_name')
        )
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the AI provider.
        
        Args:
            messages: List of conversation messages [{"role": "user", "content": "..."}]
            context: Optional RAG context to include
            tools: Optional MCP tools available to the AI
        
        Returns:
            Dict containing the AI response and metadata
        """
        if not self.is_available():
            raise ValueError("AI service is not properly configured or enabled")
        
        # Prepare the request payload
        payload = self._prepare_request(messages, context, tools)
        
        try:
            # Make the API request
            response = self.session.post(
                self.config['api_endpoint'],
                json=payload,
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            
            # Parse and return the response
            return self._parse_response(response.json())
            
        except requests.exceptions.RequestException as e:
            logger.error(f"AI API request failed: {e}")
            return {
                'text': "I'm having trouble connecting to the AI service. Please try again later.",
                'error': str(e),
                'provider': 'generic',
                'model': self.config.get('model_name', 'unknown')
            }
        except Exception as e:
            logger.error(f"Unexpected error in AI request: {e}")
            return {
                'text': "An unexpected error occurred. Please try again.",
                'error': str(e),
                'provider': 'generic',
                'model': self.config.get('model_name', 'unknown')
            }
    
    def _prepare_request(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Prepare the request payload for the AI provider.
        
        CUSTOMIZE THIS METHOD FOR YOUR AI PROVIDER
        
        This is a generic template that you should modify to match
        your AI provider's API format.
        
        Examples:
        - For OpenAI-compatible APIs: Use "messages" array format
        - For Anthropic-style APIs: Use "prompt" with specific formatting
        - For custom APIs: Adapt to your specific request structure
        """
        
        # Build the system prompt with context and tools
        system_content = self._build_system_prompt(context, tools)
        
        # TEMPLATE REQUEST FORMAT - CUSTOMIZE FOR YOUR PROVIDER
        payload = {
            "model": self.config['model_name'],
            "messages": [
                {
                    "role": "system",
                    "content": system_content
                }
            ] + messages,
            "temperature": self.config.get('temperature', 0.7),
            "max_tokens": self.config.get('max_tokens', 2000),
            
            # Add any provider-specific parameters here
            # Examples:
            # "stream": False,
            # "top_p": 1.0,
            # "frequency_penalty": 0.0,
            # "presence_penalty": 0.0,
        }
        
        # If your provider uses a different format, modify this section:
        # For example, some providers might use:
        # payload = {
        #     "prompt": self._format_prompt(messages, system_content),
        #     "model": self.config['model_name'],
        #     "parameters": {
        #         "temperature": self.config.get('temperature', 0.7),
        #         "max_length": self.config.get('max_tokens', 2000)
        #     }
        # }
        
        return payload
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the response from the AI provider.
        
        CUSTOMIZE THIS METHOD FOR YOUR AI PROVIDER
        
        Args:
            response_data: Raw response from the AI API
            
        Returns:
            Standardized response format
        """
        
        # TEMPLATE RESPONSE PARSING - CUSTOMIZE FOR YOUR PROVIDER
        try:
            # This assumes OpenAI-compatible response format
            # Modify this based on your provider's response structure
            
            if 'choices' in response_data and response_data['choices']:
                message = response_data['choices'][0].get('message', {})
                content = message.get('content', '')
                
                # Check for tool calls (if your provider supports them)
                tool_calls = message.get('tool_calls', [])
                
                return {
                    'text': content,
                    'tools_called': tool_calls,
                    'provider': 'generic',
                    'model': self.config.get('model_name'),
                    'usage': response_data.get('usage', {}),
                    'finish_reason': response_data['choices'][0].get('finish_reason'),
                    'raw_response': response_data
                }
            
            # Alternative format examples for other providers:
            
            # For Anthropic-style responses:
            # if 'completion' in response_data:
            #     return {
            #         'text': response_data['completion'],
            #         'provider': 'generic',
            #         'model': self.config.get('model_name'),
            #         'usage': response_data.get('usage', {}),
            #         'raw_response': response_data
            #     }
            
            # For custom provider format:
            # if 'generated_text' in response_data:
            #     return {
            #         'text': response_data['generated_text'],
            #         'provider': 'generic',
            #         'model': self.config.get('model_name'),
            #         'confidence': response_data.get('confidence_score'),
            #         'raw_response': response_data
            #     }
            
            # Fallback if response format is unexpected
            return {
                'text': "Received an unexpected response format from the AI service.",
                'error': f"Unexpected response structure: {response_data}",
                'provider': 'generic',
                'model': self.config.get('model_name'),
                'raw_response': response_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                'text': "Error parsing AI response.",
                'error': str(e),
                'provider': 'generic',
                'model': self.config.get('model_name'),
                'raw_response': response_data
            }
    
    def _build_system_prompt(
        self, 
        context: Optional[str] = None, 
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Build the system prompt with context and available tools.
        
        Args:
            context: RAG context from documentation
            tools: Available MCP tools
            
        Returns:
            Formatted system prompt
        """
        system_parts = [
            "You are Ben Bot, an intelligent assistant for Nautobot network automation platform.",
            "You help users navigate Nautobot, understand its features, and work with network data.",
            "",
            "Guidelines:",
            "- Be helpful, accurate, and concise",
            "- When users ask about navigation, suggest specific pages or actions",
            "- Use the provided context to give accurate information",
            "- If you can't find specific information, say so clearly",
            "- Always prioritize user safety and best practices"
        ]
        
        # Add RAG context if available
        if context:
            system_parts.extend([
                "",
                "Relevant documentation context:",
                context.strip()
            ])
        
        # Add available tools if any
        if tools:
            system_parts.extend([
                "",
                "Available tools:",
                json.dumps(tools, indent=2)
            ])
        
        return "\n".join(system_parts)
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text (if your provider supports it).
        
        CUSTOMIZE THIS METHOD IF YOUR PROVIDER SUPPORTS EMBEDDINGS
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        # Most providers have separate embedding endpoints
        # Example implementation:
        
        embedding_endpoint = self.config.get('embedding_endpoint')
        if not embedding_endpoint:
            raise NotImplementedError("Embeddings not configured for this provider")
        
        # payload = {
        #     "model": self.config.get('embedding_model', 'text-embedding-ada-002'),
        #     "input": text
        # }
        
        # response = self.session.post(embedding_endpoint, json=payload)
        # response.raise_for_status()
        # return response.json()['data'][0]['embedding']
        
        raise NotImplementedError(
            "Embeddings not implemented. "
            "Customize this method for your provider or use sentence-transformers."
        )