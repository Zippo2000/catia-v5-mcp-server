"""Tests for part_design tool input validation (mocked — no real CATIA)."""

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
    mock.get_active_part_pycatia.return_value = part
    sf = MagicMock()
    part.ShapeFactory = sf
    part.shape_factory = sf
    part.in_work_object = None
    part.update_object = part.update_object
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    body.Sketches.Count = 1
    body.Sketches.Item.return_value.Name = "Sketch.1"
    part.HybridBodies.Count = 1
    part.HybridBodies.Item.return_value.Sketches.Count = 0
    part.CreateReferenceFromObject.return_value = MagicMock()
    mock.get_origin_elements.return_value = {
        "xy": MagicMock(),
        "yz": MagicMock(),
        "zx": MagicMock(),
    }
    mock.hso = MagicMock()
    mock.hso.Count = 1
    mock.hso.Item.return_value.Value = MagicMock()
    mock.refresh_display = MagicMock()
    return mock


@pytest.fixture
def pd_tools(conn_mock):
    from catia_mcp.tools.part_design import PartDesignTools
    return PartDesignTools(conn_mock)


# ── FR-06.1 catia_pad ───────────────────────────────────────────────────

class TestPad:
    def test_pad_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.1"
        part.shape_factory.AddNewPad.return_value = pad_mock
        result = pd_tools.execute("catia_pad", {"height": 20})
        assert "Pad" in result
        assert "20" in result
        part.update_object.assert_called_once()

    def test_pad_symmetric(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.1"
        part.shape_factory.AddNewPad.return_value = pad_mock
        result = pd_tools.execute("catia_pad", {"height": 20, "symmetric": True})
        assert "Pad" in result
        assert pad_mock.IsSymmetric is True

    def test_pad_reverse(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.1"
        part.shape_factory.AddNewPad.return_value = pad_mock
        result = pd_tools.execute("catia_pad", {"height": 20, "direction": "reverse"})
        assert "Pad" in result
        assert pad_mock.DirectionOrientation == 1

    def test_pad_with_sketch_name(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        mock_sketch.Name = "Sketch.2"
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 2
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.2"
        part.shape_factory.AddNewPad.return_value = pad_mock
        result = pd_tools.execute("catia_pad", {"height": 30, "sketch_name": "Sketch.2"})
        assert "Pad" in result

    def test_pad_zero_height_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_pad", {"height": 0})

    def test_pad_negative_height_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_pad", {"height": -5})

    def test_pad_string_height_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_pad", {"height": "abc"})


# ── FR-06.2 catia_pocket ────────────────────────────────────────────────

class TestPocket:
    def test_pocket_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        pocket_mock = MagicMock()
        pocket_mock.Name = "Pocket.1"
        part.shape_factory.AddNewPocket.return_value = pocket_mock
        result = pd_tools.execute("catia_pocket", {"depth": 15})
        assert "Pocket" in result
        assert "15" in result

    def test_pocket_reverse(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        pocket_mock = MagicMock()
        pocket_mock.Name = "Pocket.1"
        part.shape_factory.AddNewPocket.return_value = pocket_mock
        result = pd_tools.execute("catia_pocket", {"depth": 15, "direction": "reverse"})
        assert "Pocket" in result
        assert pocket_mock.DirectionOrientation == 1

    def test_pocket_negative_depth_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_pocket", {"depth": -10})

    def test_pocket_zero_depth_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_pocket", {"depth": 0})


# ── FR-06.3 catia_shaft ─────────────────────────────────────────────────

class TestShaft:
    def test_shaft_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        shaft_mock = MagicMock()
        shaft_mock.Name = "Shaft.1"
        part.shape_factory.AddNewShaft.return_value = shaft_mock
        result = pd_tools.execute("catia_shaft", {})
        assert "Shaft" in result or "revolution" in result.lower()

    def test_shaft_custom_angle(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        shaft_mock = MagicMock()
        shaft_mock.Name = "Shaft.1"
        part.ShapeFactory.AddNewShaft.return_value = shaft_mock
        result = pd_tools.execute("catia_shaft", {"angle": 180})
        assert "Shaft" in result or "revolution" in result.lower()
        # win32com path uses PascalCase
        assert shaft_mock.FirstAngle == 180

    def test_shaft_negative_angle_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_shaft", {"angle": -10})


# ── FR-06.4 catia_groove ────────────────────────────────────────────────

class TestGroove:
    def test_groove_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        groove_mock = MagicMock()
        groove_mock.Name = "Groove.1"
        groove_mock.com_object = groove_mock
        groove_mock.GetDefinition.return_value = groove_mock
        result = pd_tools.execute("catia_groove", {})
        assert "Groove" in result or "revolution" in result.lower()

    def test_groove_custom_angle(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        groove_mock = MagicMock()
        groove_mock.Name = "Groove.1"
        part.ShapeFactory.AddNewGroove.return_value = groove_mock
        result = pd_tools.execute("catia_groove", {"angle": 270})
        assert "Groove" in result or "revolution" in result.lower()
        # dynamic.Dispatch path uses PascalCase attributes
        assert groove_mock.FirstAngle == 270

    def test_groove_negative_angle_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_groove", {"angle": -10})


# ── FR-06.5 catia_fillet ────────────────────────────────────────────────

class TestFillet:
    def test_fillet_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        fillet_mock = MagicMock()
        fillet_mock.Name = "Fillet.1"
        part.shape_factory.AddNewSolidEdgeFilletWithConstantRadius.return_value = fillet_mock
        result = pd_tools.execute("catia_fillet", {"radius": 5})
        assert "Fillet" in result
        assert "5" in result

    def test_fillet_with_edge_name(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        fillet_mock = MagicMock()
        fillet_mock.Name = "Fillet.1"
        part.shape_factory.AddNewSolidEdgeFilletWithConstantRadius.return_value = fillet_mock
        result = pd_tools.execute("catia_fillet", {"radius": 3, "edge_name": "Edge.1"})
        assert "Fillet" in result

    def test_zero_radius_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_fillet", {"radius": 0})

    def test_negative_radius_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_fillet", {"radius": -5})


# ── FR-06.6 catia_chamfer ───────────────────────────────────────────────

class TestChamfer:
    def test_chamfer_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        chamfer_mock = MagicMock()
        chamfer_mock.Name = "Chamfer.1"
        part.shape_factory.AddNewChamfer.return_value = chamfer_mock
        result = pd_tools.execute("catia_chamfer", {"length": 2})
        assert "Chamfer" in result
        assert "2" in result

    def test_chamfer_with_angle(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        chamfer_mock = MagicMock()
        chamfer_mock.Name = "Chamfer.1"
        part.shape_factory.AddNewChamfer.return_value = chamfer_mock
        result = pd_tools.execute("catia_chamfer", {"length": 2, "angle": 60})
        assert "Chamfer" in result

    def test_negative_length_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_chamfer", {"length": -1})

    def test_negative_angle_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_chamfer", {"length": 5, "angle": -45})


# ── FR-06.7 catia_hole ──────────────────────────────────────────────────

class TestHole:
    def test_hole_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        hole_mock = MagicMock()
        hole_mock.Name = "Hole.1"
        part.shape_factory.AddNewHoleFromSketch.return_value = hole_mock
        result = pd_tools.execute("catia_hole", {"diameter": 8, "depth": 20})
        assert "Hole" in result
        assert "8" in result

    def test_hole_threaded(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        hole_mock = MagicMock()
        hole_mock.Name = "Hole.1"
        part.ShapeFactory.AddNewHoleFromSketch.return_value = hole_mock
        result = pd_tools.execute("catia_hole", {"diameter": 8, "depth": 20, "threaded": True})
        assert "Hole" in result
        # win32com path uses PascalCase
        assert hole_mock.ThreadingMode == 1

    def test_hole_zero_diameter_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_hole", {"diameter": 0, "depth": 10})

    def test_hole_negative_depth_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools.execute("catia_hole", {"diameter": 5, "depth": -1})


# ── FR-06.8 catia_rect_pattern ──────────────────────────────────────────

class TestRectPattern:
    def test_rect_pattern_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        pattern_mock = MagicMock()
        pattern_mock.Name = "RectPattern.1"
        part.shape_factory.AddNewRectPattern.return_value = pattern_mock
        result = pd_tools.execute("catia_rect_pattern", {"dir1_count": 3, "dir1_spacing": 15})
        assert "Rectangular pattern" in result or "pattern" in result.lower()

    def test_rect_pattern_2d(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        pattern_mock = MagicMock()
        pattern_mock.Name = "RectPattern.1"
        part.shape_factory.AddNewRectPattern.return_value = pattern_mock
        result = pd_tools.execute("catia_rect_pattern", {"dir1_count": 3, "dir1_spacing": 15, "dir2_count": 2, "dir2_spacing": 10})
        assert "pattern" in result.lower()

    def test_zero_dir1_count(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_rect_pattern", {"dir1_count": 0, "dir1_spacing": 10})

    def test_negative_dir1_count(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_rect_pattern", {"dir1_count": -1, "dir1_spacing": 10})

    def test_zero_spacing(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_rect_pattern", {"dir1_count": 3, "dir1_spacing": 0})


# ── FR-06.9 catia_circ_pattern ──────────────────────────────────────────

class TestCircPattern:
    def test_circ_pattern_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        pattern_mock = MagicMock()
        pattern_mock.Name = "CircPattern.1"
        part.shape_factory.AddNewCircPattern.return_value = pattern_mock
        result = pd_tools.execute("catia_circ_pattern", {"count": 6})
        assert "Circular pattern" in result or "pattern" in result.lower()

    def test_circ_pattern_custom_spacing(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        pattern_mock = MagicMock()
        pattern_mock.Name = "CircPattern.1"
        part.shape_factory.AddNewCircPattern.return_value = pattern_mock
        result = pd_tools.execute("catia_circ_pattern", {"count": 4, "angular_spacing": 90})
        assert "pattern" in result.lower()

    def test_zero_count(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_circ_pattern", {"count": 0})


# ── FR-06.10 catia_mirror ───────────────────────────────────────────────

class TestMirror:
    def test_mirror_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        mirror_mock = MagicMock()
        mirror_mock.Name = "Mirror.1"
        part.shape_factory.AddNewMirror.return_value = mirror_mock
        result = pd_tools.execute("catia_mirror", {"plane": "xy"})
        assert "Mirror" in result

    def test_mirror_invalid_plane(self, pd_tools):
        with pytest.raises(ValueError, match="Must be one of"):
            pd_tools.execute("catia_mirror", {"plane": "front"})


# ── FR-06.11 catia_shell ────────────────────────────────────────────────

class TestShell:
    def test_shell_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        shell_mock = MagicMock()
        shell_mock.Name = "Shell.1"
        part.shape_factory.AddNewShell.return_value = shell_mock
        result = pd_tools.execute("catia_shell", {"thickness": 2})
        assert "Shell" in result
        assert "2" in result

    def test_shell_with_faces_to_remove(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        shell_mock = MagicMock()
        shell_mock.Name = "Shell.1"
        part.shape_factory.AddNewShell.return_value = shell_mock
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        result = pd_tools.execute("catia_shell", {"thickness": 2, "faces_to_remove": ["Face.1"]})
        assert "Shell" in result

    def test_zero_thickness(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools.execute("catia_shell", {"thickness": 0})


# ── FR-06.12 catia_draft ────────────────────────────────────────────────

class TestDraft:
    def test_draft_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        draft_mock = MagicMock()
        draft_mock.Name = "Draft.1"
        part.shape_factory.AddNewDraft.return_value = draft_mock
        result = pd_tools.execute("catia_draft", {"angle": 3})
        assert "Draft" in result

    def test_draft_with_pulling_direction(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        draft_mock = MagicMock()
        draft_mock.Name = "Draft.1"
        part.shape_factory.AddNewDraft.return_value = draft_mock
        result = pd_tools.execute("catia_draft", {"angle": 3, "pulling_direction": "yz"})
        assert "Draft" in result

    def test_negative_angle(self, pd_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            pd_tools.execute("catia_draft", {"angle": -5})


# ── FR-06.13 catia_thickness ────────────────────────────────────────────

class TestThickness:
    def test_thickness_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        body.Shapes.Item.return_value.Name = "Pad.1"
        thickness_mock = MagicMock()
        thickness_mock.Name = "Thickness.1"
        part.shape_factory.AddNewThickness.return_value = thickness_mock
        result = pd_tools.execute("catia_thickness", {"offset": 5})
        assert "Thickness" in result

    def test_negative_offset(self, pd_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            pd_tools.execute("catia_thickness", {"offset": -5})


# ── FR-06.14 catia_list_features ────────────────────────────────────────

class TestListFeatures:
    def test_list_features(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 3
        shapes = []
        for i in range(3):
            s = MagicMock()
            s.Name = f"Feature.{i+1}"
            s.Type = "Pad"
            shapes.append(s)
        body.Shapes.Item.side_effect = lambda i: shapes[i - 1]
        result = pd_tools.execute("catia_list_features", {})
        assert isinstance(result, str)
        assert "Feature.1" in result

    def test_list_features_empty(self, pd_tools, conn_mock):
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 0
        result = pd_tools.execute("catia_list_features", {})
        assert "No feature" in result or "No shape" in result or "feature" in result.lower()


# ── FR-06.15 catia_list_edges ───────────────────────────────────────────

class TestListEdges:
    def test_list_edges(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.1"
        body.Shapes.Item.return_value = pad_mock
        conn_mock.hso.Count = 2
        v1 = MagicMock()
        v1.Name = "Edge.1"
        v2 = MagicMock()
        v2.Name = "Edge.2"
        item1 = MagicMock()
        item1.Value = v1
        item2 = MagicMock()
        item2.Value = v2
        conn_mock.hso.Item.side_effect = lambda i: [item1, item2][i - 1]
        result = pd_tools.execute("catia_list_edges", {})
        assert isinstance(result, str)
        assert "Edge.1" in result

    def test_list_edges_empty(self, pd_tools, conn_mock):
        body = conn_mock.get_active_part_body()
        body.Shapes.Count = 1
        pad_mock = MagicMock()
        pad_mock.Name = "Pad.1"
        body.Shapes.Item.return_value = pad_mock
        conn_mock.hso.Count = 0
        result = pd_tools.execute("catia_list_edges", {})
        assert "No edge" in result or "edge" in result.lower()


# ── FR-06.16 catia_lifting ──────────────────────────────────────────────

class TestLifting:
    def test_lifting_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        lifting_mock = MagicMock()
        lifting_mock.Name = "Lifting.1"
        part.shape_factory.AddNewLifting.return_value = lifting_mock
        result = pd_tools.execute("catia_lifting", {"guiding_curve": "Line.1"})
        assert "Lifting" in result

    def test_lifting_missing_curve_raises(self, pd_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="guiding curve"):
            pd_tools.execute("catia_lifting", {"guiding_curve": "Ghost"})

    def test_lifting_missing_sketch_raises(self, pd_tools, conn_mock):
        body = conn_mock.get_active_part_body()
        body.Sketches.Count = 0
        part = conn_mock.get_active_part()
        part.HybridBodies.Count = 0
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        with pytest.raises(RuntimeError, match="sketch"):
            pd_tools.execute("catia_lifting", {"guiding_curve": "Line.1"})

    def test_lifting_with_support(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        mock_sketch = MagicMock()
        body.Sketches.Item.return_value = mock_sketch
        body.Sketches.Count = 1
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        lifting_mock = MagicMock()
        lifting_mock.Name = "Lifting.1"
        part.shape_factory.AddNewLifting.return_value = lifting_mock
        result = pd_tools.execute("catia_lifting", {"guiding_curve": "Line.1", "support": "Line.2"})
        assert "Lifting" in result


# ── FR-06.17 catia_sweep ────────────────────────────────────────────────

class TestSweep:
    def test_sweep_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        sweep_mock = MagicMock()
        sweep_mock.Name = "Sweep.1"
        part.shape_factory.AddNewVariableSectionShape.return_value = sweep_mock
        result = pd_tools.execute("catia_sweep", {"spine": "Line.1", "section": "Circle.1"})
        assert "Sweep" in result or "sweep" in result.lower()

    def test_sweep_with_profile(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        sweep_mock = MagicMock()
        sweep_mock.Name = "Sweep.1"
        part.shape_factory.AddNewVariableSectionShape.return_value = sweep_mock
        result = pd_tools.execute("catia_sweep", {"spine": "Line.1", "section": "Circle.1", "profile": "Circle.2"})
        assert "Sweep" in result or "sweep" in result.lower()

    def test_sweep_missing_spine_raises(self, pd_tools, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="spine"):
            pd_tools.execute("catia_sweep", {"spine": "Ghost", "section": "Circle.1"})


# ── FR-06.18 catia_loft ─────────────────────────────────────────────────

class TestLoft:
    def test_loft_valid(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        body = conn_mock.get_active_part_body()
        sk1 = MagicMock()
        sk1.Name = "Sketch.1"
        sk2 = MagicMock()
        sk2.Name = "Sketch.2"
        body.Sketches.Count = 2
        body.Sketches.Item.side_effect = lambda i: [sk1, sk2][i - 1]
        loft_mock = MagicMock()
        loft_mock.Name = "Loft.1"
        part.shape_factory.AddNewLoft.return_value = loft_mock
        result = pd_tools.execute("catia_loft", {"sketch_names": ["Sketch.1", "Sketch.2"]})
        assert "Loft" in result

    def test_loft_empty_sketches_raises(self, pd_tools):
        with pytest.raises(RuntimeError, match="sketch|at least 2"):
            pd_tools.execute("catia_loft", {"sketch_names": []})

    def test_loft_single_sketch_raises(self, pd_tools):
        with pytest.raises(RuntimeError, match="sketch|at least 2"):
            pd_tools.execute("catia_loft", {"sketch_names": ["Sketch.1"]})


# ── FR-06.19 catia_boolean ──────────────────────────────────────────────

class TestBoolean:
    def test_boolean_union(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        bool_mock = MagicMock()
        bool_mock.Name = "Boolean.1"
        part.shape_factory.AddOperation.return_value = bool_mock
        result = pd_tools.execute("catia_boolean", {"operation": "union", "body1": "PartBody", "body2": "PartBody.2"})
        assert "Boolean" in result or "boolean" in result.lower() or "Union" in result

    def test_boolean_cut(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        bool_mock = MagicMock()
        bool_mock.Name = "Boolean.1"
        part.shape_factory.AddOperation.return_value = bool_mock
        result = pd_tools.execute("catia_boolean", {"operation": "difference", "body1": "PartBody", "body2": "PartBody.2"})
        assert "Boolean" in result or "boolean" in result.lower() or "difference" in result.lower() or "cut" in result.lower()

    def test_boolean_intersect(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        conn_mock.hso.Count = 1
        conn_mock.hso.Item.return_value.Value = MagicMock()
        bool_mock = MagicMock()
        bool_mock.Name = "Boolean.1"
        part.shape_factory.AddOperation.return_value = bool_mock
        result = pd_tools.execute("catia_boolean", {"operation": "intersection", "body1": "PartBody", "body2": "PartBody.2"})
        assert "Boolean" in result or "boolean" in result.lower() or "intersection" in result.lower()

    def test_boolean_missing_body_raises(self, pd_tools, conn_mock):
        part = conn_mock.get_active_part()
        part.Bodies.Item.side_effect = Exception("not found")
        with pytest.raises(RuntimeError, match="not found"):
            pd_tools.execute("catia_boolean", {"operation": "union", "body1": "Ghost", "body2": "PartBody.2"})


# ── Existing tests (routing & definitions) ────────────────────────────────

class TestPadValidation:
    def test_pad_height_validation(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools._pad({"height": 0})


class TestPocketValidation:
    def test_pocket_negative_depth_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools._pocket({"depth": -10})


class TestShaftValidation:
    def test_shaft_negative_angle_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools._shaft({"angle": -10})


class TestGrooveValidation:
    def test_groove_negative_angle_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools._groove({"angle": -10})


class TestFilletValidation:
    def test_zero_radius_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._fillet({"radius": 0})

    def test_negative_radius_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._fillet({"radius": -5})


class TestChamferValidation:
    def test_negative_length_raises(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._chamfer({"length": -1})


class TestHoleValidation:
    def test_hole_zero_diameter_raises(self, pd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            pd_tools._hole({"diameter": 0, "depth": 10})


class TestRectPatternValidation:
    def test_zero_dir1_count(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._rect_pattern({"dir1_count": 0, "dir1_spacing": 10})


class TestCircPatternValidation:
    def test_zero_count(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._circ_pattern({"count": 0})


class TestMirrorValidation:
    def test_invalid_plane(self, pd_tools):
        with pytest.raises(ValueError, match="Must be one of"):
            pd_tools._mirror({"plane": "front"})


class TestShellValidation:
    def test_zero_thickness(self, pd_tools):
        with pytest.raises(ValueError, match="must be positive"):
            pd_tools._shell({"thickness": 0})


class TestDraftValidation:
    def test_negative_angle(self, pd_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            pd_tools._draft({"angle": -5})


class TestThicknessValidation:
    def test_negative_offset(self, pd_tools):
        with pytest.raises(ValueError, match="must be non-negative"):
            pd_tools._thickness({"offset": -5})


class TestExecuteRouting:
    def test_unknown_tool_raises(self, pd_tools):
        with pytest.raises(ValueError, match="Unknown part design tool"):
            pd_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_all_19_tools_defined(self, pd_tools):
        defs = pd_tools.get_tool_definitions()
        assert len(defs) == 19

    def test_pad_has_required_height(self, pd_tools):
        defs = pd_tools.get_tool_definitions()
        pad = next(d for d in defs if d["name"] == "catia_pad")
        assert "height" in pad["inputSchema"]["required"]
