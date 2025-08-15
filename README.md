# Ben Bot - Nautobot Chatbot Plugin

A sophisticated AI-powered chatbot plugin for Nautobot that provides intelligent assistance with network infrastructure management through persistent chat sessions, RAG-powered documentation access, and contextual navigation tools.

## 🚀 Features

### Core Features
- **Persistent Chat Sessions**: Maintains conversation context across different Nautobot pages and browser sessions
- **Dual Interface**: Both overlay chatbot and dedicated full-page chat interface
- **User-Specific Sessions**: Secure, isolated chat sessions for each user
- **Real-time Responses**: Live typing indicators and instant message delivery

### AI-Powered Capabilities
- **Multi-Provider Support**: Compatible with OpenAI, Anthropic, and custom AI APIs
- **RAG System**: Retrieval-Augmented Generation using Nautobot documentation for context-aware responses
- **MCP Tools Integration**: Model Context Protocol tools for navigation, search, and object creation
- **Rich Response UI**: Interactive action buttons, metadata display, and structured data presentation
- **Fallback System**: Works with basic rule-based responses when AI is not configured

### Advanced Features
- **Smart Intent Detection**: Automatically identifies user intentions and executes relevant tools
- **Performance Monitoring**: Response time tracking, token usage, and system health metrics
- **Rate Limiting**: Built-in API rate limiting for safe external service integration
- **Flexible Configuration**: Support for Django settings, environment variables, and runtime configuration

## 📦 Installation

### Prerequisites
- Nautobot 2.0+
- Python 3.8+
- (Optional) AI provider API keys for enhanced features

### Install Plugin

```bash
# Clone the repository
git clone https://github.com/your-repo/ben-bot.git
cd ben-bot

# Install in development mode
pip install -e .

# Or install from PyPI (when published)
pip install nautobot-chatbot
```

### Configure Nautobot

Add to your `nautobot_config.py`:

```python
PLUGINS = [
    "nautobot_chatbot",
    # ... other plugins
]

# Optional: Advanced configuration
PLUGINS_CONFIG = {
    "nautobot_chatbot": {
        # See Configuration section below
    }
}
```

### Run Migrations

```bash
nautobot-server migrate
nautobot-server collectstatic --noinput
```

### Restart Nautobot

```bash
nautobot-server runserver  # or your production restart command
```

## ⚙️ Configuration

### Quick Start (Basic Chatbot)
No additional configuration needed! The plugin works immediately with rule-based responses.

### AI-Enhanced Configuration

#### Method 1: Django Settings (Recommended)

```python
PLUGINS_CONFIG = {
    "nautobot_chatbot": {
        "ai_config": {
            "enabled": True,
            "provider": "openai",  # or "anthropic", "generic"
            "api_base_url": "https://api.openai.com/v1",
            "api_key": "sk-your-api-key-here",
            "model_name": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.7,
            "timeout": 30
        },
        "rag_config": {
            "enabled": True,
            "embedding_provider": "sentence_transformers",
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "max_results": 5,
            "similarity_threshold": 0.7
        },
        "mcp_config": {
            "enabled": True,
            "nautobot_api_base": "http://localhost:8000/api",
            "nautobot_api_token": "your-nautobot-api-token",
            "api_rate_limit": 10,  # requests per minute
            "enabled_tools": ["navigate_to_page", "search_nautobot", "create_object"]
        }
    }
}
```

#### Method 2: Environment Variables

```bash
# AI Configuration
export AI_PROVIDER_ENABLED=true
export AI_PROVIDER=openai
export AI_API_ENDPOINT=https://api.openai.com/v1
export AI_API_KEY=sk-your-api-key-here
export AI_MODEL_NAME=gpt-4
export AI_TEMPERATURE=0.7
export AI_MAX_TOKENS=1000

# RAG Configuration
export RAG_ENABLED=true
export RAG_EMBEDDING_PROVIDER=sentence_transformers
export RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
export RAG_CHUNK_SIZE=1000

# MCP Configuration
export MCP_TOOLS_ENABLED=true
export NAUTOBOT_API_BASE=http://localhost:8000/api
export NAUTOBOT_API_TOKEN=your-nautobot-api-token
export MCP_API_RATE_LIMIT=10
```

### Provider-Specific Examples

#### OpenAI Configuration
```python
"ai_config": {
    "enabled": True,
    "provider": "openai",
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-your-openai-key",
    "model_name": "gpt-4",
    "temperature": 0.7
}
```

#### Anthropic Configuration
```python
"ai_config": {
    "enabled": True,
    "provider": "anthropic",
    "api_base_url": "https://api.anthropic.com",
    "api_key": "your-anthropic-key",
    "model_name": "claude-3-sonnet-20240229",
    "temperature": 0.7
}
```

#### Custom API Configuration
```python
"ai_config": {
    "enabled": True,
    "provider": "generic",
    "api_base_url": "https://your-api.example.com/v1",
    "api_key": "your-custom-key",
    "model_name": "your-model",
    "request_headers": {
        "Authorization": "Bearer your-token",
        "Custom-Header": "value"
    }
}
```

## 🎯 Usage Examples

### Basic Interaction
```
User: "Hello, how can you help me?"
Bot: "Hello! I'm Ben Bot, your Nautobot assistant. I can help you navigate 
      Nautobot, find information about devices, circuits, IP addresses, and more."
```

### AI-Enhanced Navigation
```
User: "Show me all devices"
Bot: "I can help you navigate to the devices page."
     [🔗 View Devices] button appears
     Click → navigates to /dcim/devices/
```

### RAG-Powered Documentation Help
```
User: "How do I configure a new site?"
Bot: "Based on the documentation: Sites in Nautobot represent physical 
      locations where network equipment is installed. To create a site..."
     [➕ Create Site] [📖 View Documentation] buttons appear
```

### MCP Tool Integration
```
User: "Find devices in the datacenter"
Bot: "I found 15 devices in datacenter locations:"
     • Device1 (Active) - 192.168.1.1
     • Device2 (Active) - 192.168.1.2
     [🔍 Search More] [📊 View Details] buttons appear
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │◄──►│   Django Views  │◄──►│   AI Engine     │
│                 │    │                 │    │                 │
│ • Chat Overlay  │    │ • Chat API      │    │ • LLM Client    │
│ • Full Page     │    │ • History API   │    │ • RAG System    │
│ • Rich Actions  │    │ • Session API   │    │ • MCP Tools     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **AI Engine**: Central orchestrator combining LLM, RAG, and MCP components
2. **LLM Client**: Generic interface for various AI providers
3. **RAG System**: Document retrieval and vectorization for context-aware responses
4. **MCP Tools**: Contextual actions and navigation helpers
5. **Frontend**: Rich UI with action buttons and metadata display

## 📊 Monitoring & Status

### Health Check Endpoint
```bash
curl http://localhost:8000/plugins/chatbot/api/status/
```

Visit `/plugins/chatbot/api/status/` to check:
- AI component status
- Configuration validation
- Component health checks
- Performance metrics

## 🔧 Development

### Custom AI Provider Integration

Extend the `GenericLLMClient` for your provider:

```python
# In nautobot_chatbot/ai/llm_client.py

def _prepare_request(self, messages, context=None, tools=None):
    """Customize for your API format"""
    return {
        "model": self.config['model_name'],
        "messages": messages,
        "temperature": self.config['temperature'],
        # Add provider-specific fields
    }

def _parse_response(self, response_data):
    """Parse your provider's response"""
    return {
        'text': response_data.get('your_text_field', ''),
        'usage': response_data.get('usage', {}),
        'provider': self.config.get('provider', 'custom')
    }
```

### Adding Custom MCP Tools

```python
# In nautobot_chatbot/ai/mcp/tools.py

class CustomTool(MCPTool):
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom logic here
        return {
            'success': True,
            'message': 'Custom action completed',
            'action': {
                'type': 'custom',
                'text': 'View Results',
                'url': '/custom/results/'
            }
        }
```

## 🚨 Troubleshooting

### Common Issues

#### Chat Interface Not Appearing
1. Check plugin installation: `nautobot-server check`
2. Verify migrations: `nautobot-server showmigrations nautobot_chatbot`
3. Check static files: `nautobot-server collectstatic`

#### AI Features Not Working
1. Verify configuration: Visit `/plugins/chatbot/api/status/`
2. Check API credentials and endpoints
3. Review logs for error messages

#### Configuration Validation
```python
from nautobot_chatbot.ai.config import AIConfig
status = AIConfig.validate_configuration()
print(status)
```

## 📄 API Reference

### Chat API
```http
POST /plugins/chatbot/api/chat/
{
    "message": "How do I add a new device?",
    "session_id": "optional-session-id"
}
```

### Status API
```http
GET /plugins/chatbot/api/status/
```

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/your-repo/ben-bot.git
cd ben-bot
pip install -e .
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Nautobot team for the excellent platform
- OpenAI and Anthropic for AI capabilities
- sentence-transformers for embeddings
- The open-source community for tools and inspiration