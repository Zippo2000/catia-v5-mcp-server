"""Tests for sketcher tool input validation (mocked — no real CATIA)."""

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
    mock.get_active_part.return_value = MagicMock()
    mock.get_active_part_body.return_value = MagicMock()
    mock.get_origin_elements.return_value = {
        "xy": MagicMock(),
        "yz": MagicMock(),
        "zx": MagicMock(),
    }
    return mock


@pytest.fixture
def sk_tools(conn_mock):
    from catia_mcp.tools.sketcher import SketcherTools
    return SketcherTools(conn_mock)


class TestCreateSketchValidation:
    def test_invalid_plane(self, sk_tools):
        with pytest.raises(ValueError, match="Must be one of"):
            sk_tools._create_sketch("front")

    def test_xy_valid(self, sk_tools, conn_mock):
        conn_mock.get_active_part.return_value.OriginElements.PlaneXY = MagicMock()
        mock_sketch = MagicMock()
        conn_mock.get_active_part.return_value.CreateReferenceFromObject.return_value = MagicMock()
        body = conn_mock.get_active_part_body()
        body.Sketches.Add.return_value = mock_sketch
        mock_sketch.OpenEdition.return_value = MagicMock()
        result = sk_tools._create_sketch("xy")
        assert "Sketch created" in result


class TestCloseSketchNoActive:
    def test_no_active_raises(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools._close_sketch()


class TestDrawCircleValidation:
    def test_zero_radius(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools._draw_circle(0, 0, 0)

    def test_negative_radius(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools._draw_circle(0, 0, -5)


class TestDrawCenteredRectangleValidation:
    def test_zero_width(self, sk_tools):
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools._draw_centered_rectangle(0, 0, 0, 10)

    def test_negative_height(self, sk_tools):
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools._draw_centered_rectangle(0, 0, 10, -5)


class TestDrawSplineValidation:
    def test_empty_points(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="at least 2"):
            sk_tools._draw_spline([])

    def test_single_point(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="at least 2"):
            sk_tools._draw_spline([[0, 0]])


class TestDrawLineNoActiveSketch:
    def test_no_active_raises(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools._draw_line(0, 0, 1, 1)


class TestExecuteRouting:
    def test_unknown_tool_raises(self, sk_tools):
        with pytest.raises(ValueError, match="Unknown sketcher tool"):
            sk_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_11_tools_defined(self, sk_tools):
        defs = sk_tools.get_tool_definitions()
        assert len(defs) == 11
