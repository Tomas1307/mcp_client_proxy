import os
from .base import ConfigLoader, logger


class GoogleMapsLoader(ConfigLoader):
    def load(self):
        """
        Loads and configures the Google Maps MCP-Server, utilizing the API key from the
        environment variables. If the API key is not available in the environment, the
        method returns None. On a successful load, it provides the necessary configuration
        dictionary to initialize the server.

        Returns
        -------
        dict or None
            A dictionary containing the configuration for the Google Maps MCP-Server if
            the API key is found; otherwise, None.
        """
        from .config import API_IDS
        key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not key:
            return None
        logger.info("Añadiendo MCP-Server de Google Maps")
        return {
            "id": API_IDS["google_maps"],
            "type": "stdio",
            "image": "mcp/google-maps",
            "docker_args": ["-e", f"GOOGLE_MAPS_API_KEY={key}"],
        }
