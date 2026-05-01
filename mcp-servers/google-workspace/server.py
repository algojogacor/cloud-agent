#!/usr/bin/env python3
"""Google Workspace MCP Server — SSE transport on port 9102."""
import os
import json
import asyncio
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import PlainTextResponse

PORT = int(os.environ.get("MCP_GOOGLE_PORT", "9102"))
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")

app = Server("google-workspace")


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "docs_read":
        return await docs_read(arguments.get("doc_id", ""))
    elif name == "docs_write":
        return await docs_write(arguments.get("title", ""), arguments.get("content", ""))
    elif name == "docs_append":
        return await docs_append(arguments.get("doc_id", ""), arguments.get("content", ""))
    elif name == "sheets_read":
        return await sheets_read(arguments.get("sheet_id", ""), arguments.get("range", "A1:Z100"))
    elif name == "sheets_write":
        return await sheets_write(arguments.get("sheet_id", ""), arguments.get("range", ""), arguments.get("values", []))
    raise ValueError(f"Unknown tool: {name}")


@app.list_tools()
async def list_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "docs_read",
                "description": "Read a Google Doc by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Google Doc ID (from URL)"}
                    },
                    "required": ["doc_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "docs_write",
                "description": "Create a new Google Doc with content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Document title"},
                        "content": {"type": "string", "description": "Document content"}
                    },
                    "required": ["title", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "docs_append",
                "description": "Append content to an existing Google Doc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Google Doc ID"},
                        "content": {"type": "string", "description": "Content to append"}
                    },
                    "required": ["doc_id", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sheets_read",
                "description": "Read data from Google Sheets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sheet_id": {"type": "string", "description": "Google Sheet ID"},
                        "range": {"type": "string", "description": "Cell range (e.g., A1:D10)", "default": "A1:Z100"}
                    },
                    "required": ["sheet_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sheets_write",
                "description": "Write data to Google Sheets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sheet_id": {"type": "string", "description": "Google Sheet ID"},
                        "range": {"type": "string", "description": "Cell range"},
                        "values": {"type": "array", "description": "2D array of values"}
                    },
                    "required": ["sheet_id", "range", "values"]
                }
            }
        }
    ]


# Placeholder implementations - will return instructions
async def docs_read(doc_id: str):
    return [{"type": "text", "text": f"Google Docs read not yet implemented. Doc ID: {doc_id}\n\nTo enable:\n1. Set GOOGLE_SERVICE_ACCOUNT_JSON env var\n2. Share doc with service account email"}]


async def docs_write(title: str, content: str):
    return [{"type": "text", "text": f"Created doc '{title}' with {len(content)} chars.\n\nNote: Full implementation requires Google Cloud setup."}]


async def docs_append(doc_id: str, content: str):
    return [{"type": "text", "text": f"Appended to doc {doc_id}.\n\nNote: Full implementation requires Google Cloud setup."}]


async def sheets_read(sheet_id: str, range: str):
    return [{"type": "text", "text": f"Reading sheet {sheet_id} range {range}.\n\nNote: Full implementation requires Google Cloud setup."}]


async def sheets_write(sheet_id: str, range: str, values: list):
    return [{"type": "text", "text": f"Writing to sheet {sheet_id}.\n\nNote: Full implementation requires Google Cloud setup."}]


# SSE Transport
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_session(
        request.scope, request.receive, request.send
    ) as session:
        await app.run(session)


async def handle_health(request):
    return PlainTextResponse("ok")


starlette_app = Starlette(
    routes=[
        Route("/", handle_health),
        Route("/health", handle_health),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ]
)

if __name__ == "__main__":
    import uvicorn
    print(f"📄 Google Workspace MCP on :{PORT}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=PORT, log_level="warning")
