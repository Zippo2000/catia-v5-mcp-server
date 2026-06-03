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
    mock.normalize_path.return_value = "C:/out/part.stp"
    viewer = MagicMock()
    mock._safe_active_viewer.return_value = viewer
    return mock


@pytest.fixture
def exp_tools(conn_mock):
    from catia_mcp.tools.export import ExportTools
    return ExportTools(conn_mock)


# ── FR-09.1 catia_export ────────────────────────────────────────────────

class TestExport:
    def test_export_step(self, exp_tools, conn_mock):
        conn_mock.active_document.ExportData = MagicMock()
        result = exp_tools.execute("catia_export", {"file_path": "C:/out/part.stp", "format": "step"})
        assert "format" in result.lower()
        assert "STEP" in result or "stp" in result.lower()

    def test_export_iges(self, exp_tools, conn_mock):
        conn_mock.active_document.ExportData = MagicMock()
        result = exp_tools.execute("catia_export", {"file_path": "C:/out/part.igs", "format": "iges"})
        assert "format" in result.lower()

    def test_export_stl(self, exp_tools, conn_mock):
        conn_mock.active_document.ExportData = MagicMock()
        result = exp_tools.execute("catia_export", {"file_path": "C:/out/part.stl", "format": "stl"})
        assert "format" in result.lower()

    def test_export_from_extension(self, exp_tools, conn_mock):
        conn_mock.active_document.ExportData = MagicMock()
        result = exp_tools.execute("catia_export", {"file_path": "C:/out/part.stp"})
        assert "format" in result.lower()

    def test_export_invalid_format(self, exp_tools):
        with pytest.raises(ValueError, match="Unsupported export format"):
            exp_tools.execute("catia_export", {"file_path": "C:/out/bad.xyz", "format": "xyz"})

    def test_export_relative_path_raises(self, exp_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            exp_tools.execute("catia_export", {"file_path": "relative.stp", "format": "step"})


# ── FR-09.2 catia_screenshot ────────────────────────────────────────────

class TestScreenshot:
    def test_screenshot_valid(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_screenshot", {"file_path": "C:/screenshots/part.png", "width": 1920, "height": 1080})
        assert "Screenshot saved" in result or "screenshot" in result.lower()
        viewer.CaptureToFile.assert_called_once()

    def test_screenshot_custom_resolution(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_screenshot", {"file_path": "C:/screenshots/part.png", "width": 3840, "height": 2160})
        assert "Screenshot saved" in result or "screenshot" in result.lower()

    def test_screenshot_zero_width(self, exp_tools):
        with pytest.raises(ValueError, match="must be positive"):
            exp_tools.execute("catia_screenshot", {"file_path": "C:/out/screenshot.png", "width": 0, "height": 1080})

    def test_screenshot_negative_height(self, exp_tools):
        with pytest.raises(ValueError, match="must be positive"):
            exp_tools.execute("catia_screenshot", {"file_path": "C:/out/screenshot.png", "width": 1920, "height": -1})

    def test_screenshot_relative_path_raises(self, exp_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            exp_tools.execute("catia_screenshot", {"file_path": "relative.png", "width": 1920, "height": 1080})

    def test_screenshot_no_viewer_raises(self, exp_tools, conn_mock):
        conn_mock._safe_active_viewer.return_value = None
        with pytest.raises(RuntimeError, match="No active 3D viewer"):
            exp_tools.execute("catia_screenshot", {"file_path": "C:/out/screenshot.png"})


# ── FR-09.3 catia_set_view ──────────────────────────────────────────────

class TestSetView:
    def test_set_view_front(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_set_view", {"view": "front"})
        assert "front" in result.lower()
        viewer.Reframe.assert_called()

    def test_set_view_isometric(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_set_view", {"view": "isometric"})
        assert "isometric" in result.lower()

    def test_set_view_top(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_set_view", {"view": "top"})
        assert "top" in result.lower()

    def test_set_view_left(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_set_view", {"view": "left"})
        assert "left" in result.lower()

    def test_set_view_right(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_set_view", {"view": "right"})
        assert "right" in result.lower()

    def test_set_view_invalid(self, exp_tools):
        with pytest.raises(ValueError, match="Unknown view"):
            exp_tools.execute("catia_set_view", {"view": "invalid"})

    def test_set_view_no_viewer_raises(self, exp_tools, conn_mock):
        conn_mock._safe_active_viewer.return_value = None
        with pytest.raises(RuntimeError, match="No active 3D viewer"):
            exp_tools.execute("catia_set_view", {"view": "front"})


# ── FR-09.4 catia_fit_all ───────────────────────────────────────────────

class TestFitAll:
    def test_fit_all_valid(self, exp_tools, conn_mock):
        viewer = conn_mock._safe_active_viewer.return_value
        result = exp_tools.execute("catia_fit_all", {})
        assert "fitted" in result.lower() or "View fitted" in result
        viewer.Reframe.assert_called_once()

    def test_fit_all_no_viewer_raises(self, exp_tools, conn_mock):
        conn_mock._safe_active_viewer.return_value = None
        with pytest.raises(RuntimeError, match="No active 3D viewer"):
            exp_tools.execute("catia_fit_all", {})


# ── Existing tests (routing & definitions) ────────────────────────────────

class TestExecuteRouting:
    def test_unknown_tool_raises(self, exp_tools):
        with pytest.raises(ValueError, match="Unknown export tool"):
            exp_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_4_tools_defined(self, exp_tools):
        defs = exp_tools.get_tool_definitions()
        assert len(defs) == 4
