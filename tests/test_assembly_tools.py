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
        assert len(defs) == 14


class TestContactConstraint:
    def test_contact_constraint(self, assem_tools, conn_mock):
        result = assem_tools.execute("catia_contact_constraint", {
            "component1": "Part1", "component2": "Part2"
        })
        assert "Contact" in result
        constraints = conn_mock.get_active_product().Connections.return_value
        constraints.AddBiEltCst.assert_called_once()

    def test_contact_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Not found"):
            assem_tools.execute("catia_contact_constraint", {
                "component1": "NonExistent", "component2": "Part2"
            })

class TestDistanceConstraint:
    def test_distance_constraint(self, assem_tools, conn_mock):
        result = assem_tools.execute("catia_distance_constraint", {
            "component1": "Part1", "component2": "Part2", "distance": 25.0
        })
        assert "Distance" in result
        assert "25.0" in result
        constraints = conn_mock.get_active_product().Connections.return_value
        constraints.AddBiEltCst.assert_called_once()

    def test_distance_negative_raises(self, assem_tools):
        with pytest.raises(ValueError, match="must be positive"):
            assem_tools.execute("catia_distance_constraint", {
                "component1": "P1", "component2": "P2", "distance": -5
            })

class TestTangentConstraint:
    def test_tangent_constraint(self, assem_tools, conn_mock):
        result = assem_tools.execute("catia_tangent_constraint", {
            "component1": "Part1", "component2": "Part2"
        })
        assert "Tangent" in result or "Tangency" in result
        constraints = conn_mock.get_active_product().Connections.return_value
        constraints.AddBiEltCst.assert_called_once()

class TestRemoveComponent:
    def test_remove_component(self, assem_tools, conn_mock):
        result = assem_tools.execute("catia_remove_component", {
            "component_name": "Part2"
        })
        assert "Part2" in result
        conn_mock.get_active_product().RemoveComponent.assert_called_once()

    def test_remove_nonexistent_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("Not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools.execute("catia_remove_component", {"component_name": "Ghost"})

class TestRemoveConstraint:
    def test_remove_constraint(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        cst = MagicMock()
        cst.Name = "Coincidence.1"
        constraints.Count = 1
        constraints.Item.return_value = cst
        result = assem_tools.execute("catia_remove_constraint", {
            "constraint_name": "Coincidence.1"
        })
        assert "Coincidence.1" in result
        product.RemoveConstraint.assert_called_once()

    def test_remove_nonexistent_constraint_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        constraints.Count = 0
        with pytest.raises(ValueError, match="not found"):
            assem_tools.execute("catia_remove_constraint", {"constraint_name": "Ghost"})
