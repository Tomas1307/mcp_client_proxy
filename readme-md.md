# MCP Client Proxy

This project implements a FastAPI-based proxy service for MCP (Multi-tool Communication Protocol) servers. It provides a unified interface to interact with various MCP servers through standardized adapters, supporting both stdio (Docker container-based) and HTTP interfaces.

VIDEO LINK -> https://www.loom.com/share/cab5866f0c6e48a9bc5b3555a7d00566?sid=5980e45c-dbf4-44ed-94c4-49b01651e962

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Testing Cases](#testing-cases)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Adding New MCP Servers](#adding-new-mcp-servers)
- [Future Improvements](#future-improvements)
- [Technical Decisions](#technical-decisions)

## Installation

### Prerequisites

- Python 3.11
- Docker (for stdio adapters)
- Access to MCP servers and their API keys

### Setup

1. Clone the repository
2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

Create a `.env` file in the root directory with the required API keys:

```
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
BRAVE_API_KEY=your_brave_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

5. Creating de uvicorn port as localhost:

```
uvicorn main:app --reload --port 8003
```

6. Testing endpoints on powershell or postman


## Testing Cases

Below are example test cases that can be used with Postman or any other HTTP client to test the MCP Client Proxy:

### GET /tools/list

This endpoint lists all available tools from all registered adapters:

```
GET http://127.0.0.1:8000/tools/list
```

The response will be a JSON object containing tools organized by server ID.

### POST /call_tool

This endpoint is used to call specific tools with arguments. Below are several example test cases:

#### Test 1: GitHub - Get authenticated user information

```
POST http://127.0.0.1:8000/call_tool
Content-Type: application/json

{
  "tool": "get_me",
  "arguments": {}
}
```

#### Test 2: GitHub - Search repositories

```
POST http://127.0.0.1:8000/call_tool
Content-Type: application/json

{
  "tool": "search_repositories",
  "arguments": {
    "query": "fastapi"
  }
}
```

#### Test 3: Brave Search - Web search with server_id specified

```
POST http://127.0.0.1:8000/call_tool
Content-Type: application/json

{
  "tool": "brave_web_search",
  "arguments": {
    "query": "climate change solutions",
    "count": 10,
    "offset": 2
  },
  "server_id": "brave-search"
}
```

#### Test 4: Google Maps - Geocode an address

```
POST http://127.0.0.1:8000/call_tool
Content-Type: application/json

{
  "tool": "maps_geocode",
  "arguments": {
    "address": "1600 Amphitheatre Parkway, Mountain View, CA"
  },
  "server_id": "google-maps"
}
```

### GET /status/{server_id}

Check the status of a specific server:

```
GET http://127.0.0.1:8000/status/github
```

### GET /ping/{server_id}

Ping a specific server to check its availability:

```
GET http://127.0.0.1:8000/ping/brave-search
```

## Configuration

The application loads its configuration from environment variables. For testing purposes, you'll need to set the following variables:

```
GITHUB_PERSONAL_ACCESS_TOKEN=1
BRAVE_API_KEY=2
GOOGLE_MAPS_API_KEY=3
```

These are placeholder values for testing. You have to write the correct api_key. For security im not shearing mine.

## Architecture

The application follows a modular architecture:

- **Core**: Configuration loaders and infrastructure setup
- **API**: FastAPI routes and schemas for endpoint handling
- **MCP Adapter**: Base adapter class and specific implementations (stdio, http)
- **Services**: Registry for managing adapters and their tools

The application initializes a registry of adapters based on configured MCP servers, each adapter handling communication with a specific MCP server. The registry maps tools to their respective adapters, enabling the proxy to route calls to the appropriate server.

### Key Components

- **ConfigLoader**: Abstract base class for loading MCP server configurations
- **MCPAdapter**: Abstract base class for adapter implementations
- **StdIOAdapter**: Adapter for Docker container-based MCP servers using stdin/stdout
- **HTTPMCPAdapter**: Adapter for HTTP-based MCP servers
- **MCPRegistry**: Registry for managing adapters and their tools

## API Endpoints

The application exposes the following endpoints:

- **GET /**: Returns the status of the application and available adapters
- **GET /sse/{server_id}**: Streams Server-Sent Events (SSE) for a specific server
- **GET /tools/list**: Lists available tools from all adapters
- **GET /status/{server_id}**: Gets the status of a specific server
- **GET /ping/{server_id}**: Pings a specific server
- **POST /call_tool**: Calls a specific tool with provided arguments
- **GET /debug/servers**: Gets debug information about all registered servers
- **POST /debug/direct_call**: Simulates a direct JSON-RPC call to a StdIOAdapter server

But for the purpose of the test you must only use:

- **GET /tools/list**: Lists available tools from all adapters
- **POST /call_tool**: Calls a specific tool with provided arguments

## Adding New MCP Servers

To add a new MCP server, follow these steps:

1. Create a new loader file in the `core` directory following the pattern of existing loaders (e.g., `brave_search_loader.py`)
2. Implement the `ConfigLoader` class, providing a `load` method that returns the server configuration
3. Ensure the loader reads the API key from environment variables

Example:

```python
import os
from .base import ConfigLoader, logger

class NewServiceLoader(ConfigLoader):
    def load(self):
        key = os.getenv("NEW_SERVICE_API_KEY")
        if not key:
            return None
            
        logger.info("Adding New Service MCP-Server")
        return {
            "id": "new-service",
            "type": "stdio",  # or "http" for HTTP-based servers
            "image": "mcp/new-service",  # Docker image for stdio adapters
            "docker_args": ["-e", f"NEW_SERVICE_API_KEY={key}"],
            # For HTTP adapters, use "base_url" instead of "image" and "docker_args"
        }
```

## Future Improvements

1. **Enhanced Adapter Support**: Extend beyond Docker containers to support other types of MCP servers. Currently, the system only works with Docker containers, limiting its flexibility.

2. **Authentication and Security**: Implement robust authentication for the API endpoints and secure storage for API keys.

3. **Monitoring and Metrics**: Add comprehensive monitoring for adapter health, tool usage, and performance metrics.

4. **Caching Layer**: Implement caching for frequent tool calls to improve performance.

5. **Configurable Rate Limiting**: Add rate limiting for API endpoints and tool calls to prevent abuse.

6. **Enhanced Error Handling**: Improve error reporting and recovery mechanisms for adapter failures.

7. **SDK/Client Libraries**: Develop client libraries for common programming languages to simplify integration.

8. **WebSocket Support**: Add WebSocket support for real-time bidirectional communication.

9. **Interactive Documentation**: Enhance API documentation with interactive examples.

10. **Containerization**: Provide Docker Compose setup for easy deployment.

## Technical Decisions

### Choice of FastAPI

FastAPI was chosen for its asynchronous capabilities, which align well with the nature of handling multiple adapters and potentially long-running tool calls. Its built-in OpenAPI documentation also simplifies API exploration.

### Adapter Pattern

The adapter pattern was implemented to provide a consistent interface for different types of MCP servers. This allows for easy extension and maintenance as new server types are added.

### Registry Design

The MCPRegistry acts as a central repository for adapters and their tools, enabling efficient routing of tool calls to the appropriate server. This design allows for dynamic discovery of tools across multiple adapters.

### Standard I/O Adapter

The StdIOAdapter was designed to wrap Docker container-based MCP servers in an HTTP protocol, which was a challenging but essential feature to meet the requirements of the technical test. This adapter handles the complexities of communicating with Docker containers over stdin/stdout, providing a clean interface for the rest of the application.

### Future Scalability

The architecture was designed with scalability in mind, allowing for easy addition of new MCP servers by simply adding new loaders in the core directory and providing the appropriate API keys.

## Project Report

### What improvements would I add with more time?

I would like to make the system even more generalized because currently, it only works with Docker containers. This limits its flexibility for MCP servers that might not have a container available. Additional improvements could include:

- Better error handling and recovery mechanisms
- Comprehensive logging and monitoring
- User authentication and access control
- Performance optimizations for high-throughput scenarios
- A web-based dashboard for viewing adapter status and tool availability

### Which parts am I most proud of? And why?

I'm really proud of the core/ module and the StdIOAdapter implementation. It wasn't easy trying to wrap Docker container communication into an HTTP protocol. All the Docker files are being executed in stdio, and managing to wrap that as an HTTP service was essential to meet the requirements of the technical test. Other libraries were using different approaches, so creating a consistent interface was challenging but rewarding.

### Which parts did I spend the most time on? What did I find most difficult?

I spent most of my time on the StdIOAdapter, ensuring it could reliably communicate with Docker containers and handle the various edge cases that arose. Making the system as scalable as possible was also time-consuming, ensuring that adding new MCP servers only required writing the API key in the environment and adding a loader file in the core directory.

### How did I find the test overall?

The test was challenging as it required creating an MCP client, which is different from the REST architecture I'm more accustomed to. However, it was a good learning experience. I think the test was well-designed, although as someone interested in the role, I might have enjoyed something more closely related to fine-tuning an LLM or using a model from Hugging Face.
