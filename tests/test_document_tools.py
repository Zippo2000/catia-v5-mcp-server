"""Tests for document tools (mocked — no real CATIA)."""

from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def fresh_com_mocks():
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()
    yield


@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    mock.active_document = MagicMock()
    mock.active_document.Name = "Test.Part"
    mock.documents = MagicMock()
    return mock


@pytest.fixture
def doc_tools(conn_mock):
    from catia_mcp.tools.document import DocumentTools
    return DocumentTools(conn_mock)


class TestOpenDocumentValidation:
    def test_empty_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must not be empty"):
            doc_tools._open_document("")

    def test_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools._open_document("relative.part")

    def test_non_string_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must be a string"):
            doc_tools._open_document(123)


class TestSaveDocumentValidation:
    def test_save_no_path(self, doc_tools):
        result = doc_tools._save_document(None)
        assert "saved" in result.lower()

    def test_save_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools._save_document("relative.part")


class TestExecuteRouting:
    def test_catia_close_routes(self, doc_tools, conn_mock):
        conn_mock.close.return_value = "CATIA V5 has been closed"
        result = doc_tools.execute("catia_close", {})
        assert "closed" in result.lower()
        conn_mock.close.assert_called_once()

    def test_catia_connect_routes(self, doc_tools, conn_mock):
        conn_mock.connect.return_value = "Connected to running CATIA V5"
        result = doc_tools.execute("catia_connect", {})
        assert "Connected" in result
        conn_mock.connect.assert_called_once()

    def test_catia_disconnect_routes(self, doc_tools, conn_mock):
        conn_mock.disconnect.return_value = "Disconnected from CATIA V5"
        result = doc_tools.execute("catia_disconnect", {})
        assert "Disconnected" in result

    def test_unknown_tool_raises(self, doc_tools):
        with pytest.raises(ValueError, match="Unknown document tool"):
            doc_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_catia_close_present(self, doc_tools):
        defs = doc_tools.get_tool_definitions()
        names = [d["name"] for d in defs]
        assert "catia_close" in names

    def test_all_10_tools_present(self, doc_tools):
        defs = doc_tools.get_tool_definitions()
        assert len(defs) == 10
