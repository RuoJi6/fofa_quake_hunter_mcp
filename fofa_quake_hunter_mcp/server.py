#!/usr/bin/env python3
"""MCP server for FOFA, Quake, and Hunter cyberspace mapping platforms."""

import os
import base64
import json
from typing import Any
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


# Initialize MCP server
app = Server("fofa-quake-hunter-mcp")


def encode_base64(text: str) -> str:
    """Encode text to base64."""
    return base64.b64encode(text.encode()).decode()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="fofa_search",
            description="Search FOFA cyberspace mapping platform. Requires FOFA_EMAIL and FOFA_KEY environment variables. Query syntax examples: body=\"miner start\", domain=\"example.com\", ip=\"1.1.1.1\", title=\"login\", port=\"80\"",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "FOFA search query. Supports both quoted and unquoted syntax. Examples: body=\"miner start\", domain=example.com, ip=1.1.1.1",
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of results to return (default: 100, max: 10000)",
                        "default": 100,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1,
                    },
                    "fields": {
                        "type": "string",
                        "description": "Comma-separated fields to return. Available fields: host, ip, port, domain, title, protocol, server, banner, cert, icp, country, city, as_organization, etc. Default: 'host,ip,port,domain,title'",
                        "default": "host,ip,port,domain,title",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="quake_search",
            description="Search Quake 360 cyberspace mapping platform using scroll API (supports deep pagination). Requires QUAKE_KEY environment variable. Query syntax: title:\"keyword\" for title search, ip:1.1.1.1 for IP, domain:example.com for domain, port:80 for port, service:http for service. IMPORTANT: Use 'include' parameter to specify which fields to return. Supports pagination_id for getting more pages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Quake search query. Examples: title:\"后台管理\" (search title), ip:1.1.1.1 (search IP), domain:example.com (search domain), service:http (search service)",
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of results to return per page (default: 100, larger size = longer request time)",
                        "default": 100,
                    },
                    "pagination_id": {
                        "type": "string",
                        "description": "Pagination ID from previous response. Use this to get next page. Expires in 5 minutes. Leave empty for first request.",
                    },
                    "include": {
                        "type": "string",
                        "description": "Comma-separated fields to include in results. Common fields: ip (IP address), port (port number), hostname (hostname), service.name (service name), service.http.title (web title), service.http.server (server type), location.country_cn (country), location.province_cn (province), location.city_cn (city), domain (domain name). Example: 'ip' for only IP, 'ip,port,service.http.title' for IP, port and title. If not specified, returns all default fields.",
                    },
                    "exclude": {
                        "type": "string",
                        "description": "Comma-separated fields to exclude from results",
                    },
                    "ignore_cache": {
                        "type": "boolean",
                        "description": "Whether to ignore cache (default: false)",
                        "default": False,
                    },
                    "latest": {
                        "type": "boolean",
                        "description": "Whether to use latest data (default: true)",
                        "default": True,
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Query start time in format: 2020-10-14 00:00:00 (UTC timezone)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Query end time in format: 2020-10-14 00:00:00 (UTC timezone)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="hunter_search",
            description="Search Hunter (奇安信鹰图) cyberspace mapping platform. Requires HUNTER_KEY environment variable. Query syntax examples: web.body=\"keyword\", ip=\"1.1.1.1\", domain=\"example.com\", web.title=\"login\". Supports filtering by asset type: web assets, non-web assets, or all. Supports time range filtering (querying beyond 30 days will consume extra credits).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Hunter search query. Supports both quoted and unquoted syntax. Examples: web.body=\"keyword\", ip=1.1.1.1, domain=example.com",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number, starting from 1 (default: 1)",
                        "default": 1,
                        "minimum": 1,
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Results per page (default: 10, valid values: 10, 50, 100)",
                        "default": 10,
                        "enum": [10, 50, 100],
                    },
                    "is_web": {
                        "type": "integer",
                        "description": "Asset type filter: 1=only web assets (websites, web services), 2=only non-web assets (databases, IoT devices, etc.), 3=all assets (default: 3)",
                        "default": 3,
                        "enum": [1, 2, 3],
                    },
                    "status_code": {
                        "type": "string",
                        "description": "HTTP status codes filter (e.g., '200,301')",
                    },
                    "fields": {
                        "type": "string",
                        "description": "Comma-separated fields to return. Available: ip,port,domain,ip_tag,url,web_title,is_risk_protocol,protocol,base_protocol,status_code,os,company,number,icp_exception,country,province,city,is_web,isp,as_org,cert_sha256,ssl_certificate,component,asset_tag,updated_at,header,header_server,banner. If not specified, returns all fields.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Query start time in format: 2021-01-01 (YYYY-MM-DD). Note: Querying beyond 30 days will consume extra credits.",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Query end time in format: 2021-03-01 (YYYY-MM-DD). Note: Querying beyond 30 days will consume extra credits.",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "fofa_search":
        return await fofa_search(arguments)
    elif name == "quake_search":
        return await quake_search(arguments)
    elif name == "hunter_search":
        return await hunter_search(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def fofa_search(args: dict) -> list[TextContent]:
    """Search FOFA platform."""
    email = os.getenv("FOFA_EMAIL")
    key = os.getenv("FOFA_KEY")
    
    if not email or not key:
        return [TextContent(
            type="text",
            text="❌ Configuration Error: FOFA_EMAIL and FOFA_KEY environment variables are required.\n\n"
                 "Please configure them in your MCP settings:\n"
                 '{\n'
                 '  "mcpServers": {\n'
                 '    "fofa-quake-hunter": {\n'
                 '      "env": {\n'
                 '        "FOFA_EMAIL": "your_email@example.com",\n'
                 '        "FOFA_KEY": "your_fofa_api_key"\n'
                 '      }\n'
                 '    }\n'
                 '  }\n'
                 '}\n\n'
                 "Get your API key from: https://fofa.info -> Personal Center -> API Key"
        )]
    
    query = args["query"]
    size = args.get("size", 10)
    page = args.get("page", 1)
    fields = args.get("fields", "host,ip,port,domain,title")
    
    # Encode query to base64
    qbase64 = encode_base64(query)
    
    url = f"https://fofa.info/api/v1/search/all"
    params = {
        "email": email,
        "key": key,
        "qbase64": qbase64,
        "size": size,
        "page": page,
        "fields": fields,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(
                type="text",
                text=json.dumps(data, indent=2, ensure_ascii=False)
            )]
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ FOFA API Error (HTTP {e.response.status_code}): {e.response.text}\n\n"
        if e.response.status_code == 401:
            error_msg += "Authentication failed. Please check your FOFA_EMAIL and FOFA_KEY."
        elif e.response.status_code == 403:
            error_msg += "Access forbidden. Your account may not have sufficient permissions."
        return [TextContent(type="text", text=error_msg)]
    except httpx.TimeoutException:
        return [TextContent(
            type="text",
            text="❌ Request timeout: FOFA API did not respond within 30 seconds."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error querying FOFA: {type(e).__name__}: {str(e)}"
        )]


async def quake_search(args: dict) -> list[TextContent]:
    """Search Quake 360 platform."""
    key = os.getenv("QUAKE_KEY")
    
    if not key:
        return [TextContent(
            type="text",
            text="❌ Configuration Error: QUAKE_KEY environment variable is required.\n\n"
                 "Please configure it in your MCP settings:\n"
                 '{\n'
                 '  "mcpServers": {\n'
                 '    "fofa-quake-hunter": {\n'
                 '      "env": {\n'
                 '        "QUAKE_KEY": "your_quake_api_key"\n'
                 '      }\n'
                 '    }\n'
                 '  }\n'
                 '}\n\n'
                 "Get your API key from: https://quake.360.net -> Personal Center -> Key Management"
        )]
    
    query = args["query"]
    size = args.get("size", 100)
    pagination_id = args.get("pagination_id", "")
    include = args.get("include", "")
    exclude = args.get("exclude", "")
    ignore_cache = args.get("ignore_cache", False)
    latest = args.get("latest", True)
    start_time = args.get("start_time", "")
    end_time = args.get("end_time", "")
    
    url = "https://quake.360.net/api/v3/scroll/quake_service"
    headers = {
        "X-QuakeToken": key,
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "size": size,
        "ignore_cache": ignore_cache,
        "latest": latest,
    }
    
    # Add pagination_id if specified (for getting next page)
    if pagination_id:
        payload["pagination_id"] = pagination_id
    
    # Add time range if specified
    if start_time:
        payload["start_time"] = start_time
    if end_time:
        payload["end_time"] = end_time
    
    # Add include/exclude if specified
    if include:
        payload["include"] = [field.strip() for field in include.split(",")]
    
    if exclude:
        payload["exclude"] = [field.strip() for field in exclude.split(",")]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(
                type="text",
                text=json.dumps(data, indent=2, ensure_ascii=False)
            )]
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ Quake API Error (HTTP {e.response.status_code}): {e.response.text}\n\n"
        if e.response.status_code == 401:
            error_msg += "Authentication failed. Please check your QUAKE_KEY."
        elif e.response.status_code == 403:
            error_msg += "Access forbidden. Your account may not have sufficient permissions or credits."
        return [TextContent(type="text", text=error_msg)]
    except httpx.TimeoutException:
        return [TextContent(
            type="text",
            text="❌ Request timeout: Quake API did not respond within 30 seconds."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error querying Quake: {type(e).__name__}: {str(e)}"
        )]


async def hunter_search(args: dict) -> list[TextContent]:
    """Search Hunter (奇安信鹰图) platform."""
    key = os.getenv("HUNTER_KEY")
    
    if not key:
        return [TextContent(
            type="text",
            text="❌ Configuration Error: HUNTER_KEY environment variable is required.\n\n"
                 "Please configure it in your MCP settings:\n"
                 '{\n'
                 '  "mcpServers": {\n'
                 '    "fofa-quake-hunter": {\n'
                 '      "env": {\n'
                 '        "HUNTER_KEY": "your_hunter_api_key"\n'
                 '      }\n'
                 '    }\n'
                 '  }\n'
                 '}\n\n'
                 "Get your API key from: https://hunter.qianxin.com -> Personal Center -> API Management"
        )]
    
    query = args["query"]
    page = args.get("page", 1)
    page_size = args.get("page_size", 10)
    is_web = args.get("is_web", 3)
    status_code = args.get("status_code", "")
    fields = args.get("fields", "")
    start_time = args.get("start_time", "")
    end_time = args.get("end_time", "")
    
    # Encode query to base64url
    search_encoded = base64.urlsafe_b64encode(query.encode()).decode()
    
    url = "https://hunter.qianxin.com/openApi/search"
    params = {
        "api-key": key,
        "search": search_encoded,
        "page": page,
        "page_size": page_size,
        "is_web": is_web,
    }
    
    if status_code:
        params["status_code"] = status_code
    
    if fields:
        params["fields"] = fields
    
    if start_time:
        params["start_time"] = start_time
    
    if end_time:
        params["end_time"] = end_time
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [TextContent(
                type="text",
                text=json.dumps(data, indent=2, ensure_ascii=False)
            )]
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ Hunter API Error (HTTP {e.response.status_code}): {e.response.text}\n\n"
        if e.response.status_code == 401:
            error_msg += "Authentication failed. Please check your HUNTER_KEY."
        elif e.response.status_code == 403:
            error_msg += "Access forbidden. Your account may not have sufficient permissions or credits."
        return [TextContent(type="text", text=error_msg)]
    except httpx.TimeoutException:
        return [TextContent(
            type="text",
            text="❌ Request timeout: Hunter API did not respond within 30 seconds."
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error querying Hunter: {type(e).__name__}: {str(e)}"
        )]


def main():
    """Run the MCP server."""
    import anyio
    
    async def run_server():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    anyio.run(run_server)


if __name__ == "__main__":
    main()
