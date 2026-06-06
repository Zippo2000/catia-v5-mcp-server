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
    product = MagicMock()
    mock.get_active_product.return_value = product
    product.Products.Count = 2
    comp1 = MagicMock()
    comp1.Name = "Part1"
    comp1.PartNumber = "PART.001"
    comp1.Position.GetComponents.return_value = None
    comp2 = MagicMock()
    comp2.Name = "Part2"
    comp2.PartNumber = "PART.002"
    comp2.Position.GetComponents.return_value = None
    product.Products.Item.side_effect = lambda x: comp1 if x in (1, "Part1") else comp2
    constraints = MagicMock()
    constraints.Count = 0
    product.Connections.return_value = constraints
    mock.refresh_display = MagicMock()
    return mock


@pytest.fixture
def assem_tools(conn_mock):
    from catia_mcp.tools.assembly import AssemblyTools
    return AssemblyTools(conn_mock)


# ── FR-07.1 catia_add_component ─────────────────────────────────────────

class TestAddComponent:
    def test_add_component_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.AddComponentsFromFiles.return_value = [MagicMock()]
        result = assem_tools.execute("catia_add_component", {"file_path": "C:/parts/Part1.CATPart"})
        assert "Component added" in result or "added" in result.lower()

    def test_add_component_relative_path_raises(self, assem_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            assem_tools.execute("catia_add_component", {"file_path": "relative.CATPart"})

    def test_add_component_empty_path_raises(self, assem_tools):
        with pytest.raises(ValueError, match="must not be empty"):
            assem_tools.execute("catia_add_component", {"file_path": ""})


# ── FR-07.2 catia_add_new_part ──────────────────────────────────────────

class TestAddNewPart:
    def test_add_new_part_default(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        new_part = MagicMock()
        new_part.Name = "Part.1"
        product.Products.AddNewProduct.return_value = new_part
        result = assem_tools.execute("catia_add_new_part", {})
        assert "Part.1" in result or "created" in result.lower()

    def test_add_new_part_with_name(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        new_part = MagicMock()
        new_part.Name = "MyComponent"
        product.Products.AddNewProduct.return_value = new_part
        result = assem_tools.execute("catia_add_new_part", {"name": "MyComponent"})
        assert "MyComponent" in result or "created" in result.lower()


# ── FR-07.3 catia_fix_constraint ────────────────────────────────────────

class TestFixConstraint:
    def test_fix_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        fix_cst = MagicMock()
        constraints.AddMonoEltCst.return_value = fix_cst
        result = assem_tools.execute("catia_fix_constraint", {"component_name": "Part1"})
        assert "Fix" in result or "fix" in result.lower()
        constraints.AddMonoEltCst.assert_called_once()

    def test_fix_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools.execute("catia_fix_constraint", {"component_name": "NonExistent"})


# ── FR-07.4 catia_coincidence_constraint ────────────────────────────────

class TestCoincidenceConstraint:
    def test_coincidence_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        cst = MagicMock()
        constraints.AddBiEltCst.return_value = cst
        result = assem_tools.execute("catia_coincidence_constraint", {"component1": "Part1", "component2": "Part2"})
        assert "Coincidence" in result
        constraints.AddBiEltCst.assert_called_once()

    def test_coincidence_nonexistent_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Not found"):
            assem_tools.execute("catia_coincidence_constraint", {"component1": "Ghost", "component2": "Part2"})


# ── FR-07.5 catia_offset_constraint ─────────────────────────────────────

class TestOffsetConstraint:
    def test_offset_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        cst = MagicMock()
        constraints.AddBiEltCst.return_value = cst
        result = assem_tools.execute("catia_offset_constraint", {"component1": "Part1", "component2": "Part2", "offset": 10})
        assert "Offset" in result
        assert "10" in result
        constraints.AddBiEltCst.assert_called_once()

    def test_offset_negative_raises(self, assem_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            assem_tools.execute("catia_offset_constraint", {"component1": "P1", "component2": "P2", "offset": -5})


# ── FR-07.6 catia_angle_constraint ──────────────────────────────────────

class TestAngleConstraint:
    def test_angle_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        cst = MagicMock()
        constraints.AddBiEltCst.return_value = cst
        result = assem_tools.execute("catia_angle_constraint", {"component1": "Part1", "component2": "Part2", "angle": 45})
        assert "Angle" in result
        assert "45" in result
        constraints.AddBiEltCst.assert_called_once()

    def test_angle_negative_raises(self, assem_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            assem_tools.execute("catia_angle_constraint", {"component1": "P1", "component2": "P2", "angle": -30})


# ── FR-07.7 catia_move_component ────────────────────────────────────────

class TestMoveComponent:
    def test_move_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        comp = product.Products.Item.return_value
        comp.Position.GetComponents.return_value = None
        result = assem_tools.execute("catia_move_component", {"component_name": "Part1", "tx": 10, "ty": 20, "tz": 30})
        assert "Part1" in result or "moved" in result.lower()

    def test_move_with_rotation(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        comp = product.Products.Item.return_value
        comp.Position.GetComponents.return_value = None
        result = assem_tools.execute("catia_move_component", {"component_name": "Part1", "rx": 90})
        assert "Part1" in result or "moved" in result.lower()

    def test_move_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools.execute("catia_move_component", {"component_name": "NonExistent"})


# ── FR-07.8 catia_list_components ───────────────────────────────────────

class TestListComponents:
    def test_list_components(self, assem_tools, conn_mock):
        result = assem_tools.execute("catia_list_components", {})
        assert isinstance(result, str)
        assert "Part1" in result

    def test_list_components_empty(self, assem_tools, conn_mock):
        conn_mock.get_active_product().Products.Count = 0
        result = assem_tools.execute("catia_list_components", {})
        assert "No component" in result or "No" in result


# ── FR-07.9 catia_list_constraints ──────────────────────────────────────

class TestListConstraints:
    def test_list_constraints(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        constraints.Count = 2
        cst1 = MagicMock()
        cst1.Name = "Fix.Part1"
        cst1.Type = "Fix"
        cst1.Status = 0
        cst2 = MagicMock()
        cst2.Name = "Coincidence.1"
        cst2.Type = "Coincidence"
        cst2.Status = 0
        constraints.Item.side_effect = lambda i: [cst1, cst2][i - 1]
        result = assem_tools.execute("catia_list_constraints", {})
        assert isinstance(result, str)
        assert "Fix.Part1" in result

    def test_list_constraints_empty(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        constraints.Count = 0
        result = assem_tools.execute("catia_list_constraints", {})
        assert "No constraint" in result or "No" in result


# ── Existing tests ────────────────────────────────────────────────────────

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


class TestGroundConstraint:
    def test_ground_valid(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        constraints = product.Connections.return_value
        ground_cst = MagicMock()
        ground_cst.Name = "Ground.Part1"
        constraints.AddMonoEltCst.return_value = ground_cst
        result = assem_tools.execute("catia_ground_constraint", {"component_name": "Part1"})
        assert "Ground" in result or "ground" in result.lower()
        constraints.AddMonoEltCst.assert_called_once()

    def test_ground_nonexistent_component_raises(self, assem_tools, conn_mock):
        product = conn_mock.get_active_product()
        product.Products.Item.side_effect = Exception("not found")
        with pytest.raises(ValueError, match="not found"):
            assem_tools.execute("catia_ground_constraint", {"component_name": "NonExistent"})


class TestExecuteRouting:
    def test_unknown_tool_raises(self, assem_tools):
        with pytest.raises(ValueError, match="Unknown assembly tool"):
            assem_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_15_tools_defined(self, assem_tools):
        defs = assem_tools.get_tool_definitions()
        assert len(defs) == 15
