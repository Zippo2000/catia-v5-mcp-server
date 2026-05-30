"""Tests for assembly tools (mocked — no real CATIA)."""

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
    product_mock = MagicMock()
    mock.get_active_product.return_value = product_mock
    return mock


@pytest.fixture
def assem_tools(conn_mock):
    from catia_mcp.tools.assembly import AssemblyTools
    return AssemblyTools(conn_mock)


class TestAddComponentValidation:
    def test_relative_path_raises(self, assem_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            assem_tools._add_component("relative.CATPart")

    def test_empty_path_raises(self, assem_tools):
        with pytest.raises(ValueError, match="must not be empty"):
            assem_tools._add_component("")


class TestFixConstraint:
    def test_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools._fix_constraint("NonExistent")


class TestMoveComponent:
    def test_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools._move_component({"component_name": "NonExistent"})


class TestExecuteRouting:
    def test_unknown_tool_raises(self, assem_tools):
        with pytest.raises(ValueError, match="Unknown assembly tool"):
            assem_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_9_tools_defined(self, assem_tools):
        defs = assem_tools.get_tool_definitions()
        assert len(defs) == 9
