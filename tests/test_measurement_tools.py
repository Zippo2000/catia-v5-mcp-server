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
        assert len(defs) == 6
