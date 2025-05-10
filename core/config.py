# core/config.py
import os
import logging
import pkgutil
import importlib
from typing import List, Dict, Any
from dotenv import load_dotenv
from .base import ConfigLoader


load_dotenv()

logger = logging.getLogger(__name__)

_this_dir = os.path.dirname(__file__)
for _, module_name, _ in pkgutil.iter_modules([_this_dir]):

    if module_name in ("config", "base", "__init__"):
        continue
    if module_name.endswith("_loader"):
        importlib.import_module(f"{__package__}.{module_name}")

def load_mcp_servers() -> List[Dict[str, Any]]:
    """
    Recorre ConfigLoader.registry (ahora lleno tras los imports)
    e instancia cada loader para recoger su configuración.
    """
    servers: List[Dict[str, Any]] = []
    for loader_cls in ConfigLoader.registry:
        loader = loader_cls()
        cfg = loader.load()
        if cfg:
            servers.append(cfg)

    if not servers:
        logger.warning("No se encontró configuración para ningún servidor MCP")
    else:
        ids = [s["id"] for s in servers]
        logger.info(f"Servidores MCP cargados: {ids}")
    return servers


mcp_servers = load_mcp_servers()
