"""Tests for catia_mcp.connection — CATIAConnection class (all mocked)."""

from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def fresh_com_mocks():
    """Ensure COM mocks are fresh for each test."""
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()
    yield


class TestInit:
    def test_initial_state(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        assert conn.app is None
        assert conn._initialized_com is False
        assert conn._launched_instance is False
        assert conn._locked is False


class TestIsConnected:
    def test_not_connected(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        assert conn.is_connected is False

    def test_connected_caption_raises(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        # Use a custom class so Caption access raises an Exception
        class BrokenApp:
            @property
            def Caption(self):
                raise Exception("com error")
        conn.app = BrokenApp()
        assert conn.is_connected is False
        assert conn.app is None

    def test_connected_caption_ok(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn.app = MagicMock()
        conn.app.Caption = "CATIA V5"
        assert conn.is_connected is True


class TestNormalizePath:
    def test_forward_slashes(self):
        from catia_mcp.connection import _normalize_path
        assert _normalize_path("/home/test/file.txt") == "\\home\\test\\file.txt"

    def test_mixed_slashes(self):
        from catia_mcp.connection import _normalize_path
        result = _normalize_path("C:/Users/test/file.CATPart")
        assert result == "C:\\Users\\test\\file.CATPart"

    def test_trailing_slash_removed(self):
        from catia_mcp.connection import _normalize_path
        result = _normalize_path("C:\\Users\\test\\")
        assert result == "C:\\Users\\test"

    def test_non_string_passthrough(self):
        from catia_mcp.connection import _normalize_path
        assert _normalize_path(123) == 123


class TestConnect:
    def test_already_connected(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn.app = MagicMock()
        conn.app.Caption = "CATIA V5"
        result = conn.connect()
        assert "Already connected" in result

    def test_locked_raises(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn._locked = True
        with pytest.raises(RuntimeError, match="already in progress"):
            conn.connect()

    def test_get_active_object_success(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        mock_app = MagicMock()
        mock_app.Caption = "CATIA V5"
        win32com.client.GetActiveObject.return_value = mock_app
        mock_ensure = MagicMock()
        mock_ensure.Caption = "CATIA V5"
        win32com.client.gencache.EnsureDispatch.return_value = mock_ensure

        conn = CATIAConnection()
        result = conn.connect()
        assert "Connected to running" in result
        assert conn._launched_instance is False
        assert conn._locked is False

    def test_dispatch_new_instance(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        win32com.client.GetActiveObject.side_effect = Exception("no running")
        mock_new = MagicMock()
        mock_new.Caption = "CATIA V5"
        win32com.client.gencache.EnsureDispatch.return_value = mock_new

        conn = CATIAConnection()
        result = conn.connect()
        assert "Launched new" in result
        assert conn._launched_instance is True
        # Visible was assigned (not called) — MagicMock assignment returns True
        assert mock_new.Visible == True

    def test_both_fail_raises(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        win32com.client.GetActiveObject.side_effect = Exception("no running")
        win32com.client.gencache.EnsureDispatch.side_effect = Exception("no install")

        conn = CATIAConnection()
        with pytest.raises(RuntimeError, match="Failed to connect"):
            conn.connect()
        assert conn._locked is False


class TestDisconnect:
    def test_disconnect(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn.app = MagicMock()
        conn.app.Caption = "CATIA V5"
        conn._initialized_com = True
        conn._launched_instance = True

        result = conn.disconnect()
        assert "Disconnected" in result
        assert conn.app is None
        assert conn._initialized_com is False
        assert conn._launched_instance is False


class TestClose:
    def test_not_connected(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        result = conn.close()
        assert "Not connected" in result

    def test_close_with_docs(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn.app = MagicMock()
        conn.app.Caption = "CATIA V5"
        docs = conn.app.Documents
        docs.Count = 2
        doc1 = MagicMock()
        doc2 = MagicMock()
        docs.Item.side_effect = [doc1, doc2, None]
        docs.Count = 0

        result = conn.close()
        assert "closed" in result.lower()


class TestReconnect:
    def test_get_active_object_success(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        mock_app = MagicMock()
        mock_app.Caption = "CATIA V5"
        win32com.client.GetActiveObject.return_value = mock_app

        conn = CATIAConnection()
        result = conn.reconnect()
        assert "Reconnected" in result

    def test_dispatch_fallback(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        win32com.client.GetActiveObject.side_effect = Exception("no running")
        mock_new = MagicMock()
        mock_new.Caption = "CATIA V5"
        win32com.client.Dispatch.return_value = mock_new

        conn = CATIAConnection()
        result = conn.reconnect()
        assert "Launched new" in result

    def test_both_fail(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        win32com.client.GetActiveObject.side_effect = Exception("no running")
        win32com.client.Dispatch.side_effect = Exception("no install")

        conn = CATIAConnection()
        with pytest.raises(RuntimeError, match="Failed to reconnect"):
            conn.reconnect()


class TestEnsureConnected:
    def test_already_connected(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        conn.app = MagicMock()
        conn.app.Caption = "CATIA V5"
        conn.ensure_connected()  # Should not raise

    def test_reconnect_fallback(self):
        import sys
        from catia_mcp.connection import CATIAConnection
        win32com = sys.modules["win32com"]
        conn = CATIAConnection()
        win32com.client.GetActiveObject.side_effect = Exception("no running")
        win32com.client.Dispatch.side_effect = Exception("no install")
        mock_new = MagicMock()
        mock_new.Caption = "CATIA V5"
        win32com.client.gencache.EnsureDispatch.return_value = mock_new
        conn.ensure_connected()
        assert conn.app is not None


class TestNormalizePathMethod:
    def test_method_delegates(self):
        from catia_mcp.connection import CATIAConnection
        conn = CATIAConnection()
        result = conn.normalize_path("C:/test/path")
        assert result == "C:\\test\\path"
