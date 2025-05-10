import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import mcp_servers
from mcp_adapter.stdio_adapter import StdIOAdapter
from mcp_adapter.http_adapter import HTTPMCPAdapter
from services.registry import MCPRegistry
from api.router import router
from dotenv import load_dotenv
import os


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Multi-Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup():
    """Evento de inicio."""
    logger.info("Iniciando aplicación")
    
    adapters = []
    for s in mcp_servers:
        if s["type"] == "stdio":
            logger.info(f"Creando StdIOAdapter para {s['id']}")
            adapters.append(
                StdIOAdapter(
                    id=s["id"],
                    image=s["image"],
                    docker_args=s.get("docker_args", [])
                )
            )
        elif s["type"] == "http":
            logger.info(f"Creando HTTPMCPAdapter para {s['id']}")
            adapters.append(
                HTTPMCPAdapter(
                    id=s["id"],
                    base_url=s["base_url"]
                )
            )
    
    logger.info(f"Inicializando registry con {len(adapters)} adaptadores")
    registry = MCPRegistry(adapters)
    
    await registry.init()
    logger.info(f"Registry inicializado: {len(registry.tool_map)} herramientas disponibles")
    
    app.state.registry = registry

@app.on_event("shutdown")
async def shutdown():
    """Evento de cierre."""
    logger.info("Cerrando aplicación")
    
    if hasattr(app.state, "registry"):
        for adapter in app.state.registry.adapters:
            if hasattr(adapter, 'process') and adapter.process is not None:
                logger.info(f"Terminando proceso del adaptador {adapter.id}")
                adapter.process.terminate()

@app.get("/")
async def root():
    adapters_info = []
    
    if hasattr(app.state, "registry"):
        registry = app.state.registry
        for adapter in registry.adapters:
            status = "unknown"
            if hasattr(adapter, 'process'):
                if adapter.process is None:
                    status = "not_running"
                elif adapter.process.poll() is None:
                    status = "running"
                else:
                    status = "exited"
            
            adapter_info = {
                "id": adapter.id,
                "type": adapter.__class__.__name__,
                "status": status
            }
            
            if hasattr(adapter, "image"):
                adapter_info["image"] = adapter.image
            
            adapters_info.append(adapter_info)
    
    return {
        "status": "online",
        "mcp_adapter": adapters_info,
        "tools_available": len(app.state.registry.tool_map) if hasattr(app.state, "registry") else 0,
        "documentation": "Para utilizar correctamente el GitHub MCP Server, asegúrate de configurar la imagen y los toolsets adecuados."
    }