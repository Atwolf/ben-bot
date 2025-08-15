"""
Main AI engine that orchestrates RAG, MCP tools, and LLM interactions.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from .config import AIConfig
from .llm_client import GenericLLMClient
from .rag.retriever import RAGRetriever
from .mcp.tools import MCPToolRegistry
from .mcp.api_client import NautobotAPIClient

logger = logging.getLogger(__name__)


class AIEngine:
    """
    Main AI engine that combines RAG, MCP tools, and LLM capabilities.
    
    This engine provides intelligent responses by:
    1. Retrieving relevant documentation context (RAG)
    2. Identifying and executing appropriate tools (MCP)
    3. Generating responses using an LLM
    """
    
    def __init__(self):
        """Initialize AI engine with all components."""
        self.ai_config = AIConfig.get_ai_config()
        self.rag_config = AIConfig.get_rag_config()
        self.mcp_config = AIConfig.get_mcp_config()
        
        # Initialize components
        self.llm_client = None
        self.rag_retriever = None
        self.mcp_registry = None
        self.api_client = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize AI components based on configuration."""
        
        # Initialize LLM client
        if self.ai_config.get('enabled', False):
            try:
                self.llm_client = GenericLLMClient(self.ai_config)
                if self.llm_client.is_available():
                    logger.info("LLM client initialized successfully")
                else:
                    logger.warning("LLM client not properly configured")
                    self.llm_client = None
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                self.llm_client = None
        
        # Initialize RAG system
        if self.rag_config.get('enabled', True):
            try:
                self.rag_retriever = RAGRetriever()
                
                # Initialize documents if not already done
                if not self.rag_retriever.is_initialized:
                    logger.info("Initializing RAG system...")
                    self.rag_retriever.initialize_documents()
                
                logger.info("RAG system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG system: {e}")
                self.rag_retriever = None
        
        # Initialize MCP tools
        if self.mcp_config.get('enabled', True):
            try:
                self.mcp_registry = MCPToolRegistry()
                logger.info("MCP tools initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MCP tools: {e}")
                self.mcp_registry = None
        
        # Initialize API client
        try:
            self.api_client = NautobotAPIClient()
            if self.api_client.is_configured():
                logger.info("Nautobot API client initialized successfully")
            else:
                logger.info("Nautobot API client not configured (this is optional)")
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            self.api_client = None
    
    def is_configured(self) -> bool:
        """Check if AI engine has any functional components."""
        return any([
            self.llm_client and self.llm_client.is_available(),
            self.rag_retriever and self.rag_retriever.is_initialized,
            self.mcp_registry
        ])
    
    def generate_response(
        self,
        message: str,
        user: Any,
        session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered response to a user message.
        
        Args:
            message: User message
            user: User object (for personalization and permissions)
            session: Optional chat session for context
            
        Returns:
            Dict containing response and metadata
        """
        response_data = {
            'text': '',
            'actions': [],
            'data': None,
            'provider': 'ai_engine',
            'model': self.ai_config.get('model_name', 'unknown'),
            'tools_used': [],
            'context_sources': []
        }
        
        try:
            # Step 1: Analyze intent and get RAG context
            context = self._get_rag_context(message) if self.rag_retriever else ""
            
            # Step 2: Identify and execute relevant MCP tools
            tool_results = self._execute_relevant_tools(message) if self.mcp_registry else []
            
            # Step 3: Generate response
            if self.llm_client and self.llm_client.is_available():
                # Use AI to generate response
                response_data.update(self._generate_ai_response(message, context, tool_results, user))
            else:
                # Fallback to rule-based response with enhanced capabilities
                response_data.update(self._generate_fallback_response(message, context, tool_results, user))
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                'text': "I apologize, but I encountered an error while processing your request. Please try again.",
                'error': str(e),
                'provider': 'ai_engine',
                'model': 'error_fallback'
            }
    
    def _get_rag_context(self, message: str) -> str:
        """Get relevant documentation context for the message."""
        if not self.rag_retriever or not self.rag_retriever.is_initialized:
            return ""
        
        try:
            context = self.rag_retriever.retrieve(message)
            if context:
                logger.debug(f"Retrieved RAG context: {len(context)} characters")
            return context
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")
            return ""
    
    def _execute_relevant_tools(self, message: str) -> List[Dict[str, Any]]:
        """Identify and execute relevant MCP tools based on the message."""
        if not self.mcp_registry:
            return []
        
        tool_results = []
        message_lower = message.lower()
        
        # Simple intent detection for tool execution
        # In a production system, you might use more sophisticated NLP
        
        # Navigation intents
        navigation_keywords = {
            'show me': ['navigate_to_page'],
            'go to': ['navigate_to_page'],
            'navigate to': ['navigate_to_page'],
            'view': ['navigate_to_page'],
            'see': ['navigate_to_page'],
            'list': ['navigate_to_page'],
            'where': ['navigate_to_page']
        }
        
        # Create object intents
        create_keywords = {
            'create': ['create_object'],
            'add': ['create_object'],
            'new': ['create_object'],
            'make': ['create_object']
        }
        
        # Search intents
        search_keywords = {
            'search': ['search_nautobot'],
            'find': ['search_nautobot'],
            'look for': ['search_nautobot']
        }
        
        # Check for navigation intents
        for keyword, tools in navigation_keywords.items():
            if keyword in message_lower:
                result = self._try_navigation_tool(message_lower)
                if result:
                    tool_results.append(result)
                break
        
        # Check for create intents
        for keyword, tools in create_keywords.items():
            if keyword in message_lower:
                result = self._try_create_tool(message_lower)
                if result:
                    tool_results.append(result)
                break
        
        # Check for search intents
        for keyword, tools in search_keywords.items():
            if keyword in message_lower:
                result = self._try_search_tool(message, message_lower)
                if result:
                    tool_results.append(result)
                break
        
        return tool_results
    
    def _try_navigation_tool(self, message_lower: str) -> Optional[Dict[str, Any]]:
        """Try to execute navigation tool based on message."""
        nav_tool = self.mcp_registry.get_tool('navigate_to_page')
        if not nav_tool:
            return None
        
        # Map common phrases to page types
        page_mappings = {
            'devices': 'devices',
            'device': 'devices',
            'sites': 'sites',
            'site': 'sites',
            'circuits': 'circuits',
            'circuit': 'circuits',
            'circuit types': 'circuit_types',
            'circuit type': 'circuit_types',
            'ip addresses': 'ip_addresses',
            'ip address': 'ip_addresses',
            'ips': 'ip_addresses',
            'prefixes': 'prefixes',
            'prefix': 'prefixes',
            'vlans': 'vlans',
            'vlan': 'vlans',
            'racks': 'racks',
            'rack': 'racks',
            'cables': 'cables',
            'cable': 'cables'
        }
        
        for phrase, page_type in page_mappings.items():
            if phrase in message_lower:
                result = nav_tool.execute({'page_type': page_type})
                if result.get('success'):
                    return {
                        'tool': 'navigate_to_page',
                        'result': result
                    }
        
        return None
    
    def _try_create_tool(self, message_lower: str) -> Optional[Dict[str, Any]]:
        """Try to execute create object tool based on message."""
        create_tool = self.mcp_registry.get_tool('create_object')
        if not create_tool:
            return None
        
        # Map phrases to object types
        object_mappings = {
            'device': 'device',
            'site': 'site',
            'circuit': 'circuit',
            'ip address': 'ip_address',
            'ip': 'ip_address',
            'prefix': 'prefix',
            'vlan': 'vlan',
            'rack': 'rack',
            'cable': 'cable'
        }
        
        for phrase, object_type in object_mappings.items():
            if phrase in message_lower:
                result = create_tool.execute({'object_type': object_type})
                if result.get('success'):
                    return {
                        'tool': 'create_object',
                        'result': result
                    }
        
        return None
    
    def _try_search_tool(self, message: str, message_lower: str) -> Optional[Dict[str, Any]]:
        """Try to execute search tool based on message."""
        search_tool = self.mcp_registry.get_tool('search_nautobot')
        if not search_tool:
            return None
        
        # Extract search query (simple approach)
        search_patterns = ['search for ', 'find ', 'look for ']
        query = message.strip()
        
        for pattern in search_patterns:
            if pattern in message_lower:
                query = message[message_lower.index(pattern) + len(pattern):].strip()
                break
        
        if query and query != message.lower():
            result = search_tool.execute({'query': query})
            if result.get('success'):
                return {
                    'tool': 'search_nautobot',
                    'result': result
                }
        
        return None
    
    def _generate_ai_response(
        self,
        message: str,
        context: str,
        tool_results: List[Dict[str, Any]],
        user: Any
    ) -> Dict[str, Any]:
        """Generate response using AI/LLM."""
        
        # Prepare conversation messages
        messages = [
            {
                'role': 'user',
                'content': message
            }
        ]
        
        # Get available tools schema
        tools_schema = self.mcp_registry.get_tools_schema() if self.mcp_registry else []
        
        try:
            # Generate response using LLM
            llm_response = self.llm_client.generate_response(
                messages=messages,
                context=context,
                tools=tools_schema
            )
            
            # Process tool results into actions
            actions = []
            tools_used = []
            
            for tool_result in tool_results:
                tools_used.append(tool_result['tool'])
                
                if tool_result['result'].get('action'):
                    actions.append(tool_result['result']['action'])
            
            return {
                'text': llm_response.get('text', 'I apologize, but I could not generate a response.'),
                'actions': actions,
                'tools_used': tools_used,
                'context_sources': ['rag'] if context else [],
                'provider': llm_response.get('provider', 'generic'),
                'model': llm_response.get('model', 'unknown'),
                'usage': llm_response.get('usage', {}),
                'raw_response': llm_response.get('raw_response', {})
            }
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            # Fall back to rule-based response
            return self._generate_fallback_response(message, context, tool_results, user)
    
    def _generate_fallback_response(
        self,
        message: str,
        context: str,
        tool_results: List[Dict[str, Any]],
        user: Any
    ) -> Dict[str, Any]:
        """Generate fallback response using rule-based logic with RAG and tools."""
        
        message_lower = message.lower()
        actions = []
        tools_used = []
        
        # Process tool results
        for tool_result in tool_results:
            tools_used.append(tool_result['tool'])
            
            if tool_result['result'].get('action'):
                actions.append(tool_result['result']['action'])
        
        # Generate text response based on context and tools
        if actions:
            if any('navigate' in action.get('type', '') for action in actions):
                response_text = "I can help you navigate to the relevant page. Click the button below:"
            else:
                response_text = "I found some relevant actions for you:"
        elif context:
            # Use RAG context to provide informed response
            if 'device' in message_lower:
                response_text = "Based on the documentation: " + context[:300] + "..."
            elif 'circuit' in message_lower:
                response_text = "Here's what I found about circuits: " + context[:300] + "..."
            elif 'ip' in message_lower or 'ipam' in message_lower:
                response_text = "For IP address management: " + context[:300] + "..."
            else:
                response_text = "Here's relevant information from the documentation: " + context[:200] + "..."
        else:
            # Basic rule-based responses
            if any(word in message_lower for word in ['hello', 'hi', 'hey']):
                response_text = f"Hello{' ' + user.first_name if hasattr(user, 'first_name') and user.first_name else ''}! I'm Ben Bot, your Nautobot assistant. How can I help you today?"
            elif any(word in message_lower for word in ['help', 'what can you do']):
                response_text = "I can help you navigate Nautobot, find information about devices, circuits, IP addresses, and more. Try asking me about specific features or tell me what you're looking for!"
            else:
                response_text = "I'm here to help with Nautobot! You can ask me about devices, circuits, IP addresses, or navigation. What would you like to know?"
        
        return {
            'text': response_text,
            'actions': actions,
            'tools_used': tools_used,
            'context_sources': ['rag'] if context else [],
            'provider': 'rule_based_enhanced',
            'model': 'fallback'
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all AI components."""
        return {
            'ai_enabled': bool(self.llm_client and self.llm_client.is_available()),
            'rag_enabled': bool(self.rag_retriever and self.rag_retriever.is_initialized),
            'mcp_enabled': bool(self.mcp_registry),
            'api_enabled': bool(self.api_client and self.api_client.is_configured()),
            'components': {
                'llm_client': {
                    'configured': bool(self.llm_client),
                    'available': bool(self.llm_client and self.llm_client.is_available())
                },
                'rag_retriever': {
                    'configured': bool(self.rag_retriever),
                    'initialized': bool(self.rag_retriever and self.rag_retriever.is_initialized),
                    'stats': self.rag_retriever.get_stats() if self.rag_retriever else {}
                },
                'mcp_tools': {
                    'configured': bool(self.mcp_registry),
                    'tool_count': len(self.mcp_registry.tools) if self.mcp_registry else 0,
                    'available_tools': list(self.mcp_registry.tools.keys()) if self.mcp_registry else []
                },
                'api_client': {
                    'configured': bool(self.api_client),
                    'available': bool(self.api_client and self.api_client.is_configured())
                }
            },
            'configuration': {
                'ai_config': self.ai_config,
                'rag_config': self.rag_config,
                'mcp_config': self.mcp_config
            }
        }