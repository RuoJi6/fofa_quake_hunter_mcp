import base64
import json

import pytest
from mcp.client import Client

from fofa_quake_hunter_mcp import server


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_v2_lists_all_tools(monkeypatch):
    monkeypatch.delenv("DAYDAYMAP_KEY", raising=False)
    monkeypatch.delenv("DAYDAYMAP_API_KEY", raising=False)

    async with Client(server.app) as client:
        listing = await client.list_tools()
        result = await client.call_tool("daydaymap_search", {"query": 'ip="1.1.1.1"'})

    assert [tool.name for tool in listing.tools] == [
        "fofa_search",
        "quake_search",
        "hunter_search",
        "daydaymap_search",
    ]
    assert "DAYDAYMAP_KEY" in result.content[0].text


@pytest.mark.anyio
async def test_daydaymap_request_matches_api(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"code": 200, "data": {"list": [{"ip": "1.1.1.1"}]}}

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse()

    monkeypatch.setenv("DAYDAYMAP_KEY", "test-key")
    monkeypatch.delenv("DAYDAYMAP_API_KEY", raising=False)
    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)

    result = await server.daydaymap_search(
        query='domain="example.com"',
        page=2,
        page_size=25,
        fields="ip,port,domain",
        exclude_fields="",
    )

    assert json.loads(result)["data"]["list"][0]["ip"] == "1.1.1.1"
    _, request = calls[1]
    assert calls[1][0] == server.DAYDAYMAP_ENDPOINT
    assert request["headers"]["api-key"] == "test-key"
    assert request["json"] == {
        "page": 2,
        "page_size": 25,
        "keyword": base64.b64encode(b'domain="example.com"').decode("ascii"),
        "fields": "ip,port,domain",
    }


@pytest.mark.anyio
async def test_daydaymap_api_key_alias_is_supported(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"code": 200, "data": []}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, **kwargs):
            assert kwargs["headers"]["api-key"] == "alias-key"
            return FakeResponse()

    monkeypatch.delenv("DAYDAYMAP_KEY", raising=False)
    monkeypatch.setenv("DAYDAYMAP_API_KEY", "alias-key")
    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)

    result = await server.daydaymap_search(query='port="443"')

    assert json.loads(result)["code"] == 200


@pytest.mark.anyio
async def test_fofa_default_size_is_100(monkeypatch):
    request_params = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"error": False, "results": []}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def get(self, url, **kwargs):
            request_params.update(kwargs["params"])
            return FakeResponse()

    monkeypatch.setenv("FOFA_KEY", "test-key")
    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)

    await server.fofa_search(query='body="admin"')

    assert request_params["size"] == 100
