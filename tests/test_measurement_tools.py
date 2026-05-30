"""Tests for measurement tools (mocked — no real CATIA)."""

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
    mock.app = MagicMock()
    return mock


@pytest.fixture
def meas_tools(conn_mock):
    from catia_mcp.tools.measurement import MeasurementTools
    return MeasurementTools(conn_mock)


class TestGetInertiaValidation:
    def test_negative_density_raises(self, meas_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            meas_tools._get_inertia(density=-1)


class TestSetParameterValidation:
    def test_nonexistent_parameter_raises(self, meas_tools, conn_mock):
        part = conn_mock.get_active_part()
        part.Parameters.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            meas_tools._set_parameter("NonExistent", 10.0)


class TestMeasureDistance:
    def test_element_not_found_raises(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        sel = conn_mock.hso
        sel.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools._measure_distance("Pad.1", "Sketch.1")


class TestExecuteRouting:
    def test_unknown_tool_raises(self, meas_tools):
        with pytest.raises(ValueError, match="Unknown measurement tool"):
            meas_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_6_tools_defined(self, meas_tools):
        defs = meas_tools.get_tool_definitions()
        assert len(defs) == 10


class TestMeasureAngle:
    def test_measure_angle(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetAngle.return_value = 0.785398  # 45 deg in radians
        spa.GetMeasurable.return_value = measurable
        part = conn_mock.get_active_part.return_value
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_angle", {"element1": "Face.1", "element2": "Face.2"})
        assert "45.0" in result or "Angle" in result

    def test_measure_angle_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises((RuntimeError, ValueError), match="not found"):
            meas_tools.execute("catia_measure_angle", {"element1": "Ghost", "element2": "Face.2"})


class TestMeasureArea:
    def test_measure_area(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.Area = 1234.56
        spa.GetMeasurable.return_value = measurable
        part = conn_mock.get_active_part.return_value
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_area", {"element": "Face.1"})
        assert "1234.56" in result
        assert "mm" in result

    def test_measure_area_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_area", {"element": "Ghost"})


class TestMeasureLength:
    def test_measure_length(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.Length = 50.123
        spa.GetMeasurable.return_value = measurable
        part = conn_mock.get_active_part.return_value
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_length", {"element": "Edge.1"})
        assert "50.123" in result
        assert "mm" in result

    def test_measure_length_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_length", {"element": "Ghost"})


class TestMeasureInterference:
    def test_measure_interference_no_overlap(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetMinimumDistance.return_value = 5.0
        spa.GetMeasurable.return_value = measurable
        part = conn_mock.get_active_part.return_value
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_interference", {"element1": "Body.1", "element2": "Body.2"})
        assert "No interference" in result
        assert "clearance" in result

    def test_measure_interference_with_overlap(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetMinimumDistance.return_value = -2.5
        spa.GetMeasurable.return_value = measurable
        part = conn_mock.get_active_part.return_value
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_interference", {"element1": "Body.1", "element2": "Body.2"})
        assert "Interference" in result
        assert "overlap" in result

    def test_measure_interference_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_interference", {"element1": "Ghost", "element2": "Body.2"})
