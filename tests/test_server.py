"""Server-level smoke tests (mocked COM, no real CATIA)."""

from unittest.mock import MagicMock
import pytest


def _has_mcp() -> bool:
    try:
        import mcp.server
        return True
    except ImportError:
        return False


@pytest.fixture(autouse=True)
def fresh_com_mocks():
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()
    yield


class TestServerToolCount:
    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_all_tools_registered(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        assert len(server._tool_router) >= 45, (
            f"Expected 45+ tools, got {len(server._tool_router)}"
        )

    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_tool_router_has_all_modules(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        assert len(server._tool_modules) == 6


class TestToolRouting:
    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_catia_close_not_auto_connected(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        import inspect
        source = inspect.getsource(server._setup_handlers)
        assert "catia_close" in source

    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_unknown_tool_returns_error(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        assert "catia_nonexistent" not in server._tool_router


class TestServerInit:
    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_server_creates_connection(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        assert server.connection is not None

    @pytest.mark.skipif(not _has_mcp(), reason="mcp module not installed")
    def test_has_com_lock(self):
        from catia_mcp.server import CATIAMCPServer
        server = CATIAMCPServer()
        assert hasattr(server, "_com_lock")
