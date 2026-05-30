"""CATIA V5 MCP Server.

Main entry point. Exposes all CATIA V5 automation tools via the
Model Context Protocol (MCP) for use with Claude Desktop, Claude Code,
vLLM.rs, LM Studio, Open WebUI, and any other MCP-compatible client.

Usage:
    python -m catia_mcp                     # stdio (Claude Desktop/Code, default)
    python -m catia_mcp --sse               # SSE over HTTP (Hermes, vLLM, LM Studio)
    python -m catia_mcp --streamable-http   # Streamable HTTP (Open WebUI)
    # or
    catia-mcp  (if installed via pip)
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import signal
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from catia_mcp.connection import CATIAConnection
from catia_mcp.tools.assembly import AssemblyTools
from catia_mcp.tools.document import DocumentTools
from catia_mcp.tools.export import ExportTools
from catia_mcp.tools.measurement import MeasurementTools
from catia_mcp.tools.gsd import GSDTools
from catia_mcp.tools.part_design import PartDesignTools
from catia_mcp.tools.sketcher import SketcherTools

# ── Logging ──
import os
import tempfile

_log_dir = os.path.join(tempfile.gettempdir(), "catia-mcp")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "catia_mcp.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(_log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("catia_mcp")

# ── CLI Arguments ──
DEFAULT_SSE_HOST = "0.0.0.0"
DEFAULT_SSE_PORT = 3000
DEFAULT_STREAMABLE_HTTP_PORT = 3001


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for transport mode selection."""
    parser = argparse.ArgumentParser(
        description="CATIA V5 MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--sse",
        action="store_true",
        default=False,
        help="Run as SSE MCP server over HTTP (for Hermes, vLLM, LM Studio)",
    )
    transport.add_argument(
        "--streamable-http",
        action="store_true",
        default=False,
        help="Run as Streamable HTTP MCP server (for Open WebUI)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_SSE_HOST,
        help=f"HTTP bind host (default: {DEFAULT_SSE_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_SSE_PORT,
        help=f"SSE bind port (default: {DEFAULT_SSE_PORT})",
    )
    parser.add_argument(
        "--shport",
        type=int,
        default=DEFAULT_STREAMABLE_HTTP_PORT,
        help=f"Streamable HTTP bind port (default: {DEFAULT_STREAMABLE_HTTP_PORT})",
    )
    return parser.parse_args(argv)


class CATIAMCPServer:
    """MCP Server that bridges Claude (or any MCP client) to CATIA V5 via COM Automation."""

    def __init__(self) -> None:
        self.server = Server("catia-v5-mcp")
        self.connection = CATIAConnection()

        # Initialize tool modules with shared connection
        self.document_tools = DocumentTools(self.connection)
        self.sketcher_tools = SketcherTools(self.connection)
        self.part_design_tools = PartDesignTools(self.connection)
        self.assembly_tools = AssemblyTools(self.connection)
        self.measurement_tools = MeasurementTools(self.connection)
        self.export_tools = ExportTools(self.connection)
        self.gsd_tools = GSDTools(self.connection)

        # All tool modules
        self._tool_modules = [
            self.document_tools,
            self.sketcher_tools,
            self.part_design_tools,
            self.assembly_tools,
            self.measurement_tools,
            self.export_tools,
            self.gsd_tools,
        ]

        # Build tool name -> module routing table
        self._tool_router: dict[str, Any] = {}
        for module in self._tool_modules:
            for tool_def in module.get_tool_definitions():
                self._tool_router[tool_def["name"]] = module

        # Asyncio lock for serializing COM calls (COM is single-threaded)
        self._com_lock = asyncio.Lock()

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            tools = []
            for module in self._tool_modules:
                for tool_def in module.get_tool_definitions():
                    tools.append(
                        Tool(
                            name=tool_def["name"],
                            description=tool_def["description"],
                            inputSchema=tool_def["inputSchema"],
                        )
                    )
            logger.info("Listed %d tools", len(tools))
            return tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[TextContent]:
            arguments = arguments or {}
            logger.info("Tool call: %s(%s)", name, arguments)

            try:
                module = self._tool_router.get(name)
                if module is None:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: '{name}'. Use list_tools to see available tools.",
                    )]

                # Serialize COM calls with an asyncio lock
                # CATIA COM is single-threaded, so we must serialize access
                async with self._com_lock:
                    # Auto-connect for non-connect/close tools
                    if name not in ("catia_connect", "catia_disconnect", "catia_close"):
                        if not self.connection.is_connected:
                            connect_msg = self.connection.connect()
                            logger.info("Auto-connected: %s", connect_msg)

                    result = module.execute(name, arguments)

                logger.info("Tool result: %s", result[:200] if len(result) > 200 else result)
                return [TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error in {name}: {e}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=error_msg)]

    async def run_stdio(self) -> None:
        """Run the MCP server over stdio (Claude Desktop / Claude Code)."""
        pd_source = inspect.getsourcefile(PartDesignTools)
        pad_source = inspect.getsource(PartDesignTools._pad)
        has_inworkobject = "InWorkObject" in pad_source

        logger.info("=" * 60)
        logger.info("Starting CATIA V5 MCP Server (stdio)...")
        logger.info("PartDesignTools source: %s", pd_source)
        logger.info("_pad has InWorkObject: %s", has_inworkobject)
        logger.info("Registered %d tools across %d modules",
                     len(self._tool_router), len(self._tool_modules))
        logger.info("=" * 60)

        # Set up graceful shutdown
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self._shutdown)
            loop.add_signal_handler(signal.SIGTERM, self._shutdown)
        except (NotImplementedError, OSError):
            # Windows doesn't support add_signal_handler
            pass

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def run_sse(self, host: str = DEFAULT_SSE_HOST, port: int = DEFAULT_SSE_PORT) -> None:
        """Run the MCP server over HTTP SSE (Server-Sent Events).

        Creates two ASGI endpoints:
            GET  /sse         → SSE stream (server → client)
            POST /messages/   → Client messages (client → server)

        Compatible with Hermes, vLLM.rs, LM Studio, Cursor, and any
        MCP client that supports the SSE transport.
        """
        import uvicorn
        from sse_starlette import EventSourceResponse  # noqa: F401
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        from mcp.server.sse import SseServerTransport

        pd_source = inspect.getsourcefile(PartDesignTools)
        pad_source = inspect.getsource(PartDesignTools._pad)
        has_inworkobject = "InWorkObject" in pad_source

        logger.info("=" * 60)
        logger.info("Starting CATIA V5 MCP Server (SSE)...")
        logger.info("Transport: SSE over HTTP")
        logger.info("Host: %s, Port: %d", host, port)
        logger.info("SSE endpoint:  http://%s:%d/sse", host, port)
        logger.info("Message endpoint: http://%s:%d/messages/", host, port)
        logger.info("PartDesignTools source: %s", pd_source)
        logger.info("_pad has InWorkObject: %s", has_inworkobject)
        logger.info("Registered %d tools across %d modules",
                     len(self._tool_router), len(self._tool_modules))
        logger.info("=" * 60)

        # Create SSE transport — handles the ASGI protocol
        sse = SseServerTransport("/messages/")

        # SSE connection handler: each GET /sse opens a new MCP session
        async def handle_sse(request):
            try:
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        self.server.create_initialization_options(),
                    )
            except Exception:
                # Client disconnected (ClosedResourceError, ConnectionResetError, etc.)
                # This is normal when the MCP client opens a new SSE connection
                # for each request instead of keeping one persistent connection.
                pass
            # Return empty response to avoid NoneType error on disconnect
            return Response()

        # Build Starlette app with two routes
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # uvicorn handles signals (SIGINT/SIGTERM) and graceful shutdown
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        srv = uvicorn.Server(config)

        try:
            await srv.serve()
        finally:
            # Clean up CATIA connection on server exit
            try:
                self.connection.disconnect()
            except Exception:
                pass
            logger.info("SSE server shutdown complete")

    async def run_streamable_http(self, host: str = DEFAULT_SSE_HOST, port: int = DEFAULT_STREAMABLE_HTTP_PORT) -> None:
        """Run the MCP server over Streamable HTTP (RFC-compatible MCP HTTP transport).

        Creates a single ASGI endpoint:
            POST /mcp  → Client messages (bidirectional via HTTP)
            GET  /mcp  → SSE stream for server-to-client messages

        Compatible with Open WebUI and any MCP client that supports
        the Streamable HTTP transport.
        """
        import contextlib

        import uvicorn

        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

        pd_source = inspect.getsourcefile(PartDesignTools)
        pad_source = inspect.getsource(PartDesignTools._pad)
        has_inworkobject = "InWorkObject" in pad_source

        logger.info("=" * 60)
        logger.info("Starting CATIA V5 MCP Server (Streamable HTTP)...")
        logger.info("Transport: Streamable HTTP")
        logger.info("Host: %s, Port: %d", host, port)
        logger.info("Endpoint: http://%s:%d/mcp", host, port)
        logger.info("PartDesignTools source: %s", pd_source)
        logger.info("_pad has InWorkObject: %s", has_inworkobject)
        logger.info("Registered %d tools across %d modules",
                     len(self._tool_router), len(self._tool_modules))
        logger.info("=" * 60)

        # StreamableHTTPSessionManager requires its run() to be called as a lifespan
        # context manager before handle_request() can process HTTP requests.
        # We wrap it in a minimal ASGI app that delegates to the session manager.
        session_manager = StreamableHTTPSessionManager(self.server)

        @contextlib.asynccontextmanager
        async def lifespan(app):
            async with session_manager.run():
                yield

        async def asgi_app(scope, receive, send):
            if scope["type"] == "lifespan":
                # Handle lifespan events
                message = await receive()
                if message["type"] == "lifespan.startup":
                    async with session_manager.run():
                        await send({"type": "lifespan.startup.complete"})
                        message = await receive()
                        if message["type"] == "lifespan.shutdown":
                            await send({"type": "lifespan.shutdown.complete"})
                return
            await session_manager.handle_request(scope, receive, send)

        config = uvicorn.Config(
            asgi_app,
            host=host,
            port=port,
            log_level="info",
            lifespan="on",
        )
        srv = uvicorn.Server(config)

        try:
            await srv.serve()
        finally:
            # Clean up CATIA connection on server exit
            try:
                self.connection.disconnect()
            except Exception:
                pass
            logger.info("Streamable HTTP server shutdown complete")

    async def run(
        self,
        transport: str = "stdio",
        host: str = DEFAULT_SSE_HOST,
        port: int = DEFAULT_SSE_PORT,
        shport: int = DEFAULT_STREAMABLE_HTTP_PORT,
    ) -> None:
        """Run the MCP server with the specified transport.

        Args:
            transport: "stdio", "sse", or "streamable_http"
            host: HTTP bind host (ignored for stdio)
            port: SSE bind port (ignored for stdio and streamable_http)
            shport: Streamable HTTP bind port (ignored for stdio and sse)
        """
        if transport == "sse":
            await self.run_sse(host, port)
        elif transport == "streamable_http":
            await self.run_streamable_http(host, shport)
        else:
            await self.run_stdio()

    def _shutdown(self) -> None:
        """Graceful shutdown handler (used by stdio mode)."""
        logger.info("Shutting down CATIA V5 MCP Server...")
        try:
            # Use disconnect (not close) on shutdown - user decides when to close CATIA
            self.connection.disconnect()
        except Exception:
            pass
        logger.info("Server shutdown complete")
        # Exit cleanly
        try:
            asyncio.get_running_loop().stop()
        except Exception:
            pass


def main() -> None:
    """Entry point for the CATIA V5 MCP Server."""
    args = parse_args()
    server = CATIAMCPServer()

    if args.sse:
        asyncio.run(server.run(transport="sse", host=args.host, port=args.port))
    elif args.streamable_http:
        asyncio.run(server.run(transport="streamable_http", host=args.host, shport=args.shport))
    else:
        asyncio.run(server.run(transport="stdio"))


if __name__ == "__main__":
    main()
