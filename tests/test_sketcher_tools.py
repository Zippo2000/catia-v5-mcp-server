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
    part = MagicMock()
    mock.get_active_part.return_value = part
    part.OriginElements.PlaneXY = MagicMock()
    part.OriginElements.PlaneYZ = MagicMock()
    part.OriginElements.PlaneZX = MagicMock()
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    body.Sketches.Add.return_value = MagicMock()
    part.CreateReferenceFromObject.return_value = MagicMock()
    mock.hso = MagicMock()
    mock.refresh_display = MagicMock()
    return mock


@pytest.fixture
def sk_tools(conn_mock):
    from catia_mcp.tools.sketcher import SketcherTools
    return SketcherTools(conn_mock)


# ── FR-05.1 catia_create_sketch ─────────────────────────────────────────

class TestCreateSketch:
    def test_create_sketch_xy(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        conn_mock.get_active_part.return_value.CreateReferenceFromObject.return_value = MagicMock()
        body = conn_mock.get_active_part_body()
        body.Sketches.Add.return_value = mock_sketch
        mock_sketch.OpenEdition.return_value = MagicMock()
        result = sk_tools.execute("catia_create_sketch", {"plane": "xy"})
        assert "Sketch created" in result

    def test_create_sketch_yz(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        conn_mock.get_active_part.return_value.CreateReferenceFromObject.return_value = MagicMock()
        body = conn_mock.get_active_part_body()
        body.Sketches.Add.return_value = mock_sketch
        mock_sketch.OpenEdition.return_value = MagicMock()
        result = sk_tools.execute("catia_create_sketch", {"plane": "yz"})
        assert "Sketch created" in result

    def test_create_sketch_zx(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        conn_mock.get_active_part.return_value.CreateReferenceFromObject.return_value = MagicMock()
        body = conn_mock.get_active_part_body()
        body.Sketches.Add.return_value = mock_sketch
        mock_sketch.OpenEdition.return_value = MagicMock()
        result = sk_tools.execute("catia_create_sketch", {"plane": "zx"})
        assert "Sketch created" in result

    def test_create_sketch_plane_name(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        part = conn_mock.get_active_part()
        mock_plane = MagicMock()
        mock_plane.Name = "Plane(xy,90mm)"
        mock_shapes = MagicMock()
        mock_shapes.Count = 1
        mock_shapes.Item.return_value = mock_plane
        mock_hb = MagicMock()
        mock_hb.HybridShapes = mock_shapes
        part.HybridBodies = [mock_hb]
        part.CreateReferenceFromObject.return_value = MagicMock()
        body = conn_mock.get_active_part_body()
        body.Sketches.Add.return_value = mock_sketch
        mock_sketch.OpenEdition.return_value = MagicMock()
        result = sk_tools.execute("catia_create_sketch", {"plane_name": "Plane(xy,90mm)"})
        assert "Plane(xy,90mm)" in result
        part.CreateReferenceFromObject.assert_called_with(mock_plane)

    def test_create_sketch_invalid_plane(self, sk_tools):
        with pytest.raises(ValueError, match="Must be one of"):
            sk_tools.execute("catia_create_sketch", {"plane": "front"})


# ── FR-05.2 catia_close_sketch ──────────────────────────────────────────

class TestCloseSketch:
    def test_close_sketch_valid(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_close_sketch", {})
        assert "Sketch closed" in result
        mock_sketch.CloseEdition.assert_called()
        assert sk_tools._active_sketch is None

    def test_close_sketch_no_active_raises(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_close_sketch", {})


# ── FR-05.3 catia_sketch_line ───────────────────────────────────────────

class TestSketchLine:
    def test_sketch_line_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_line", {"x1": 0, "y1": 0, "x2": 10, "y2": 20})
        assert "Line created" in result
        factory.CreateLine.assert_called_with(0, 0, 10, 20)

    def test_sketch_line_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_line", {"x1": 0, "y1": 0, "x2": 10, "y2": 20})


# ── FR-05.4 catia_sketch_rectangle ──────────────────────────────────────

class TestSketchRectangle:
    def test_rectangle_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_rectangle", {"x1": 0, "y1": 0, "x2": 50, "y2": 30})
        assert "Rectangle created" in result
        assert factory.CreateLine.call_count == 4

    def test_rectangle_centered_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_centered_rectangle", {"cx": 0, "cy": 0, "width": 40, "height": 20})
        assert "Rectangle created" in result

    def test_rectangle_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_rectangle", {"x1": 0, "y1": 0, "x2": 50, "y2": 30})

    def test_rectangle_centered_zero_width_raises(self, sk_tools):
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_centered_rectangle", {"width": 0, "height": 10})

    def test_rectangle_centered_negative_height_raises(self, sk_tools):
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_centered_rectangle", {"width": 10, "height": -5})


# ── FR-05.5 catia_sketch_circle ─────────────────────────────────────────

class TestSketchCircle:
    def test_circle_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_circle", {"cx": 0, "cy": 0, "radius": 25})
        assert "Circle created" in result
        factory.CreateClosedCircle.assert_called_with(0, 0, 25)

    def test_circle_negative_radius_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_circle", {"cx": 0, "cy": 0, "radius": -5})

    def test_circle_zero_radius_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_circle", {"cx": 0, "cy": 0, "radius": 0})

    def test_circle_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_circle", {"radius": 25})


# ── FR-05.6 catia_sketch_spline ─────────────────────────────────────────

class TestSketchSpline:
    def test_spline_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_spline", {"points": [[0, 0], [10, 10], [20, 0]]})
        assert "Spline created" in result

    def test_spline_closed(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_spline", {"points": [[0, 0], [10, 10], [20, 0]], "closed": True})
        assert "Spline created" in result
        assert "closed" in result.lower()

    def test_spline_empty_points_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="at least 2"):
            sk_tools.execute("catia_sketch_spline", {"points": []})

    def test_spline_single_point_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="at least 2"):
            sk_tools.execute("catia_sketch_spline", {"points": [[0, 0]]})

    def test_spline_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_spline", {"points": [[0, 0], [10, 10]]})


# ── FR-05.7 catia_sketch_arc ────────────────────────────────────────────

class TestSketchArc:
    def test_arc_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_arc", {"cx": 0, "cy": 0, "radius": 20, "start_angle": 0, "end_angle": 90})
        assert "Arc created" in result

    def test_arc_negative_radius_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_arc", {"cx": 0, "cy": 0, "radius": -10, "start_angle": 0, "end_angle": 90})

    def test_arc_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_arc", {"cx": 0, "cy": 0, "radius": 20, "start_angle": 0, "end_angle": 90})


# ── FR-05.8 catia_sketch_ellipse ────────────────────────────────────────

class TestSketchEllipse:
    def test_ellipse_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_ellipse", {"cx": 0, "cy": 0, "major_axis": 20, "minor_axis": 10})
        assert "Ellipse created" in result

    def test_ellipse_with_rotation(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_ellipse", {"cx": 0, "cy": 0, "major_axis": 20, "minor_axis": 10, "angle": 30})
        assert "Ellipse created" in result

    def test_ellipse_negative_major_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_ellipse", {"cx": 0, "cy": 0, "major_axis": -10, "minor_axis": 5})

    def test_ellipse_negative_minor_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_ellipse", {"cx": 0, "cy": 0, "major_axis": 10, "minor_axis": -5})

    def test_ellipse_no_active_sketch(self, sk_tools):
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_ellipse", {"cx": 0, "cy": 0, "major_axis": 10, "minor_axis": 5})


# ── FR-05.9 catia_sketch_point ──────────────────────────────────────────

class TestSketchPoint:
    def test_point_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_point", {"x": 10, "y": 20})
        assert "Point created" in result
        factory.CreatePoint.assert_called_with(10, 20)

    def test_point_no_active_sketch(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_point", {"x": 10, "y": 20})


# ── FR-05.10 catia_sketch_constraint ────────────────────────────────────

class TestSketchConstraint:
    def test_constraint_coincidence(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "coincidence", "geometry_index_1": 1, "geometry_index_2": 2})
        assert "coincidence" in result.lower() or "Coincidence" in result

    def test_constraint_distance(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "distance", "value": 50, "geometry_index_1": 1})
        assert "distance" in result.lower() or "Distance" in result

    def test_constraint_distance_two_elements(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "distance", "value": 50, "geometry_index_1": 1, "geometry_index_2": 2})
        assert "distance" in result.lower() or "Distance" in result

    def test_constraint_no_active(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_constraint", {"type": "distance", "value": 50, "geometry_index_1": 1})

    def test_constraint_invalid_type(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="Unknown constraint type"):
            sk_tools.execute("catia_sketch_constraint", {"type": "invalid"})

    def test_constraint_radius(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "radius", "value": 25, "geometry_index_1": 1})
        assert "radius" in result.lower() or "Radius" in result

    def test_constraint_angle(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "angle", "value": 90, "geometry_index_1": 1, "geometry_index_2": 2})
        assert "angle" in result.lower() or "Angle" in result

    def test_constraint_missing_value_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="requires a 'value'"):
            sk_tools.execute("catia_sketch_constraint", {"type": "distance", "geometry_index_1": 1})

    def test_constraint_missing_geometry_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="requires 'geometry_index_1'"):
            sk_tools.execute("catia_sketch_constraint", {"type": "distance", "value": 50})


# ── FR-05.11 catia_sketch_get_geometry ──────────────────────────────────

class TestSketchGetGeometry:
    def test_get_geometry_list(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        mock_sketch.GeometricElements.Count = 2
        elem1 = MagicMock()
        elem1.Name = "Line.1"
        elem1.GeometricType = "Line"
        elem2 = MagicMock()
        elem2.Name = "Circle.1"
        elem2.GeometricType = "Circle"
        mock_sketch.GeometricElements.Item.side_effect = lambda i: [elem1, elem2][i - 1]
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_get_geometry", {})
        assert "Line.1" in result

    def test_get_geometry_empty(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        mock_sketch.GeometricElements.Count = 0
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_get_geometry", {})
        assert "No geometry" in result or "active sketch" in result.lower()

    def test_get_geometry_no_active(self, sk_tools):
        sk_tools._active_sketch = None
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_get_geometry", {})


# ── FR-05.12 catia_sketch_hyperbola ─────────────────────────────────────

class TestSketchHyperbola:
    def test_hyperbola_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_hyperbola", {"cx": 0, "cy": 0, "transverse_axis": 10, "conjugate_axis": 5})
        assert "Hyperbola created" in result

    def test_hyperbola_negative_transverse_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_hyperbola", {"cx": 0, "cy": 0, "transverse_axis": -10, "conjugate_axis": 5})

    def test_hyperbola_negative_conjugate_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_hyperbola", {"cx": 0, "cy": 0, "transverse_axis": 10, "conjugate_axis": -5})

    def test_hyperbola_no_active_sketch(self, sk_tools):
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_hyperbola", {"cx": 0, "cy": 0, "transverse_axis": 10, "conjugate_axis": 5})


# ── FR-05.13 catia_sketch_parabola ──────────────────────────────────────

class TestSketchParabola:
    def test_parabola_valid(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_parabola", {"cx": 0, "cy": 0, "focal_length": 15})
        assert "Parabola created" in result

    def test_parabola_with_rotation(self, sk_tools, conn_mock):
        sk_tools._active_sketch = MagicMock()
        factory = MagicMock()
        sk_tools._active_factory = factory
        result = sk_tools.execute("catia_sketch_parabola", {"cx": 0, "cy": 0, "focal_length": 15, "angle": 45})
        assert "Parabola created" in result

    def test_parabola_zero_focal_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_parabola", {"cx": 0, "cy": 0, "focal_length": 0})

    def test_parabola_negative_focal_raises(self, sk_tools):
        sk_tools._active_sketch = MagicMock()
        sk_tools._active_factory = MagicMock()
        with pytest.raises(ValueError, match="must be positive"):
            sk_tools.execute("catia_sketch_parabola", {"cx": 0, "cy": 0, "focal_length": -5})

    def test_parabola_no_active_sketch(self, sk_tools):
        with pytest.raises(RuntimeError, match="No active sketch"):
            sk_tools.execute("catia_sketch_parabola", {"cx": 0, "cy": 0, "focal_length": 10})


# ── FR-05.14 catia_sketch_horizontal/vertical/fix constraints ────────────

class TestSketchMonoConstraints:
    def test_constraint_horizontal(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "horizontal", "geometry_index_1": 1})
        assert "horizontal" in result.lower() or "Horizontal" in result

    def test_constraint_vertical(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "vertical", "geometry_index_1": 1})
        assert "vertical" in result.lower() or "Vertical" in result

    def test_constraint_fix(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "fix", "geometry_index_1": 1})
        assert "fix" in result.lower() or "Fix" in result

    def test_constraint_tangent(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "tangent", "geometry_index_1": 1, "geometry_index_2": 2})
        assert "tangent" in result.lower() or "Tangent" in result

    def test_constraint_perpendicular(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "perpendicular", "geometry_index_1": 1, "geometry_index_2": 2})
        assert "perpendicular" in result.lower() or "Perpendicular" in result

    def test_constraint_parallel(self, sk_tools, conn_mock):
        mock_sketch = MagicMock()
        sk_tools._active_sketch = mock_sketch
        sk_tools._active_factory = MagicMock()
        result = sk_tools.execute("catia_sketch_constraint", {"type": "parallel", "geometry_index_1": 1, "geometry_index_2": 2})
        assert "parallel" in result.lower() or "Parallel" in result


# ── Existing tests (routing & definitions) ────────────────────────────────

class TestCreateSketchValidation:
    def test_invalid_plane(self, sk_tools):
        with pytest.raises(ValueError, match="Must be one of"):
            sk_tools._create_sketch("front")


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
    def test_all_14_tools_defined(self, sk_tools):
        defs = sk_tools.get_tool_definitions()
        assert len(defs) == 14
