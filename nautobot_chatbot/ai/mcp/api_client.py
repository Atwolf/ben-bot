"""
Nautobot API client for MCP tools.
Provides safe, rate-limited access to Nautobot's REST API.
"""

# Standard library imports
import logging
import time
from typing import Any, Dict, Optional

# Third-party imports
import requests

# Local imports
from ..config import AIConfig

logger = logging.getLogger(__name__)


class NautobotAPIClient:
    """
    Safe, rate-limited client for Nautobot REST API.

    This client provides controlled access to Nautobot data
    with proper authentication and rate limiting.
    """

    def __init__(self):
        """Initialize API client with configuration."""
        self.config = AIConfig.get_mcp_config()
        self.base_url = self.config.get("nautobot_api_base", "http://localhost:8000/api")
        self.api_token = self.config.get("nautobot_api_token", "")
        self.rate_limit = self.config.get("api_rate_limit", 10)  # requests per minute

        # Rate limiting tracking
        self.request_times = []

        # Setup session
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update(
                {
                    "Authorization": f"Token {self.api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )

    def is_configured(self) -> bool:
        """Check if API client is properly configured."""
        return bool(self.base_url and (self.api_token or self._is_local_request()))

    def _is_local_request(self) -> bool:
        """Check if this is a local request that might not need authentication."""
        return "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        minute_ago = now - 60

        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if t > minute_ago]

        # Check if we're within rate limit
        return len(self.request_times) < self.rate_limit

    def _record_request(self):
        """Record a request for rate limiting."""
        self.request_times.append(time.time())

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a safe API request with rate limiting and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional request arguments

        Returns:
            API response data
        """
        if not self.is_configured():
            return {
                "error": "Nautobot API not configured. Set NAUTOBOT_API_BASE and NAUTOBOT_API_TOKEN.",
                "configured": False,
            }

        if not self._check_rate_limit():
            return {
                "error": f"Rate limit exceeded ({self.rate_limit} requests per minute)",
                "rate_limited": True,
            }

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            self._record_request()

            response = self.session.request(method, url, timeout=10, **kwargs)

            if response.status_code == 401:
                return {"error": "Authentication failed. Check API token.", "status_code": 401}
            elif response.status_code == 403:
                return {"error": "Access denied. Check user permissions.", "status_code": 403}
            elif response.status_code == 404:
                return {"error": "API endpoint not found.", "status_code": 404, "url": url}
            elif not response.ok:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "status_code": response.status_code,
                    "url": url,
                }

            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "error": "Cannot connect to Nautobot API. Check if Nautobot is running.",
                "connection_error": True,
            }
        except requests.exceptions.Timeout:
            return {"error": "API request timed out.", "timeout": True}
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {"error": f"Unexpected error: {str(e)}", "exception": True}

    def get_devices(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get devices from Nautobot API.

        Args:
            limit: Maximum number of devices to return
            filters: Optional filters to apply

        Returns:
            API response with device data
        """
        params = {"limit": min(limit, 50)}  # Cap at 50 for safety

        if filters:
            params.update(filters)

        return self._make_request("GET", "dcim/devices/", params=params)

    def get_sites(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get sites from Nautobot API."""
        params = {"limit": min(limit, 50)}

        if filters:
            params.update(filters)

        return self._make_request("GET", "dcim/sites/", params=params)

    def get_circuits(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get circuits from Nautobot API."""
        params = {"limit": min(limit, 50)}

        if filters:
            params.update(filters)

        return self._make_request("GET", "circuits/circuits/", params=params)

    def get_ip_addresses(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get IP addresses from Nautobot API."""
        params = {"limit": min(limit, 50)}

        if filters:
            params.update(filters)

        return self._make_request("GET", "ipam/ip-addresses/", params=params)

    def get_prefixes(
        self, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get IP prefixes from Nautobot API."""
        params = {"limit": min(limit, 50)}

        if filters:
            params.update(filters)

        return self._make_request("GET", "ipam/prefixes/", params=params)

    def search_objects(
        self, query: str, object_type: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for objects in Nautobot.

        Args:
            query: Search query
            object_type: Optional object type to search within
            limit: Maximum results

        Returns:
            Search results
        """
        if object_type:
            # Search within specific object type
            type_map = {
                "devices": "dcim/devices/",
                "sites": "dcim/sites/",
                "circuits": "circuits/circuits/",
                "ip_addresses": "ipam/ip-addresses/",
                "prefixes": "ipam/prefixes/",
            }

            if object_type in type_map:
                endpoint = type_map[object_type]
                params = {"q": query, "limit": min(limit, 20)}
                return self._make_request("GET", endpoint, params=params)
            else:
                return {"error": f"Unsupported object type: {object_type}"}
        else:
            # Global search - would need to implement based on Nautobot's search API
            return {"error": "Global search not implemented. Specify object_type."}

    def get_object_count(self, object_type: str) -> Dict[str, Any]:
        """
        Get count of objects for a specific type.

        Args:
            object_type: Type of object to count

        Returns:
            Object count information
        """
        type_map = {
            "devices": "dcim/devices/",
            "sites": "dcim/sites/",
            "circuits": "circuits/circuits/",
            "ip_addresses": "ipam/ip-addresses/",
            "prefixes": "ipam/prefixes/",
            "racks": "dcim/racks/",
            "vlans": "ipam/vlans/",
        }

        if object_type not in type_map:
            return {"error": f"Unsupported object type: {object_type}"}

        # Get just the count by requesting with limit=1
        response = self._make_request("GET", type_map[object_type], params={"limit": 1})

        if "error" in response:
            return response

        return {
            "object_type": object_type,
            "count": response.get("count", 0),
            "endpoint": type_map[object_type],
        }

    def get_api_info(self) -> Dict[str, Any]:
        """Get API information and status."""
        response = self._make_request("GET", "")

        if "error" not in response:
            return {
                "status": "connected",
                "api_version": response.get("api_version", "unknown"),
                "nautobot_version": response.get("nautobot_version", "unknown"),
                "base_url": self.base_url,
            }
        else:
            return {
                "status": "error",
                "error": response.get("error"),
                "base_url": self.base_url,
                "configured": self.is_configured(),
            }
