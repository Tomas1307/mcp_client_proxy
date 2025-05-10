from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class CallToolRequest(BaseModel):
    """
    Request body para POST /call_tool.
    - tool: nombre de la herramienta a invocar.
    - arguments: diccionario con los parámetros de esa herramienta.
    - server_id: (opcional) ID del servidor MCP específico a usar.
    """
    tool: str = Field(..., description="Name of the MCP tool")
    arguments: Dict[str, Any] = Field(default={}, description="Input parameters for the tool")
    server_id: Optional[str] = Field(None, description="ID of the specific MCP server to use (optional)")