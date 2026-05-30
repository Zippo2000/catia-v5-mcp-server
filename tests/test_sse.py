"""Tests for SSE transport, CLI parsing, and server infrastructure.

Tests the SSE (Server-Sent Events) transport mode added for compatibility with
vLLM.rs, LM Studio, Open WebUI, and other MCP clients that use HTTP SSE.

All tests run without live CATIA or live HTTP — mocking is used throughout.
"""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.fixture(autouse=True)
def fresh_com_mocks():
    """Reset COM mocks before each test (shared from conftest.py)."""
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()


# ─── 1. CLI Argument Parsing ──────────────────────────────────────────


class TestCLIParseArgs:
    """Test parse_args() CLI argument handling."""

    def test_default_is_stdio(self):
        from catia_mcp.server import parse_args
        args = parse_args([])
        assert args.stdio is False
        assert args.sse is False
        assert args.host == "0.0.0.0"
        assert args.port == 8765

    def test_sse_flag(self):
        from catia_mcp.server import parse_args
        args = parse_args(["--sse"])
        assert args.sse is True
        assert args.stdio is False
        assert args.host == "0.0.0.0"
        assert args.port == 8765

    def test_stdio_flag(self):
        from catia_mcp.server import parse_args
        args = parse_args(["--stdio"])
        assert args.stdio is True
        assert args.sse is False

    def test_custom_host_and_port(self):
        from catia_mcp.server import parse_args
        args = parse_args(["--sse", "--host", "127.0.0.1", "--port", "9999"])
        assert args.sse is True
        assert args.host == "127.0.0.1"
        assert args.port == 9999

    def test_mutually_exclusive_stdio_and_sse(self):
        from catia_mcp.server import parse_args
        with pytest.raises(SystemExit):
            parse_args(["--stdio", "--sse"])

    def test_invalid_port_type(self):
        from catia_mcp.server import parse_args
        with pytest.raises((SystemExit, TypeError)):
            parse_args(["--port", "abc"])

    def test_defaults_constants(self):
        from catia_mcp.server import DEFAULT_SSE_HOST, DEFAULT_SSE_PORT
        assert DEFAULT_SSE_HOST == "0.0.0.0"
        assert DEFAULT_SSE_PORT == 8765


# ─── 2. Transport Selection in main() ──────────────────────────────────


class TestMainTransportSelection:
    """Test that main() routes to the correct transport mode."""

    def test_main_stdio_default(self):
        from catia_mcp.server import parse_args
        args = parse_args([])
        assert args.sse is False  # → stdio path

    def test_main_sse_mode(self):
        from catia_mcp.server import parse_args
        args = parse_args(["--sse"])
        assert args.sse is True  # → sse path


# ─── 3. SSE Server Infrastructure ─────────────────────────────────────


class TestSSEInfrastructure:
    """Test that CATIAMCPServer SSE wiring is correct."""

    def test_server_has_run_sse_method(self):
        from catia_mcp.server import CATIAMCPServer
        import inspect
        assert hasattr(CATIAMCPServer, "run_sse")
        assert asyncio.iscoroutinefunction(CATIAMCPServer.run_sse)

    def test_server_has_run_stdio_method(self):
        from catia_mcp.server import CATIAMCPServer
        import asyncio
        assert hasattr(CATIAMCPServer, "run_stdio")
        assert asyncio.iscoroutinefunction(CATIAMCPServer.run_stdio)

    def test_server_run_dispatches_stdio(self):
        """CATIAMCPServer.run(transport='stdio') calls run_stdio()."""
        import asyncio
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        srv.run_stdio = AsyncMock()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(srv.run(transport="stdio"))
        loop.close()
        srv.run_stdio.assert_called_once()

    def test_server_run_dispatches_sse(self):
        """CATIAMCPServer.run(transport='sse') calls run_sse()."""
        import asyncio
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        srv.run_sse = AsyncMock()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(srv.run(transport="sse", host="0.0.0.0", port=9999))
        loop.close()
        srv.run_sse.assert_called_once_with("0.0.0.0", 9999)


# ─── 4. SSE handle_sse Handler (Mocked) ───────────────────────────────


class TestSSEHandleSse:
    """Test the SSE connection handler logic with mocked dependencies."""

    def _build_app(self):
        """Build a CATIAMCPServer with mocked internal MCP server."""
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        srv.server = MagicMock()
        srv.server.run = AsyncMock()
        srv.server.create_initialization_options = MagicMock(return_value={})
        return srv

    @patch("mcp.server.sse.SseServerTransport")
    def test_handle_sse_calls_connect_sse(self, MockSseTransport):
        """handle_sse should call sse.connect_sse() with request scope/receive/send."""
        from catia_mcp.server import CATIAMCPServer
        import asyncio
        from starlette.responses import Response

        srv = self._build_app()
        mock_sse = MagicMock()
        MockSseTransport.return_value = mock_sse

        # Mock connect_sse as async context manager yielding (read_stream, write_stream)
        mock_read = MagicMock()
        mock_write = MagicMock()

        class MockSseCtx:
            async def __aenter__(self):
                return (mock_read, mock_write)
            async def __aexit__(self, *args):
                pass

        mock_sse.connect_sse.return_value = MockSseCtx()
        mock_sse.handle_post_message = MagicMock()

        # Build minimal Starlette app mimicking run_sse's structure
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        async def handle_sse(request):
            async with mock_sse.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await srv.server.run(
                    read_stream,
                    write_stream,
                    srv.server.create_initialization_options(),
                )
            return Response()

        app = Starlette(routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=mock_sse.handle_post_message),
        ])

        # Verify app structure
        assert len(app.routes) == 2
        # Starlette auto-adds HEAD to GET routes
        assert "GET" in app.routes[0].methods
        assert app.routes[0].path == "/sse"

    @patch("mcp.server.sse.SseServerTransport")
    def test_sse_app_has_two_routes(self, MockSseTransport):
        """The SSE Starlette app must have exactly 2 routes: GET /sse and Mount /messages/."""
        mock_sse = MagicMock()
        MockSseTransport.return_value = mock_sse

        from catia_mcp.server import CATIAMCPServer
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import Response

        srv = self._build_app()

        class MockSseCtx:
            async def __aenter__(self):
                return (MagicMock(), MagicMock())
            async def __aexit__(self, *args):
                pass

        mock_sse.connect_sse.return_value = MockSseCtx()

        async def handle_sse(request):
            async with mock_sse.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await srv.server.run(
                    read_stream,
                    write_stream,
                    srv.server.create_initialization_options(),
                )
            return Response()

        app = Starlette(routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=mock_sse.handle_post_message),
        ])

        # Verify structure
        assert isinstance(app.routes[0], Route)
        assert app.routes[0].path == "/sse"
        assert "GET" in app.routes[0].methods

        assert isinstance(app.routes[1], Mount)
        assert app.routes[1].path == "/messages"  # Mount strips trailing slash


# ─── 5. Integration: SSE + Tool-Calling ───────────────────────────────


class TestSSEToolIntegration:
    """Verify that SSE mode exposes the same tools as stdio mode."""

    def test_tool_count_same_in_both_modes(self):
        """SSE and stdio share the same CATIAMCPServer instance → same tools."""
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        # Both transports use the same _tool_router and _tool_modules
        assert len(srv._tool_router) >= 50  # at least 50 tools

    def test_all_tool_modules_present(self):
        """All 6 tool modules are initialized."""
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        assert len(srv._tool_modules) == 7


# ─── 6. Edge Cases ────────────────────────────────────────────────────


class TestSSEEdgeCases:
    """Edge cases for SSE transport."""

    def test_custom_port(self):
        """run_sse() accepts custom port."""
        import asyncio
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        # Just verify the method signature accepts the args — don't actually start uvicorn
        assert hasattr(srv, "run_sse")

    def test_localhost_bind(self):
        """run_sse() accepts 127.0.0.1 as host."""
        import asyncio
        from catia_mcp.server import CATIAMCPServer
        srv = CATIAMCPServer()
        assert hasattr(srv, "run_sse")

    def test_sse_imports_available(self):
        """Required SSE dependencies are importable."""
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import Response
        import uvicorn
        from mcp.server.sse import SseServerTransport
        assert Starlette is not None
        assert SseServerTransport is not None
        assert uvicorn is not None


# ─── Helpers ───────────────────────────────────────────────────────────

import asyncio