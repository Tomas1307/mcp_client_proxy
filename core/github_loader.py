
import os
from .base import ConfigLoader, logger

class GitHubLoader(ConfigLoader):
    def load(self):
        """
        Load configuration for a GitHub MCP Server using environment variable.

        This function retrieves the GitHub Personal Access Token from the
        environment, validates its existence, and prepares the server
        configuration. The function logs a relevant message and returns a dictionary
        representing the server configurations.

        Returns:
            dict | None: A dictionary containing server configuration details such
            as id, type, image, and Docker arguments if the access token is found,
            otherwise None.
        """
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not token:
            return None
        logger.info("Añadiendo MCP-Server de GitHub")
        return {
            "id": "github",
            "type": "stdio",
            "image": "ghcr.io/github/github-mcp-server",
            "docker_args": [
                "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={token}",
                "-e", "GITHUB_TOOLSETS=all",
            ],
        }
