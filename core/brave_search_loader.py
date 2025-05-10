
import os
from .base import ConfigLoader, logger

class BraveSearchLoader(ConfigLoader):
    def load(self):
        """
        Loads the Brave Search MCP-Server configuration.

        This function retrieves the API key required for the Brave Search MCP-Server
        from the environment variables. If the API key is not found, the function
        returns None. Otherwise, it constructs a configuration dictionary to set up
        a MCP-Server with specific parameters.

        Returns
        -------
        dict or None
            Returns a configuration dictionary containing the ID, type, image, and
            Docker arguments for the Brave Search MCP-Server if the API key is found.
            Returns None if the API key is not found.
        """
        key = os.getenv("BRAVE_API_KEY")
        if not key:
            return None

        logger.info("Añadiendo MCP‑Server de Brave Search")
        return {
            "id": "brave-search",
            "type": "stdio",
            "image": "mcp/brave-search",
            "docker_args": [
                "-e", f"BRAVE_API_KEY={key}"
            ],
        }
