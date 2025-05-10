import asyncio
import logging
from typing import List, Dict, Optional
from mcp_adapter.base import MCPAdapter

logger = logging.getLogger(__name__)

class MCPRegistry:
    """
    Manages a registry of MCPAdapters and their associated tools.

    Provides functionality for initializing the registry by discovering tools
    from a list of MCPAdapters in an asynchronous manner. Maintains a mapping
    between tool names and their respective adapters for quick retrieval.
    """
    def __init__(self, adapters: List[MCPAdapter]):
        self.adapters = adapters
        self.tool_map: Dict[str, MCPAdapter] = {}
        logger.info(f"MCPRegistry initialized with {len(adapters)} adapters")

    async def init(self):
        """
        Asynchronous initialization of tool discovery and registration processes for a system. This includes
        requesting tools from adapters, registering them in an internal mapping, and logging progress and
        errors encountered during the process.

        Methods
        -------
        init :
            Initiates the discovery process for tools across all registered adapters.

        _reg :
            Handles the registration of tools from a single adapter into the internal mapping.

        Attributes
        ----------
        tool_map : dict
            A mapping of tool names to their corresponding adapter instances.
        adapters : list
            A list of adapter instances from which tools will be requested.

        """
        logger.info("Initiating tool discovery process...")
        
        async def _reg(a: MCPAdapter):
            try:
                logger.info(f"requesting tools for {a.id}...")
                resp = await a.list_tools()
                
                if "result" in resp and "tools" in resp["result"]:
                    tools = resp["result"]["tools"]
                    logger.info(f"Adapter {a.id} returned {len(tools)} tools")
                    
                    for tool in tools:
                        name = tool.get("name")
                        if name:
                            self.tool_map[name] = a
                            #logger.info(f"Registered tool: {name}")
                else:
                    logger.warning(f"Response unexpected from {a.id}: {resp}")
            except Exception as e:
                logger.error(f"Error registing tools for {a.id}: {str(e)}")

        tasks = [_reg(a) for a in self.adapters]
        await asyncio.gather(*tasks)
        
        #for tool, adapter in self.tool_map.items():
            #logger.info(f"Tool {tool} asigned to adapter {adapter.id}")
        
        logger.info(f"Discovering completed: {len(self.tool_map)} tools registered")

    def get_adapter(self, tool_name: str) -> Optional[MCPAdapter]:
        """
        Retrieves the MCPAdapter associated with the given tool name.

        This method searches for the specified tool name within the internal
        tool_map dictionary and returns the corresponding MCPAdapter instance
        if it exists. If the tool name does not exist in the mapping, the method
        returns None.

        Parameters:
        tool_name: str
            The name of the tool for which the corresponding MCPAdapter should
            be retrieved.

        Returns:
        Optional[MCPAdapter]
            The MCPAdapter instance associated with the provided tool name,
            or None if the tool name is not found in the tool_map.
        """
        return self.tool_map.get(tool_name)

    def get_adapter_by_id(self, server_id: str) -> Optional[MCPAdapter]:
        """
        Fetches an adapter by its unique server identifier.

        This method iterates over the list of adapters to locate an adapter
        matching the provided server identifier. If an adapter with the
        specified identifier is found, it is returned. If no matching adapter
        is found, None is returned.

        Parameters:
            server_id: str
                The unique identifier of the server to look for.

        Returns:
            Optional[MCPAdapter]: The adapter object if a matching identifier
            is found; otherwise, None.
        """
        for a in self.adapters:
            if getattr(a, "id", None) == server_id:
                return a
        return None