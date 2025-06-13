from typing import Dict, Any, List, Optional
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class ToolExtractor:
    
    def __init__(self, mcp_base_url: str = "http://localhost:8003"):
        self.mcp_url = mcp_base_url
        self._tools_cache: Optional[Dict[str, Any]] = None
    
    
    async def get_all_tools(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch all available tools from MCP proxy
        
        Returns:
            Dict containing all tools organized by server
        """
        if use_cache and self._tools_cache is not None:
           return self._tools_cache
       
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.mcp_url}/tools/list")
                response.raise_for_status()
                self._tools_cache = response.json()
                return self._tools_cache
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch tools: {e.response.status_code} - {e.response.text}")
                raise
            
            
    async def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific tool by name
        
        Args:
            tool_name (str): Name of the tool to fetch
            
        Returns:
            Dict containing tool details or None if not found
        """
        tools = await self.get_all_tools()
        return tools.get(tool_name, None)
    
    async def get_tool_details(self, tool_name: str) -> Optional[Dict[str,Any]]:
        """
        Get details for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool details if found, None otherwise
        """
        all_tools = await self.get_all_tools()
        
        for server_id, server_tools in all_tools.items():
            if isinstance(server_tools, dict) and tool_name in server_tools:
                
                tool_info = server_tools[tool_name]
                tool_info["server_name"] = server_id
                return tool_info
            
        return None
    
    
    async def get_tools_names(self, server_name: str) -> List[str]:
        """

        Args:
            server_name (str):

        Returns:
            List[str]: List of tool names available on the specified server
        """
        tools = []
        all_tools = await self.get_all_tools()
        tools_server = all_tools.get(server_name, {})
        for tool in tools_server:
            if isinstance(tools_server[tool], dict):
                tools.append(tool)
        return tools
    
    async def get_tools_list_flat(self) -> List[Dict[str, Any]]:
       """
       Get a flat list of all tools with server information
       
       Returns:
           List of tool dictionaries with server_id included
       """
       all_tools = await self.get_all_tools()
       flat_list = []
       
       for server_id, server_tools in all_tools.items():
           if isinstance(server_tools, dict) and "error" not in server_tools:
               for tool_name, tool_info in server_tools.items():
                   if isinstance(tool_info, dict):
                       tool_data = {
                           "name": tool_name,
                           "server_id": server_id,
                           **tool_info
                       }
                       flat_list.append(tool_data)
       
       return flat_list
                
    def clear_cache(self):
        """Clear the tools cache"""
        self._tools_cache = None      
            
async def main():
    extractor = ToolExtractor(mcp_base_url="http://localhost:8003")
    server_name = "google-maps"
    tools = await extractor.get_tools_names(server_name=server_name)
    #print(f"Herramientas disponibles de github:", tools)
    print(f"""Generate a concise and comprehensive description of **{server_name}** as a tool, detailing its **core capabilities** and the **specific functionalities** it offers. The description should be detailed enough to capture the essence of the tool and its uses, yet direct to facilitate the creation of embeddings.
            Include the following information:
            1.  **General overview of {server_name}**: What it is and its primary purpose.

            2.  **Key use cases**: Examples of scenarios where {server_name} is indispensable (e.g., version control, team collaboration, software project management).

            3.  **Available functionalities**: Mention the following specific tools/actions that can be performed with {server_name}:

            {tools}

            Ensure the description is coherent, flows naturally, and that the functionalities are integrated seamlessly into the text, highlighting their purpose. 
            
            Return it as a json object with the following structure:
            ```json
            {{
                "name": "{server_name}",
                "description": "Your detailed description here"
            }}
            ```""")

if __name__ == "__main__":
    asyncio.run(main())
