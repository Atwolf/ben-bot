"""
MCP tools for AI-assisted Nautobot interactions.
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MCPTool(ABC):
    """Base class for MCP tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize MCP tool.
        
        Args:
            name: Tool name
            description: Tool description for AI
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dict containing execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for AI consumption.
        
        Returns:
            JSON schema describing the tool
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.get_parameters_schema()
        }
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool."""
        pass


class NavigationTool(MCPTool):
    """Tool for generating navigation links to Nautobot pages."""
    
    # Navigation mappings for common Nautobot pages
    NAVIGATION_MAP = {
        # Organization
        'sites': {
            'url': '/dcim/sites/',
            'description': 'View all sites and locations'
        },
        'racks': {
            'url': '/dcim/racks/',
            'description': 'View all racks'
        },
        'devices': {
            'url': '/dcim/devices/',
            'description': 'View device inventory'
        },
        'device_types': {
            'url': '/dcim/device-types/',
            'description': 'View device types'
        },
        'device_roles': {
            'url': '/dcim/device-roles/',
            'description': 'View device roles'
        },
        'manufacturers': {
            'url': '/dcim/manufacturers/',
            'description': 'View manufacturers'
        },
        
        # IPAM
        'ip_addresses': {
            'url': '/ipam/ip-addresses/',
            'description': 'View IP addresses'
        },
        'prefixes': {
            'url': '/ipam/prefixes/',
            'description': 'View IP prefixes'
        },
        'vlans': {
            'url': '/ipam/vlans/',
            'description': 'View VLANs'
        },
        'vrfs': {
            'url': '/ipam/vrfs/',
            'description': 'View VRFs (Virtual Routing and Forwarding)'
        },
        
        # Circuits
        'circuits': {
            'url': '/circuits/circuits/',
            'description': 'View circuits'
        },
        'circuit_types': {
            'url': '/circuits/circuit-types/',
            'description': 'View circuit types'
        },
        'providers': {
            'url': '/circuits/providers/',
            'description': 'View circuit providers'
        },
        
        # Cables and Connections
        'cables': {
            'url': '/dcim/cables/',
            'description': 'View cable connections'
        },
        'interfaces': {
            'url': '/dcim/interfaces/',
            'description': 'View device interfaces'
        },
        
        # Admin and Configuration
        'users': {
            'url': '/admin/users/',
            'description': 'Manage users (admin only)'
        },
        'groups': {
            'url': '/admin/groups/',
            'description': 'Manage user groups (admin only)'
        },
        'api_tokens': {
            'url': '/users/api-tokens/',
            'description': 'Manage API tokens'
        },
        
        # Extras
        'tags': {
            'url': '/extras/tags/',
            'description': 'View and manage tags'
        },
        'custom_fields': {
            'url': '/extras/custom-fields/',
            'description': 'Manage custom fields'
        },
        'webhooks': {
            'url': '/extras/webhooks/',
            'description': 'Configure webhooks'
        }
    }
    
    def __init__(self):
        super().__init__(
            name='navigate_to_page',
            description='Generate navigation links to specific Nautobot pages'
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigation tool."""
        page_type = parameters.get('page_type', '').lower()
        
        if page_type in self.NAVIGATION_MAP:
            nav_info = self.NAVIGATION_MAP[page_type]
            return {
                'success': True,
                'action': {
                    'type': 'navigate',
                    'url': nav_info['url'],
                    'label': f"Go to {nav_info['description']}",
                    'description': nav_info['description']
                }
            }
        else:
            # Try to find partial matches
            matches = []
            for key, value in self.NAVIGATION_MAP.items():
                if page_type in key or page_type in value['description'].lower():
                    matches.append({
                        'key': key,
                        'url': value['url'],
                        'description': value['description']
                    })
            
            if matches:
                return {
                    'success': True,
                    'suggestions': matches,
                    'message': f'Found {len(matches)} possible matches for "{page_type}"'
                }
            else:
                return {
                    'success': False,
                    'message': f'No navigation found for "{page_type}". Available options: {", ".join(self.NAVIGATION_MAP.keys())}'
                }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for navigation tool."""
        return {
            'type': 'object',
            'properties': {
                'page_type': {
                    'type': 'string',
                    'description': f'Type of page to navigate to. Options: {", ".join(self.NAVIGATION_MAP.keys())}',
                    'enum': list(self.NAVIGATION_MAP.keys())
                }
            },
            'required': ['page_type']
        }


class SearchTool(MCPTool):
    """Tool for generating search queries within Nautobot."""
    
    def __init__(self):
        super().__init__(
            name='search_nautobot',
            description='Generate search actions for finding objects in Nautobot'
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search tool."""
        query = parameters.get('query', '').strip()
        search_type = parameters.get('search_type', 'global')
        
        if not query:
            return {
                'success': False,
                'message': 'Search query is required'
            }
        
        # Generate search URL based on type
        if search_type == 'global':
            search_url = f'/search/?q={query}'
            description = f'Search for "{query}" across all Nautobot objects'
        else:
            # Specific object type search
            type_map = {
                'devices': '/dcim/devices/',
                'sites': '/dcim/sites/',
                'circuits': '/circuits/circuits/',
                'ip_addresses': '/ipam/ip-addresses/',
                'prefixes': '/ipam/prefixes/'
            }
            
            if search_type in type_map:
                search_url = f'{type_map[search_type]}?q={query}'
                description = f'Search for "{query}" in {search_type}'
            else:
                search_url = f'/search/?q={query}'
                description = f'Search for "{query}" across all objects'
        
        return {
            'success': True,
            'action': {
                'type': 'navigate',
                'url': search_url,
                'label': f'Search for "{query}"',
                'description': description
            }
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for search tool."""
        return {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search query string'
                },
                'search_type': {
                    'type': 'string',
                    'description': 'Type of search to perform',
                    'enum': ['global', 'devices', 'sites', 'circuits', 'ip_addresses', 'prefixes'],
                    'default': 'global'
                }
            },
            'required': ['query']
        }


class CreateObjectTool(MCPTool):
    """Tool for generating links to create new objects in Nautobot."""
    
    # Object creation mappings
    CREATE_MAP = {
        'site': {
            'url': '/dcim/sites/add/',
            'description': 'Create a new site'
        },
        'device': {
            'url': '/dcim/devices/add/',
            'description': 'Create a new device'
        },
        'rack': {
            'url': '/dcim/racks/add/',
            'description': 'Create a new rack'
        },
        'circuit': {
            'url': '/circuits/circuits/add/',
            'description': 'Create a new circuit'
        },
        'ip_address': {
            'url': '/ipam/ip-addresses/add/',
            'description': 'Create a new IP address'
        },
        'prefix': {
            'url': '/ipam/prefixes/add/',
            'description': 'Create a new IP prefix'
        },
        'vlan': {
            'url': '/ipam/vlans/add/',
            'description': 'Create a new VLAN'
        },
        'cable': {
            'url': '/dcim/cables/add/',
            'description': 'Create a new cable connection'
        }
    }
    
    def __init__(self):
        super().__init__(
            name='create_object',
            description='Generate links to create new objects in Nautobot'
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create object tool."""
        object_type = parameters.get('object_type', '').lower()
        
        if object_type in self.CREATE_MAP:
            create_info = self.CREATE_MAP[object_type]
            return {
                'success': True,
                'action': {
                    'type': 'navigate',
                    'url': create_info['url'],
                    'label': create_info['description'],
                    'description': f'Navigate to form to {create_info["description"].lower()}'
                }
            }
        else:
            return {
                'success': False,
                'message': f'Cannot create object of type "{object_type}". Available types: {", ".join(self.CREATE_MAP.keys())}'
            }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for create object tool."""
        return {
            'type': 'object',
            'properties': {
                'object_type': {
                    'type': 'string',
                    'description': f'Type of object to create. Options: {", ".join(self.CREATE_MAP.keys())}',
                    'enum': list(self.CREATE_MAP.keys())
                }
            },
            'required': ['object_type']
        }


class MCPToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, MCPTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default MCP tools."""
        default_tools = [
            NavigationTool(),
            SearchTool(),
            CreateObjectTool()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: MCPTool):
        """Register a new tool."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Tool "{tool_name}" not found'
            }
        
        try:
            return tool.execute(parameters)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }