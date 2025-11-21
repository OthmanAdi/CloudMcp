import os
import asyncio
from datetime import datetime
from mcp.server import Server
from mcp.server.sse import SseServerTransport  # FIXED: Changed from sse_server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request

app_mcp = Server("railway-mcp-server")
memory_store = {}

@app_mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_time",
            description="Get current time",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_date",
            description="Get current date",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="calculator",
            description="Calculate math expression",
            inputSchema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        ),
        Tool(
            name="save_memory",
            description="Save to memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="recall_memory",
            description="Recall from memory",
            inputSchema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"]
            }
        )
    ]

@app_mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_time":
        now = datetime.now()
        result = f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        return [TextContent(type="text", text=result)]
    elif name == "get_date":
        now = datetime.now()
        result = f"Today is: {now.strftime('%A, %B %d, %Y')}"
        return [TextContent(type="text", text=result)]
    elif name == "calculator":
        expression = arguments.get("expression", "")
        try:
            result = eval(expression)
            return [TextContent(type="text", text=f"Result: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    elif name == "save_memory":
        key = arguments.get("key")
        value = arguments.get("value")
        memory_store[key] = value
        return [TextContent(type="text", text=f"Saved: {key} = {value}")]
    elif name == "recall_memory":
        key = arguments.get("key")
        value = memory_store.get(key, "Not found")
        return [TextContent(type="text", text=f"Memory '{key}': {value}")]
    raise ValueError(f"Unknown tool: {name}")

# FIXED: Changed to use SseServerTransport instead of sse_server()
async def handle_sse(request: Request):
    async with SseServerTransport("/messages") as transport:
        await app_mcp.run(
            transport.read_stream,
            transport.write_stream,
            app_mcp.create_initialization_options()
        )

starlette_app = Starlette(
    routes=[Route("/sse", endpoint=handle_sse)],
    debug=True
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting MCP SSE Server on port {port}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
