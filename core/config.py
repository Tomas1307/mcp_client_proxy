import os
import logging
import pkgutil
import importlib
from typing import List, Dict, Any
from dotenv import load_dotenv
from .base import ConfigLoader
import yaml

load_dotenv()

logger = logging.getLogger(__name__)

_this_dir = os.path.dirname(__file__)
_project_root = os.path.join(_this_dir, "..")
CONFIG_YAML_PATH = os.path.join(_project_root, 'config.yaml')

API_IDS: Dict[str, str] = {}

def load_api_ids_from_yaml():
    global API_IDS
    try:
        with open(CONFIG_YAML_PATH, 'r') as file:
            config_data = yaml.safe_load(file)
            if config_data and 'api_ids' in config_data:
                API_IDS.update(config_data['api_ids'])
            else:
                logger.warning(f"No 'api_ids' section found in {CONFIG_YAML_PATH}. IDs will not be loaded.")
    except FileNotFoundError:
        logger.error(f"YAML configuration file not found at: {CONFIG_YAML_PATH}. Ensure it exists.")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {CONFIG_YAML_PATH}: {e}")

load_api_ids_from_yaml()

for _, module_name, _ in pkgutil.iter_modules([_this_dir]):
    if module_name in ("config", "base", "__init__"):
        continue
    if module_name.endswith("_loader"):
        importlib.import_module(f"{__package__}.{module_name}")

def load_mcp_servers() -> List[Dict[str, Any]]:
    servers: List[Dict[str, Any]] = []
    for loader_cls in ConfigLoader.registry:
        loader = loader_cls()
        cfg = loader.load()
        if cfg:
            servers.append(cfg)

    if not servers:
        logger.warning("No MCP server configuration found.")
    else:
        ids = [s["id"] for s in servers]
        logger.info(f"Loaded MCP servers: {ids}")
    return servers

mcp_servers = load_mcp_servers()