#!/usr/bin/env python3
"""Brave Search MCP Server — SSE transport on port 9101."""
import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import PlainTextResponse

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
PORT = int(os.environ.get("MCP_BRAVE_PORT", "9101"))

# MCP Server
app = Server("brave-search")


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "brave_web_search":
        return await web_search(arguments.get("query", ""), arguments.get("count", 10))
    elif name == "brave_news_search":
        return await news_search(arguments.get("query", ""), arguments.get("count", 10))
    raise ValueError(f"Unknown tool: {name}")


@app.list_tools()
async def list_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "brave_web_search",
                "description": "Search the web using Brave Search. Returns titles, URLs, and snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "count": {"type": "integer", "description": "Number of results (max 20)", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "brave_news_search",
                "description": "Search recent news articles via Brave Search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "News search query"},
                        "count": {"type": "integer", "description": "Number of results", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        }
    ]


async def web_search(query: str, count: int = 10):
    if not BRAVE_API_KEY:
        return [{"type": "text", "text": "Error: BRAVE_API_KEY not configured"}]
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(count, 20)},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
        )
        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
            })
        return [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}]


async def news_search(query: str, count: int = 10):
    if not BRAVE_API_KEY:
        return [{"type": "text", "text": "Error: BRAVE_API_KEY not configured"}]
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/news/search",
            params={"q": query, "count": min(count, 20)},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
        )
        data = resp.json()
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
                "age": r.get("age", ""),
            })
        return [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}]


# SSE Transport setup
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
    print(f"🔍 Brave Search MCP on :{PORT}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=PORT, log_level="warning")
