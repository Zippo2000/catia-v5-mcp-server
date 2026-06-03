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
    part = MagicMock()
    mock.get_active_part.return_value = part
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    mock.app = MagicMock()
    spa = MagicMock()
    mock.app.GetWorkbench.return_value = spa
    measurable = MagicMock()
    measurable.bounding_box = [-10, -20, -30, 10, 20, 30]
    measurable.Volume = 1000.0
    measurable.Area = 500.0
    measurable.cog = [0.0, 0.0, 0.0]
    measurable.inertia = [1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 3.0]
    spa.GetMeasurable.return_value = measurable
    part.Parameters.Count = 2
    p1 = MagicMock()
    p1.Name = "Param1"
    p1.Value = 10.0
    p1.Comment = "First param"
    p2 = MagicMock()
    p2.Name = "Param2"
    p2.Value = 20.0
    p2.Comment = "Second param"
    part.Parameters.Item.side_effect = lambda x: p1 if (x == 1 or x == "Param1") else p2
    part.Parameters.Item.return_value = p2
    mock.hso = MagicMock()
    mock.hso.Count = 1
    mock.hso.Item.return_value.Value = MagicMock()
    mock.refresh_display = MagicMock()
    return mock


@pytest.fixture
def meas_tools(conn_mock):
    from catia_mcp.tools.measurement import MeasurementTools
    return MeasurementTools(conn_mock)


# ── FR-08.1 catia_measure_distance ──────────────────────────────────────

class TestMeasureDistance:
    def test_distance_valid(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetMinimumDistance.return_value = 15.5
        spa.GetMeasurable.return_value = measurable
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_distance", {"element1": "Pad.1", "element2": "Sketch.1"})
        assert "15.5" in result or "distance" in result.lower()

    def test_element_not_found_raises(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_distance", {"element1": "Ghost", "element2": "Pad.1"})


# ── FR-08.2 catia_get_inertia ───────────────────────────────────────────

class TestGetInertia:
    def test_inertia_valid(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_get_inertia", {})
        assert isinstance(result, str)
        assert "volume" in result.lower() or "1000" in result

    def test_inertia_with_density(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_get_inertia", {"density": 7800})
        assert isinstance(result, str)
        assert "mass" in result.lower() or "7800" in result

    def test_negative_density_raises(self, meas_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            meas_tools.execute("catia_get_inertia", {"density": -1})


# ── FR-08.3 catia_get_bounding_box ──────────────────────────────────────

class TestGetBoundingBox:
    def test_bounding_box_valid(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_get_bounding_box", {})
        assert isinstance(result, str)
        assert "min" in result or "max" in result

    def test_bounding_box_not_found(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        spa.GetMeasurable.side_effect = Exception("not measurable")
        with pytest.raises((RuntimeError, Exception), match="not measurable|GetBoundingBox"):
            meas_tools.execute("catia_get_bounding_box", {})


# ── FR-08.4 catia_get_parameters ────────────────────────────────────────

class TestGetParameters:
    def test_get_parameters_all(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_get_parameters", {})
        assert isinstance(result, str)
        assert "Param1" in result

    def test_get_parameters_with_filter(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_get_parameters", {"filter": "Param1"})
        assert isinstance(result, str)
        assert "Param1" in result
        assert "Param2" not in result

    def test_get_parameters_empty(self, meas_tools, conn_mock):
        conn_mock.get_active_part().Parameters.Count = 0
        result = meas_tools.execute("catia_get_parameters", {})
        assert "No parameter" in result or "No" in result


# ── FR-08.5 catia_set_parameter ─────────────────────────────────────────

class TestSetParameter:
    def test_set_parameter_valid(self, meas_tools, conn_mock):
        part = conn_mock.get_active_part()
        p1 = MagicMock()
        p1.Name = "Param1"
        p1.Value = 10.0
        part.Parameters.Item.side_effect = lambda name: p1 if name == "Param1" else MagicMock()
        result = meas_tools.execute("catia_set_parameter", {"name": "Param1", "value": 25.0})
        assert "Param1" in result
        assert p1.Value == 25.0

    def test_nonexistent_parameter_raises(self, meas_tools, conn_mock):
        part = conn_mock.get_active_part()
        part.Parameters.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            meas_tools.execute("catia_set_parameter", {"name": "NonExistent", "value": 10.0})


# ── FR-08.6 catia_update_part ───────────────────────────────────────────

class TestUpdatePart:
    def test_update_part_valid(self, meas_tools, conn_mock):
        result = meas_tools.execute("catia_update_part", {})
        assert "updated" in result.lower() or "Part updated" in result
        conn_mock.get_active_part().Update.assert_called()


# ── FR-08.7 catia_measure_angle ─────────────────────────────────────────

class TestMeasureAngle:
    def test_measure_angle(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetAngle.return_value = 0.785398
        spa.GetMeasurable.return_value = measurable
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_angle", {"element1": "Face.1", "element2": "Face.2"})
        assert "45.0" in result or "Angle" in result

    def test_measure_angle_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises((RuntimeError, ValueError), match="not found"):
            meas_tools.execute("catia_measure_angle", {"element1": "Ghost", "element2": "Face.2"})


# ── FR-08.8 catia_measure_area ──────────────────────────────────────────

class TestMeasureArea:
    def test_measure_area(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.Area = 1234.56
        spa.GetMeasurable.return_value = measurable
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_area", {"element": "Face.1"})
        assert "1234.56" in result
        assert "mm" in result

    def test_measure_area_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_area", {"element": "Ghost"})


# ── FR-08.9 catia_measure_length ────────────────────────────────────────

class TestMeasureLength:
    def test_measure_length(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.Length = 50.123
        spa.GetMeasurable.return_value = measurable
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_length", {"element": "Edge.1"})
        assert "50.123" in result
        assert "mm" in result

    def test_measure_length_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_length", {"element": "Ghost"})


# ── FR-08.10 catia_measure_interference ─────────────────────────────────

class TestMeasureInterference:
    def test_measure_interference_no_overlap(self, meas_tools, conn_mock):
        spa = conn_mock.app.GetWorkbench.return_value
        measurable = MagicMock()
        measurable.GetMinimumDistance.return_value = 5.0
        spa.GetMeasurable.return_value = measurable
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
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = meas_tools.execute("catia_measure_interference", {"element1": "Body.1", "element2": "Body.2"})
        assert "Interference" in result
        assert "overlap" in result

    def test_measure_interference_not_found(self, meas_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            meas_tools.execute("catia_measure_interference", {"element1": "Ghost", "element2": "Body.2"})


# ── Existing tests (routing & definitions) ────────────────────────────────

class TestSetParameterValidation:
    def test_nonexistent_parameter_raises(self, meas_tools, conn_mock):
        part = conn_mock.get_active_part()
        part.Parameters.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            meas_tools._set_parameter("NonExistent", 10.0)


class TestExecuteRouting:
    def test_unknown_tool_raises(self, meas_tools):
        with pytest.raises(ValueError, match="Unknown measurement tool"):
            meas_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_10_tools_defined(self, meas_tools):
        defs = meas_tools.get_tool_definitions()
        assert len(defs) == 10
