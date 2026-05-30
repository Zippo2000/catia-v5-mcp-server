"""Tests for export tools (mocked — no real CATIA)."""

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
def exp_tools(conn_mock):
    from catia_mcp.tools.export import ExportTools
    return ExportTools(conn_mock)


class TestExportValidation:
    def test_invalid_format(self, exp_tools):
        with pytest.raises(ValueError, match="Unsupported export format"):
            exp_tools._export("C:/out/bad.xyz", "xyz")

    def test_relative_path_raises(self, exp_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            exp_tools._export("relative.stp", "step")

    def test_format_from_extension(self, exp_tools, conn_mock):
        conn_mock.active_document.ExportData = MagicMock()
        conn_mock.normalize_path.return_value = "C:/out/part.stp"
        result = exp_tools._export("C:/out/part.stp", "step")
        assert "format" in result.lower()
        assert "step" in result.lower()


class TestScreenshotValidation:
    def test_zero_width(self, exp_tools):
        with pytest.raises(ValueError, match="must be positive"):
            exp_tools._screenshot("C:/out/screenshot.png", 0, 1080)

    def test_negative_height(self, exp_tools):
        with pytest.raises(ValueError, match="must be positive"):
            exp_tools._screenshot("C:/out/screenshot.png", 1920, -1)

    def test_relative_path_raises(self, exp_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            exp_tools._screenshot("relative.png", 1920, 1080)


class TestSetView:
    def test_invalid_view(self, exp_tools):
        with pytest.raises(ValueError, match="Unknown view"):
            exp_tools._set_view("invalid")


class TestExecuteRouting:
    def test_unknown_tool_raises(self, exp_tools):
        with pytest.raises(ValueError, match="Unknown export tool"):
            exp_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_4_tools_defined(self, exp_tools):
        defs = exp_tools.get_tool_definitions()
        assert len(defs) == 4
