#!/usr/bin/env python3
"""MCP server for FOFA, Quake, Hunter, and DayDayMap."""

from __future__ import annotations

import base64
import json
import os
from typing import Annotated, Literal

import httpx
from pydantic import Field

try:
    # MCP Python SDK v2+
    from mcp.server import MCPServer
except ImportError:  # pragma: no cover - exercised only with MCP Python SDK v1
    # Keep existing v1 installations working while uvx resolves v2 for new installs.
    from mcp.server.fastmcp import FastMCP as MCPServer


DAYDAYMAP_ENDPOINT = "https://www.daydaymap.com/api/v1/raymap/search/all"
DAYDAYMAP_DEFAULT_FIELDS = ",".join(
    [
        "ip",
        "is_ipv6",
        "is_website",
        "port",
        "protocol",
        "country",
        "country_code",
        "province",
        "city",
        "asn",
        "asn_org",
        "isp",
        "domain",
        "icp_reg_name",
        "industry",
        "title",
        "url",
        "banner",
        "header",
        "os",
        "server",
        "lang",
        "device",
        "product",
        "service",
        "tags",
        "cert",
        "cert_selfsigned",
        "time_stamp",
    ]
)


app = MCPServer("fofa-quake-hunter-mcp")


def encode_base64(text: str, *, urlsafe: bool = False) -> str:
    """Encode text as UTF-8 Base64."""
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    return encoder(text.encode("utf-8")).decode("ascii")


def format_response(data: object) -> str:
    """Serialize an API response without escaping non-ASCII text."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def missing_key_message(platform: str, variable: str, key_url: str, aliases: tuple[str, ...] = ()) -> str:
    """Build a consistent missing-key message for MCP clients."""
    alias_text = ""
    if aliases:
        alias_text = f"\nCompatible aliases: {', '.join(aliases)}"
    return (
        f"❌ Configuration Error: {variable} environment variable is required for {platform}.\n\n"
        "Configure it in your MCP server's env section, for example:\n"
        f'{{"env": {{"{variable}": "your_api_key"}}}}\n\n'
        f"Get your API key from: {key_url}{alias_text}"
    )


def http_error_message(platform: str, key_name: str, error: httpx.HTTPStatusError) -> str:
    """Convert HTTP status failures into model-readable tool output."""
    status = error.response.status_code
    message = f"❌ {platform} API Error (HTTP {status}): {error.response.text}\n\n"
    if status == 401:
        message += f"Authentication failed. Please check your {key_name}."
    elif status == 403:
        message += "Access forbidden. Your account may not have sufficient permissions or credits."
    return message


@app.tool()
async def fofa_search(
    query: Annotated[
        str,
        Field(
            description=(
                'FOFA query using field="value" syntax. Supports =, ==, !=, *=, '
                '&&, and ||. Example: domain="example.com" && port="443".'
            )
        ),
    ],
    size: Annotated[
        int,
        Field(ge=1, le=10000, description="Number of results to return (default 100, maximum 10000)."),
    ] = 100,
    page: Annotated[int, Field(ge=1, description="Page number, starting at 1.")] = 1,
    fields: Annotated[
        str,
        Field(description="Comma-separated response fields, such as host,ip,port,domain,title."),
    ] = "host,ip,port,domain,title",
) -> str:
    """Search the FOFA cyberspace mapping platform. Requires FOFA_KEY; FOFA_EMAIL is optional."""
    key = os.getenv("FOFA_KEY")
    email = os.getenv("FOFA_EMAIL", "")
    if not key:
        return missing_key_message(
            "FOFA",
            "FOFA_KEY",
            "https://fofa.info -> Personal Center -> API Key",
        )

    params: dict[str, str | int] = {
        "key": key,
        "qbase64": encode_base64(query),
        "size": size,
        "page": page,
        "fields": fields,
    }
    if email:
        params["email"] = email

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://fofa.info/api/v1/search/all", params=params)
            response.raise_for_status()
            return format_response(response.json())
    except httpx.HTTPStatusError as error:
        return http_error_message("FOFA", "FOFA_KEY", error)
    except httpx.TimeoutException:
        return "❌ Request timeout: FOFA API did not respond within 30 seconds."
    except Exception as error:  # noqa: BLE001 - tool errors must be readable by the model
        return f"❌ Error querying FOFA: {type(error).__name__}: {error}"


@app.tool()
async def quake_search(
    query: Annotated[
        str,
        Field(
            description=(
                'Quake query using field:value syntax and uppercase AND, OR, NOT. '
                'Example: port:443 AND title:"login".'
            )
        ),
    ],
    size: Annotated[int, Field(ge=1, description="Number of results to return per page (default 100).")] = 100,
    pagination_id: Annotated[
        str,
        Field(description="Pagination ID from the previous response; leave empty for the first request."),
    ] = "",
    include: Annotated[
        str,
        Field(
            description=(
                "Comma-separated fields to include. Use exact names such as ip,port,asn,org,"
                "service.http.title; do not use as_org or a bare components field."
            )
        ),
    ] = "",
    exclude: Annotated[str, Field(description="Comma-separated fields to exclude.")] = "",
    ignore_cache: Annotated[bool, Field(description="Ignore cached results.")] = False,
    latest: Annotated[bool, Field(description="Use the latest data.")] = True,
    start_time: Annotated[str, Field(description="UTC start time, for example 2020-10-14 00:00:00.")] = "",
    end_time: Annotated[str, Field(description="UTC end time, for example 2020-10-14 00:00:00.")] = "",
) -> str:
    """Search the Quake 360 platform through its scroll API. Requires QUAKE_KEY."""
    key = os.getenv("QUAKE_KEY")
    if not key:
        return missing_key_message(
            "Quake",
            "QUAKE_KEY",
            "https://quake.360.net -> Personal Center -> Key Management",
        )

    payload: dict[str, object] = {
        "query": query,
        "size": size,
        "ignore_cache": ignore_cache,
        "latest": latest,
    }
    if pagination_id:
        payload["pagination_id"] = pagination_id
    if start_time:
        payload["start_time"] = start_time
    if end_time:
        payload["end_time"] = end_time
    if include:
        payload["include"] = [field.strip() for field in include.split(",") if field.strip()]
    if exclude:
        payload["exclude"] = [field.strip() for field in exclude.split(",") if field.strip()]

    headers = {"X-QuakeToken": key, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://quake.360.net/api/v3/scroll/quake_service",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return format_response(response.json())
    except httpx.HTTPStatusError as error:
        return http_error_message("Quake", "QUAKE_KEY", error)
    except httpx.TimeoutException:
        return "❌ Request timeout: Quake API did not respond within 30 seconds."
    except Exception as error:  # noqa: BLE001 - tool errors must be readable by the model
        return f"❌ Error querying Quake: {type(error).__name__}: {error}"


@app.tool()
async def hunter_search(
    query: Annotated[
        str,
        Field(
            description=(
                'Hunter query using field="value" syntax. Supports =, ==, !=, !==, &&, and ||. '
                'Example: web.title="login" && web.status_code="200".'
            )
        ),
    ],
    page: Annotated[int, Field(ge=1, description="Page number, starting at 1.")] = 1,
    page_size: Annotated[Literal[10, 50, 100], Field(description="Results per page: 10, 50, or 100.")] = 10,
    is_web: Annotated[
        Literal[1, 2, 3],
        Field(description="Asset type: 1 for web, 2 for non-web, 3 for all assets."),
    ] = 3,
    status_code: Annotated[str, Field(description="Comma-separated HTTP status codes, for example 200,301.")] = "",
    fields: Annotated[str, Field(description="Comma-separated response fields; empty returns all fields.")] = "",
    start_time: Annotated[str, Field(description="Start date in YYYY-MM-DD format.")] = "",
    end_time: Annotated[str, Field(description="End date in YYYY-MM-DD format.")] = "",
) -> str:
    """Search the Qianxin Hunter (奇安信鹰图) platform. Requires HUNTER_KEY."""
    key = os.getenv("HUNTER_KEY")
    if not key:
        return missing_key_message(
            "Hunter",
            "HUNTER_KEY",
            "https://hunter.qianxin.com -> Personal Center -> API Management",
        )

    params: dict[str, str | int] = {
        "api-key": key,
        "search": encode_base64(query, urlsafe=True),
        "page": page,
        "page_size": page_size,
        "is_web": is_web,
    }
    for name, value in (
        ("status_code", status_code),
        ("fields", fields),
        ("start_time", start_time),
        ("end_time", end_time),
    ):
        if value:
            params[name] = value

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://hunter.qianxin.com/openApi/search", params=params)
            response.raise_for_status()
            return format_response(response.json())
    except httpx.HTTPStatusError as error:
        return http_error_message("Hunter", "HUNTER_KEY", error)
    except httpx.TimeoutException:
        return "❌ Request timeout: Hunter API did not respond within 30 seconds."
    except Exception as error:  # noqa: BLE001 - tool errors must be readable by the model
        return f"❌ Error querying Hunter: {type(error).__name__}: {error}"


@app.tool()
async def daydaymap_search(
    query: Annotated[
        str,
        Field(
            description=(
                'DayDayMap query before Base64 encoding. Examples: ip="1.1.1.1", '
                'domain="example.com", port="443", web.title="login". '
                "Supports && and || for logical combinations."
            )
        ),
    ],
    page: Annotated[int, Field(ge=1, description="Page number, starting at 1.")] = 1,
    page_size: Annotated[
        int,
        Field(ge=1, le=10000, description="Number of results per page (default 100, maximum 10000)."),
    ] = 100,
    fields: Annotated[
        str,
        Field(
            description=(
                "Comma-separated response fields. Set to an empty string to omit fields and use exclude_fields."
            )
        ),
    ] = DAYDAYMAP_DEFAULT_FIELDS,
    exclude_fields: Annotated[
        str,
        Field(description="Comma-separated fields to exclude; effective only when fields is empty."),
    ] = "",
) -> str:
    """Search the DayDayMap cyberspace mapping platform. Requires DAYDAYMAP_KEY or DAYDAYMAP_API_KEY."""
    key = os.getenv("DAYDAYMAP_KEY") or os.getenv("DAYDAYMAP_API_KEY")
    if not key:
        return missing_key_message(
            "DayDayMap",
            "DAYDAYMAP_KEY",
            "https://www.daydaymap.com -> Personal Center",
            aliases=("DAYDAYMAP_API_KEY",),
        )

    payload: dict[str, object] = {
        "page": page,
        "page_size": page_size,
        "keyword": encode_base64(query),
    }
    if fields:
        payload["fields"] = fields
    elif exclude_fields:
        payload["exclude_fields"] = exclude_fields

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DAYDAYMAP_ENDPOINT,
                headers={"api-key": key, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("code") not in (None, 200):
                return (
                    f"❌ DayDayMap API Error (code {data.get('code')}): "
                    f"{data.get('msg') or data.get('message') or format_response(data)}"
                )
            return format_response(data)
    except httpx.HTTPStatusError as error:
        return http_error_message("DayDayMap", "DAYDAYMAP_KEY", error)
    except httpx.TimeoutException:
        return "❌ Request timeout: DayDayMap API did not respond within 60 seconds."
    except Exception as error:  # noqa: BLE001 - tool errors must be readable by the model
        return f"❌ Error querying DayDayMap: {type(error).__name__}: {error}"


def main() -> None:
    """Run the MCP server over stdio."""
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
