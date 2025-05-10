from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import json
import logging
from api.schemas import CallToolRequest


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sse/{server_id}")
async def sse(server_id: str, request: Request):
    """
    Asynchronous Endpoint to Stream Server-Sent Events (SSE) for a Specific Server

    This endpoint provides a Server-Sent Events (SSE) stream for a specific server
    identified by its `server_id`. It utilizes an adapter associated with the given
    server to stream events. If the server or its SSE capability is not found,
    a 404 error is raised. The endpoint streams the events using an asynchronous
    generator that transmits each event as it becomes available.

    Parameters:
        server_id (str): The unique identifier of the server for which to stream SSE.
        request (Request): The current HTTP request object containing application
            state and metadata.

    Raises:
        HTTPException: If no server with the given `server_id` exists or if the
            server does not support event streaming.

    Returns:
        StreamingResponse: An asynchronous streaming response with events sent
            to the client in text/event-stream format.
    """
    registry = request.app.state.registry
    adapter = registry.get_adapter_by_id(server_id)
    
    if not adapter or not hasattr(adapter, "stream_events"):
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' no tiene SSE")
    
    async def event_gen():
        try:
            async for line in adapter.stream_events():
                yield line
        except Exception as e:
            logger.error(f"Error en event_stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_gen(), media_type="text/event-stream")

@router.get("/tools/list")
async def list_tools(request: Request):
    """
    Handles the listing of tools from various adapters in a registry.

    Summary:
    The function retrieves tool information from multiple adapters, processes
    the details, and structures the data into a dictionary format. The resulting
    dictionary contains adapter identifiers as keys and their respective tool data
    or errors as values. Each tool entry may include its description, title,
    input parameters, and other metadata based on the adapter's response.

    Args:
        request (Request): The incoming HTTP request object containing application
        state and registry of adapters.

    Returns:
        JSONResponse: A JSON-formatted response containing the processed tool data
        or any related error messages, organized per adapter.

    Raises:
        Exception: Logs and includes error details within the response if issues
        occur during processing or tool retrieval for any adapter.
    """
    registry = request.app.state.registry
    
    servers_tools = {}
    
    for adapter in registry.adapters:
        servers_tools[adapter.id] = {}
    
    for adapter in registry.adapters:
        try:
            #logger.info(f"Listing Tools for {adapter.id}")
            resp = await adapter.list_tools()
            
            if "error" in resp:
                servers_tools[adapter.id] = {"error": resp["error"]}
                continue
                
            if "result" in resp and "tools" in resp["result"]:
                tools = resp["result"]["tools"]
                
                for tool in tools:
                    if "name" not in tool:
                        continue
                    
                    tool_name = tool["name"]
                    
                    tool_info = {
                        "description": tool.get("description", "No description available"),
                        "inputs": {}
                    }
                    
                    if "annotations" in tool and "title" in tool["annotations"]:
                        tool_info["title"] = tool["annotations"]["title"]
                    
                    if "inputSchema" in tool and "properties" in tool["inputSchema"]:
                        properties = tool["inputSchema"]["properties"]
                        required = tool["inputSchema"].get("required", [])
                        
                        for param_name, param_details in properties.items():
                            param_info = {
                                "mandatory": param_name in required,
                                "type": param_details.get("type", "any")
                            }
                            
                            if "description" in param_details:
                                param_info["description"] = param_details["description"]
                            
                            if "enum" in param_details:
                                param_info["options"] = param_details["enum"]
                            
                            if param_details.get("type") == "array" and "items" in param_details:
                                param_info["items_type"] = param_details["items"].get("type", "any")
                            
                            tool_info["inputs"][param_name] = param_info
                    
                    servers_tools[adapter.id][tool_name] = tool_info
            else:
                servers_tools[adapter.id] = {"error": "Formato de respuesta inválido"}
        except Exception as e:
            logger.error(f"Error listando herramientas para {adapter.id}: {e}")
            servers_tools[adapter.id] = {"error": str(e)}
    
    return JSONResponse(content=servers_tools)


@router.get("/status/{server_id}")
async def status(server_id:str, request: Request):
    """
    Get the status of a server by its ID. This function queries the registry for the specified server and aggregates the
    status of all adapters. Adapter statuses include running, exited, not running, or an unknown state. Errors during
    status processing are captured and returned.

    Args:
        server_id: The ID of the server whose status is being queried.
        request: The incoming HTTP request object.

    Raises:
        HTTPException: Raised with status 404 if the requested server ID is not found in the registry.

    Returns:
        A dictionary containing the status information for all adapters. The status may include details such as process
        state, PID, or any encountered errors.
    """
    registry = request.app.state.registry
    adapter = registry.get_adapter_by_id(server_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' no encontrado")
    
    result = {}
    
    for adapter in registry.adapters:
        try:
            if hasattr(adapter, 'process'):
                if adapter.process is None:
                    result[adapter.id] = {"status": "not_running"}
                else:
                    returncode = adapter.process.poll()
                    if returncode is not None:
                        result[adapter.id] = {
                            "status": "exited",
                            "returncode": returncode
                        }
                    else:
                        result[adapter.id] = {
                            "status": "running",
                            "pid": adapter.process.pid
                        }
            else:
                result[adapter.id] = {"status": "unknown", "details": "No tiene proceso"}
        except Exception as e:
            result[adapter.id] = {"status": "error", "details": str(e)}
    
    return result

@router.get("/ping/{server_id}")
async def ping(server_id: str, request: Request):
    """
    Handles a ping request to a specific server by its ID by calling the server's RPC ping tool.

    Parameters:
    server_id : str
        The unique identifier for the server to be pinged.
    request : Request
        The incoming HTTP request object, which holds the application state.

    Returns:
    JSONResponse
        A JSON response with the result of the ping operation. If successful, the response includes
        the status "ok" and the content from the server's RPC ping tool. If an error occurs, the
        response includes the status "error", an error message, and a 500 HTTP status code.

    Raises:
    HTTPException
        If the adapter for the given server ID is not found, a 404 HTTPException is raised
        with a detailed error message.
    """
    registry = request.app.state.registry
    adapter = registry.get_adapter_by_id(server_id)
    
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' no encontrado")
    
    try:

        resp = await adapter.call_tool("rpc.ping", {})
        return JSONResponse(content={"status": "ok", "response": resp})
    except Exception as e:
        logger.error(f"Error en ping para {server_id}: {e}")
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)

@router.post("/call_tool")
async def call_tool(req: CallToolRequest, request: Request):
    """
    Handles POST requests to invoke a specified tool via an adapter system. The function
    retrieves the tool's name, arguments, and optional server information from the request.
    It validates the tool's availability and executes its logic if found. If any errors
    occur during execution, appropriate error information is returned to the client.

    Parameters:
        req (CallToolRequest): The body of the request containing tool name, arguments, and
            optional server identification.
        request (Request): The FastAPI request object providing additional context about
            the operation.

    Returns:
        JSONResponse: An HTTP JSON response summarizing the result of the tool invocation.
            Includes error details if any issues occur during processing.

    Raises:
        Exception: If an unexpected error occurs during the evaluation of the specified tool.
    """
    tool_name = req.tool
    arguments = req.arguments or {}
    server_id = req.server_id if hasattr(req, "server_id") else None 
    
    #logger.info(f"Calling tools: {tool_name}")
    #logger.info(f"Arguments: {arguments}")
    if server_id:
        logger.info(f"Servidor especificado: {server_id}")
    
    registry = request.app.state.registry
    if not registry.tool_map:
        logger.error("No tools registered")
        return JSONResponse(
            content={
                "error": "No tools registered. Check the MCP server configuration."
            },
            status_code=500
        )
    
    adapter = None
    if server_id:
        for a in registry.adapters:
            if a.id == server_id:
                adapter = a
                break
        
        if not adapter:
            return JSONResponse(
                content={
                    "error": f"Server '{server_id}' not found",
                    "available_servers": [a.id for a in registry.adapters]
                },
                status_code=404
            )
    else:
        adapter = registry.get_adapter(tool_name)
    
    if not adapter:
        logger.error(f"Tool not found: {tool_name}")
        return JSONResponse(
            content={
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(registry.tool_map.keys())[:10],
                "tool_count": len(registry.tool_map)
            },
            status_code=404
        )
    
    try:
        #logger.info(f"Executing {tool_name} on {adapter.id}")
        resp = await adapter.call_tool(tool_name, arguments)
        #logger.info(f"Response: {resp}")
        
        if "error" in resp:
            error_obj = resp.get("error", {})
            error_code = error_obj.get("code") if isinstance(error_obj, dict) else None
            
            if error_code == -32601:
                return JSONResponse(
                    content={
                        "error": f"El método '{tool_name}' no está disponible en el servidor MCP {adapter.id}",
                        "server_id": adapter.id,
                        "tool_name": tool_name
                    },
                    status_code=501
                )
            
            if isinstance(error_obj, dict) and "message" in error_obj:
                error_message = error_obj["message"]
            else:
                error_message = str(error_obj)
                
            return JSONResponse(
                content={"error": error_message, "details": error_obj},
                status_code=400
            )
        
        if "server_id" not in resp:
            resp["server_id"] = adapter.id
        
        return JSONResponse(content=resp)
            
    except Exception as e:
        logger.error(f"Error ejecutando {tool_name}: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
        
@router.get("/debug/servers")
async def debug_servers(request: Request):
    """
    Retrieve detailed debug information about all registered servers.

    This function collects data about all server adapters registered with the application. It
    categorizes them based on their type and enriches the information with additional details
    specific to the type of adapter. Additionally, it calculates the number of tools mapped
    to each server adapter and returns all collected data in JSON format.

    Args:
        request (Request): The HTTP request instance carrying the app state, which includes
        the registry that holds server adapters and tool mappings.

    Returns:
        JSONResponse: A JSON HTTP response containing:
            - `servers_count` (int): The total number of registered server adapters.
            - `total_tools` (int): The total number of tools mapped to any server adapter.
            - `servers` (list): A list of dictionaries, each representing a server adapter and
              its associated information:
                  * `id` (str): The unique identifier of the server adapter.
                  * `type` (str): The class name representing the type of the server adapter.
                  * Additional information depending on adapter type:
                      - For `StdIOAdapter`:
                          - `image` (str): The image associated with the adapter.
                          - `docker_args` (list): Arguments used for Docker operations.
                      - For `HTTPMCPAdapter`:
                          - `base_url` (str): The base URL associated with the adapter.
                  * `tools_count` (int): The number of tools mapped to the server adapter.
    """
    registry = request.app.state.registry
    
    servers_info = []
    for adapter in registry.adapters:
        server_info = {
            "id": adapter.id,
            "type": adapter.__class__.__name__
        }
        
        if adapter.__class__.__name__ == "StdIOAdapter":
            server_info.update({
                "image": getattr(adapter, "image", "unknown"),
                "docker_args": getattr(adapter, "docker_args", [])
            })
        elif adapter.__class__.__name__ == "HTTPMCPAdapter":
            server_info.update({
                "base_url": getattr(adapter, "base_url", "unknown")
            })
        
        tools_count = 0
        for _, reg_adapter in registry.tool_map.items():
            if reg_adapter.id == adapter.id:
                tools_count += 1
        
        server_info["tools_count"] = tools_count
        servers_info.append(server_info)
    
    return JSONResponse(content={
        "servers_count": len(servers_info),
        "total_tools": len(registry.tool_map),
        "servers": servers_info
    })
    
@router.post("/debug/direct_call")
async def debug_direct_call(request: Request):
    """
    Handles a POST request to debug and simulate a direct JSON-RPC call to a registered
    StdIOAdapter server.

    This method is designed for debugging purposes and allows a JSON-RPC call to be
    sent to a specified server adapter using details provided in the request body. The
    server must use the `StdIOAdapter` class. The endpoint processes the request,
    sends a command to the selected server, waits for a response, and returns the
    details of the debug process and the received response (if any).

    Parameters:
        request (Request): The incoming HTTP request containing the request details
            in the body.

    Returns:
        JSONResponse: A JSON object containing debug details such as the tool name,
            arguments, the formatted JSON-RPC request, the command sent, and all
            collected responses. In case an error occurs, a JSON object with an error
            message and appropriate status code is returned.
    """
    try:
        body = await request.json()
        
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})
        server_id = body.get("server_id")
        
        if not tool_name:
            return JSONResponse(
                content={"error": " 'tool' is required in the body"},
                status_code=400
            )
            
        if not server_id:
            return JSONResponse(
                content={"error": "'server_id' is required in the body"},
                status_code=400
            )
        
        registry = request.app.state.registry
        adapter = None
        
        for a in registry.adapters:
            if a.id == server_id:
                adapter = a
                break
        
        if not adapter:
            return JSONResponse(
                content={"error": f"Server '{server_id}' not found"},
                status_code=404
            )
        
        rpc_id = 1
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": tool_name,
            "params": arguments
        }
        
        if adapter.__class__.__name__ != "StdIOAdapter":
            return JSONResponse(
                content={"error": "This endpoint only works with StdIOAdapter adapters"},
                status_code=400
            )
            
        proc = adapter.start_process()
        
        command = json.dumps(jsonrpc_request) + "\n"
        
        debug_info = {
            "server_id": server_id,
            "tool": tool_name,
            "arguments": arguments,
            "request": jsonrpc_request,
            "command_sent": command
        }
        
        proc.stdin.write(command)
        proc.stdin.flush()
        
        import time
        start_time = time.time()
        responses = []
        
        while time.time() - start_time < 5.0:
            line = proc.stdout.readline()
            if not line:
                break
                
            line = line.strip()
            responses.append(line)
            
            try:
                response_json = json.loads(line)
                if "id" in response_json and response_json["id"] == rpc_id:
                    debug_info["response"] = response_json
                    debug_info["all_responses"] = responses
                    return JSONResponse(content=debug_info)
            except:
                pass
            
            time.sleep(0.1)
        
        debug_info["all_responses"] = responses
        debug_info["error"] = "No specific response was received for the request"
        return JSONResponse(content=debug_info)
        
    except Exception as e:
        logger.error(f"Error on debug_direct_call: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )