from abc import ABC, abstractmethod
from typing import Any, Dict

class MCPAdapter(ABC):
    """
    Defines an abstract base class (ABC) called MCPAdapter.

    This class provides an interface for managing tools through asynchronous
    operations. It serves as a foundation for tool listing and invoking functionality.
    The specific implementation of the methods are left for"""
    @abstractmethod
    async def list_tools(self) -> Dict[str, Any]:
        """
        Provides an abstract method for asynchronously listing tools.

        Methods
        -------
        list_tools()
            Abstract method that retrieves a dictionary of tools. The structure
            and content of the dictionary remain implementation-specific.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing tools data, where the keys are strings and
            values can be of any type.

        """


    @abstractmethod
    async def call_tool(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
            Provides an abstract method for calling tools with specified arguments
            and returning a dictionary response.

            @param tool: The name of the tool to be called.
            @type tool: str
            @param arguments: A dictionary containing key-value pairs of arguments
            to be passed to the tool.
            @type arguments: Dict[str, Any]
            @return: A dictionary containing the response from the tool's execution.
            @rtype: Dict[str, Any]
        """
