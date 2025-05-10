import subprocess
import asyncio
import json
import logging
import os
from typing import Dict, Any, AsyncIterator
from .base import MCPAdapter

logger = logging.getLogger(__name__)

class StdIOAdapter(MCPAdapter):
    """
    Provides an implementation of an MCPAdapter class for managing dockerized MCP processes.

    This class is responsible for handling the communication between the adapter and an MCP
    backend process. It initializes a specific Docker container and interacts through
    stdin and stdout using JSON-RPC protocol. It allows for listing tools, invoking specific
    tools, receiving responses, and streaming events.

    Attributes:
        id (str): A unique identifier for the adapter instance, such as 'github'.
        image (str): Docker image name associated with the adapter, e.g., 'mcp/github'.
        docker_args (list[str]): Additional arguments for the Docker `run` command.
        _next_id (int): Internally managed JSON-RPC identifier, incrementing with each RPC call.
        process (Optional[subprocess.Popen]): The active subprocess running the MCP within Docker.

    Methods:
        start_process:
            Starts the Docker-based MCP process if not already running or if the process has exited.

        _send_and_receive:
            Sends a JSON-RPC command via stdin and waits for a valid response line via stdout.

        list_tools:
            Lists available tools by invoking the standard 'tools/list' JSON-RPC method.

        call_tool:
            Calls a specific tool via JSON-RPC, passing required arguments.

        stream_events:
            Provides a live stream of unparsed stdout lines, reformatting them as Server-Sent Events (SSE).
    """
    def __init__(self, id: str, image: str, docker_args: list[str]):
        """
        Represents a container instance with associated attributes and lifecycle management.

        This class holds the details of a container, including its ID, image, and arguments
        needed to run the container. Additionally, it manages process state and increments
        internal IDs for container session tracking.

        Attributes:
            id (str): Identifier for the container instance.
            image (str): Name of the Docker image used to create the container.
            docker_args (list[str]): List of arguments to be passed to the Docker runtime.
            _next_id (int): Internal attribute used for generating internal session IDs. Default is 1.
            process: Represents the state or reference to the running process of the container. Initially None.

        """
        self.id = id
        self.image = image
        self.docker_args = docker_args
        self._next_id: int = 1
        self.process = None

    def start_process(self):
        """
        Starts a new subprocess if no process is running or if the current process has terminated.
        The subprocess runs a Docker container with the specified arguments and environment configuration.

        Attributes
        ----------
        process : subprocess.Popen or None
            Represents the subprocess that runs the Docker container.
        id : str
            An identifier used for logging purposes.
        docker_args : list of str
            Additional arguments for the docker run command.
        image : str
            The name of the Docker image to be executed.

        Parameters
        ----------
        self

        Returns
        -------
        subprocess.Popen
            The process object representing the running Docker container.

        Raises
        ------
        Exception
            If an error occurs while attempting to read the initial output line of the process.
        """
        if self.process is None or self.process.poll() is not None:
            docker_path = "docker"
            docker_args = ["run", "-i", "--rm", *self.docker_args, self.image]
            

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"  
            
            self.process = subprocess.Popen(
                [docker_path] + docker_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                errors="replace",
                encoding="utf-8",
                text=True,
                bufsize=0,  
                env=env,
                shell=False,  
                universal_newlines=True,  
            )
            
            try:
                startup_line = self.process.stdout.readline()
                logger.info(f"Docker startup: {startup_line.strip()}")
                if "running on stdio" in startup_line:
                    logger.info(f"{self.id} MCP correctly initialized.")
                else:
                    logger.warning(f"Unusual beginning: {startup_line}")
            except Exception as e:
                logger.error(f"Error reading main output: {e}")
            
            logger.info(f"Process initialized PID: {self.process.pid}")
        
        return self.process

    async def _send_and_receive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles sending a payload asynchronously and receiving a JSON response via a process's
        standard input and output streams. Operates within a set timeout, decoding data in JSON
        format. Logs command sent, any decoding errors, or EOF warnings encountered during
        execution, ensuring proper flow and error handling.

        Parameters:
        payload: Dict[str, Any]
            The data to be serialized into JSON and sent to the process for processing.

        Returns:
        Dict[str, Any]
            A dictionary representing the JSON-decoded response received from the process.

        Raises:
        RuntimeError
            Raised if no valid response is received within the specified timeout period.
        """
        proc = self.start_process()
        
        command = json.dumps(payload) + "\n"
        #logger.info(f"Command sent: {command.strip()}")
        
        proc.stdin.write(command)
        proc.stdin.flush()

        response = None
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 5.0:
            line = proc.stdout.readline()
            if not line:
                logger.warning("EOF mistake")
                break
                
            line = line.strip()
            
            try:
                response = json.loads(line)
                return response
            except json.JSONDecodeError:
                logger.error(f"Error JSON: {line}")
                continue
        
        if response is None:
            raise RuntimeError("Timeout STDIO")
        
        return response

    async def list_tools(self) -> Dict[str, Any]:
        """
        Llama al método estándar 'tools/list' del MCP JSON-RPC.
        Retorna el JSON-RPC entero, con 'result.tools'.
        """
        rpc_id = self._next_id
        self._next_id += 1
        
        payload = {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/list", "params": {}}
        return await self._send_and_receive(payload)

    async def call_tool(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously calls a specified tool using the JSON-RPC protocol, sends arguments to the tool,
        and retrieves the response from the tool's process output. Handles process initiation, command
        sending, response reading, and error handling if any issue arises during these steps.

        Parameters
        ----------
        tool : str
            The name of the tool to invoke.
        arguments : Dict[str, Any]
            A dictionary containing tool-specific arguments to be passed during the call. If None,
            an empty dictionary will be used.

        Returns
        -------
        Dict[str, Any]
            The response from the tool in JSON-RPC format. If an error occurs (e.g., process failure,
            communication errors), the response will include an error field describing the issue.

        Raises
        ------
        Exception
            An exception is raised if there is an issue writing to or reading from the process
            standard input/output or if JSON decoding of the response fails.
        """
        rpc_id = self._next_id
        self._next_id += 1

        if arguments is None:
            arguments = {}
        
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": "tools/call", 
            "params": {
                "name":tool,
                "arguments":arguments,
                }
        }
        
        #logger.info(f"Adapter {self.id}: sending request JSON-RPC: {jsonrpc_request}")
        
        proc = self.start_process()
        if proc is None:
            logger.error(f"Failed to start process for {self.id}")
            return {
                "jsonrpc": "2.0", 
                "id": rpc_id, 
                "error": {"message": f"Failed to start the process for {self.id}"}
            }
        
        command = json.dumps(jsonrpc_request) + "\n"
        #logger.info(f"Adapter {self.id}: Command sent: {command.strip()}")
        
        try:
            proc.stdin.write(command)
            proc.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending command to {self.id}: {e}")
            return {
                "jsonrpc": "2.0", 
                "id": rpc_id, 
                "error": {"message": f"Error sending command: {str(e)}"}
            }
        
        import time
        start_time = time.time()
        raw_responses = []
        
        while time.time() - start_time < 10.0:
            try:
                line = proc.stdout.readline()
                if not line:
                    logger.warning(f"Adapter {self.id}: EOF mistake")
                    break
                    
                line = line.strip()
                if line:
                    raw_responses.append(line)
                    #logger.info(f"Adapter {self.id}: Response received: {line}")
                    
                    try:
                        response = json.loads(line)
                        if "id" in response and response["id"] == rpc_id:
                            #logger.info(f"Adapter {self.id}: response equals id: {rpc_id}")
                            return response
                        else:
                            logger.info(f"Adapter {self.id}: Response different id: {response.get('id')} != {rpc_id}")
                    except json.JSONDecodeError:
                        logger.error(f"Adapter {self.id}: Error JSON: {line}")
                        continue
            except Exception as e:
                logger.error(f"Adapter {self.id}: Error reading response: {e}")
                break
            
            time.sleep(0.1)
        
        logger.error(f"Adapter {self.id}:No valid response received for {tool}")
        logger.error(f"Adapter {self.id}: raw response received: {raw_responses}")
        
        return {
            "jsonrpc": "2.0", 
            "id": rpc_id, 
            "error": {
                "code": -32603,
                "message": f"No valid response was received for {tool} in {self.id}"
            }
        }

    async def stream_events(self) -> AsyncIterator[str]:
        """
            Asynchronously streams events from a process' stdout.

            This coroutine reads lines from the standard output of a subprocess,
            parses them as JSON, and yields them formatted as Server-Sent Events
            (SSE). Each event is logged for monitoring purposes.

            Raises:
                json.JSONDecodeError: If the line cannot be parsed as valid JSON.
                Exception: If there's an error while processing a line.

            Yields:
                str: Formatted SSE strings including the event type and event data.
        """
        proc = self.start_process()
        logger.info("Initiating stream events")
        
        while True:
            line = proc.stdout.readline()
            if not line:
                logger.warning("EOF mistake")
                break
                
            logger.info(f"Line received: {line.strip()}")
            
            try:
                data = json.loads(line.strip())
                
                event_type = data.get("event", "message")
                yield f"event: {event_type}\n"
                event_data = data.get("data", {})
                yield f"data: {json.dumps(event_data)}\n\n"
                logger.info(f"Event SSE sent: {event_type}")
            except json.JSONDecodeError:
                logger.error(f"Error parsing JSON: {line.strip()}")
            except Exception as e:
                logger.error(f"Error processing line: {e}")