import httpx
from typing import Any, Dict
from .base import MCPAdapter

class HTTPMCPAdapter(MCPAdapter):
    """
    Represents an HTTP-based adapter for interacting with the MCP (Multi-tool Communication Protocol).

    This class enables communication with an MCP server over HTTP using JSON-RPC and provides methods for listing tools, invoking specific tools, and optionally handling server-sent events (SSE). The adapter is designed to simplify interaction with the MCP server while ensuring compatibility and extendability.

    Attributes
    ----------
    id : str
        A unique identifier for the HTTPMCPAdapter instance.
    base_url : str
        The base URL of the MCP server, which is used for making HTTP requests to various endpoints.

    Methods
    -------
    __init__(id: str, base_url: str)
        Initializes an instance of HTTPMCPAdapter with a unique identifier and base URL.

    list_tools() -> Dict[str, Any]
        Sends a JSON-RPC request via HTTP to list available tools on the MCP server.

    call_tool(tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]
        Invokes a specific tool on the MCP server using a POST request with the specified tool
        and its arguments.

    stream_events() -> Any
        Optionally listens to server-sent events (SSE) if supported by the server,
        raising NotImplementedError by default if not utilized.
    """
    def __init__(self, id: str, base_url: str):
        self.id = id
        self.base_url = base_url.rstrip("/")

    async def list_tools(self) -> Dict[str, Any]:
        """
        Fetches the list of tools from the remote service.

        This asynchronous method sends a POST request to a specific endpoint
        on the remote service to retrieve a list of available tools. The
        communication is performed in JSON-RPC format, and the returned
        response is parsed and returned as JSON.

        Returns:
            Dict[str, Any]: The JSON representation of the tools list
            provided by the remote service.

        Raises:
            httpx.HTTPStatusError: If the HTTP request encounters an error
            status.
        """
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{self.base_url}/call_tool", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def call_tool(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously sends a request to a tool with specified arguments and retrieves the response.

        This method constructs a payload based on the provided tool and arguments, then sends an
        asynchronous HTTP POST request to the tool service endpoint. The response is returned
        as a parsed JSON object.

        Parameters:
        tool: str
            The name of the tool to be called.
        arguments: Dict[str, Any]
            A dictionary containing the arguments to pass to the tool.

        Returns:
        Dict[str, Any]
            The parsed JSON response returned by the tool.

        Raises:
        httpx.HTTPError
            If the HTTP request fails or the response contains an HTTP error status code.
        """
        payload = {"tool": tool, "arguments": arguments}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/call_tool", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def stream_events(self) -> Any:
        """
        Raises a `NotImplementedError` for the `stream_events` method, indicating that
        Server-Sent Events (SSE) functionality is not implemented for the `HTTPMCPAdapter`.

        Returns
        -------
        Any
            This method does not return a value but raises a NotImplementedError.

        Raises
        ------
        NotImplementedError
            Raised when attempting to call the method, as SSE functionality is not
            implemented for the adapter.
        """
        raise NotImplementedError("SSE no implementado para HTTPMCPAdapter")
