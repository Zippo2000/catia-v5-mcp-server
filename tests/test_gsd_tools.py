"""Tests for GSD (Wireframe & Surface Design) tools (mocked — no real CATIA)."""

from unittest.mock import MagicMock, patch
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
    part_mock = MagicMock()
    mock.get_active_part.return_value = part_mock

    # HybridShapeFactory
    hsf = MagicMock()
    part_mock.HybridShapeFactory = hsf

    # HybridBodies — mock as a callable collection with .Add()
    hbody = MagicMock()
    hbody.Name = "Geometrical Set.1"
    hbody.HybridShapes = MagicMock()
    hbody.HybridShapes.Count = 0
    hbodies = MagicMock()
    hbodies.__iter__ = MagicMock(return_value=iter([hbody]))
    hbodies.__len__ = MagicMock(return_value=1)
    hbodies.Add.return_value = hbody
    hbodies.Item.return_value = hbody
    part_mock.HybridBodies = hbodies

    # Origin elements
    mock.get_origin_elements.return_value = {
        "xy": MagicMock(),
        "yz": MagicMock(),
        "zx": MagicMock(),
    }

    return mock


@pytest.fixture
def gsd_tools(conn_mock):
    from catia_mcp.tools.gsd import GSDTools

    return GSDTools(conn_mock)


# ── Tool Definitions ──────────────────────────────────────────────────────


class TestToolDefinitions:
    """All 16 GSD tools are registered with correct schemas."""

    def test_16_tools(self, gsd_tools):
        defs = gsd_tools.get_tool_definitions()
        assert len(defs) == 24

    def test_all_tool_names_present(self, gsd_tools):
        names = {d["name"] for d in gsd_tools.get_tool_definitions()}
        expected = {
            # Wireframe
            "catia_create_geometrical_set",
            "catia_create_point_coord",
            "catia_create_line_2points",
            "catia_create_line_point_direction",
            "catia_create_circle_center_radius",
            "catia_create_plane_offset",
            "catia_create_cylinder",
            "catia_list_geometrical_sets",
            # Surface
            "catia_create_plane_3points",
            "catia_create_fill",
            "catia_create_sweep",
            "catia_create_rotational_surface",
            "catia_create_offset_surface",
            "catia_create_join",
            "catia_create_thicken",
            "catia_create_surface_from_contours",
            # Advanced Primitives
            "catia_create_sphere",
            "catia_create_cone",
            "catia_create_torus",
            "catia_create_ruled",
            # Surface Manipulation
            "catia_create_blend",
            "catia_split_surface",
            "catia_extend_surface",
            "catia_trim_surface",
        }
        assert names == expected

    def test_wireframe_tools_have_set_name_option(self, gsd_tools):
        for d in gsd_tools.get_tool_definitions():
            if (
                d["name"].startswith("catia_create_")
                and d["name"] not in
                {"catia_list_geometrical_sets", "catia_create_fill",
                 "catia_create_sweep", "catia_create_rotational_surface",
                 "catia_create_offset_surface", "catia_create_join",
                 "catia_create_thicken", "catia_create_surface_from_contours",
                 "catia_create_geometrical_set", "catia_create_plane_3points"}
            ):
                assert "set_name" in d["inputSchema"]["properties"], (
                    f"{d['name']} should have set_name option"
                )


# ── Wireframe Tools ───────────────────────────────────────────────────────


class TestCreateGeometricalSet:
    def test_create_geometrical_set(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_geometrical_set", {"name": "Construction"})
        assert "Construction" in result
        assert "created" in result.lower() or "Construction" in result

    def test_empty_name_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="non-empty"):
            gsd_tools.execute("catia_create_geometrical_set", {"name": ""})

    def test_non_string_name_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="non-empty|string"):
            gsd_tools.execute("catia_create_geometrical_set", {"name": 123})


class TestCreatePointCoord:
    def test_point_coord_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_point_coord",
            {"x": 0, "y": 10, "z": 20},
        )
        assert "Point" in result
        assert "0" in result and "10" in result and "20" in result

    def test_point_coord_with_set_name(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_point_coord",
            {"x": 5, "y": 10, "z": 15, "set_name": "MySet"},
        )
        assert isinstance(result, str)

    def test_point_coord_non_numeric_raises(self, gsd_tools):
        with pytest.raises((ValueError, RuntimeError)):
            gsd_tools.execute(
                "catia_create_point_coord",
                {"x": "abc", "y": 10, "z": 20},
            )


class TestCreateLine2Points:
    def test_line_2points_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_line_2points",
            {"point1_name": "Point.1", "point2_name": "Point.2"},
        )
        assert isinstance(result, str)
        assert "Line" in result or "line" in result.lower()


class TestCreateLinePointDirection:
    def test_line_pt_dir_axis(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_line_point_direction",
            {"point_name": "Point.1", "direction": "x"},
        )
        assert isinstance(result, str)

    def test_line_pt_dir_plane(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_line_point_direction",
            {"point_name": "Point.1", "direction": "xy"},
        )
        assert isinstance(result, str)

    def test_line_pt_dir_invalid_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="Invalid direction"):
            gsd_tools.execute(
                "catia_create_line_point_direction",
                {"point_name": "Point.1", "direction": "invalid"},
            )


class TestCreateCircle:
    def test_circle_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_circle_center_radius",
            {"center_name": "Point.1", "radius": 50},
        )
        assert isinstance(result, str)

    def test_circle_with_support_plane(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_circle_center_radius",
            {"center_name": "Point.1", "radius": 25, "support_plane": "yz"},
        )
        assert isinstance(result, str)

    def test_circle_negative_radius_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_circle_center_radius",
                {"center_name": "Point.1", "radius": -10},
            )

    def test_circle_zero_radius_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_circle_center_radius",
                {"center_name": "Point.1", "radius": 0},
            )

    def test_circle_invalid_support_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="support_plane"):
            gsd_tools.execute(
                "catia_create_circle_center_radius",
                {"center_name": "Point.1", "radius": 10, "support_plane": "bad"},
            )


class TestCreatePlaneOffset:
    def test_plane_offset_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_plane_offset",
            {"reference_plane": "xy", "offset": 25},
        )
        assert isinstance(result, str)

    def test_plane_offset_negative(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_plane_offset",
            {"reference_plane": "zx", "offset": -10},
        )
        assert isinstance(result, str)

    def test_plane_offset_invalid_ref_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="reference_plane"):
            gsd_tools.execute(
                "catia_create_plane_offset",
                {"reference_plane": "bad", "offset": 10},
            )


class TestCreateCylinder:
    def test_cylinder_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_cylinder",
            {"center_name": "Point.1", "axis": "z", "radius": 20, "height": 100},
        )
        assert isinstance(result, str)

    def test_cylinder_negative_radius_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_cylinder",
                {"center_name": "Point.1", "axis": "z", "radius": -5, "height": 100},
            )

    def test_cylinder_negative_height_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_cylinder",
                {"center_name": "Point.1", "axis": "z", "radius": 20, "height": -50},
            )

    def test_cylinder_invalid_axis_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="Invalid axis"):
            gsd_tools.execute(
                "catia_create_cylinder",
                {"center_name": "Point.1", "axis": "bad", "radius": 20, "height": 100},
            )


class TestListGeometricalSets:
    def test_list_geometrical_sets(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_list_geometrical_sets", {})
        assert isinstance(result, str)
        assert "Geometrical Set" in result or "Geometrical" in result


# ── Surface Tools ─────────────────────────────────────────────────────────


class TestCreatePlane3Points:
    def test_plane_3points_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_plane_3points",
            {
                "point1_name": "Point.1",
                "point2_name": "Point.2",
                "point3_name": "Point.3",
            },
        )
        assert isinstance(result, str)


class TestCreateFill:
    def test_fill_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_fill",
            {"contour_names": ["Circle.1", "Circle.2"]},
        )
        assert isinstance(result, str)

    def test_fill_empty_contours_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="contour"):
            gsd_tools.execute("catia_create_fill", {"contour_names": []})


class TestCreateSweep:
    def test_sweep_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_sweep",
            {"spine_name": "Line.1", "section_name": "Circle.1"},
        )
        assert isinstance(result, str)


class TestCreateRotationalSurface:
    def test_rotational_surface_default_angle(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_rotational_surface",
            {"axis_name": "Axis.1", "profile_name": "Circle.1"},
        )
        assert isinstance(result, str)

    def test_rotational_surface_custom_angle(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_rotational_surface",
            {"axis_name": "Axis.1", "profile_name": "Circle.1", "angle": 180},
        )
        assert isinstance(result, str)

    def test_rotational_surface_negative_angle_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_rotational_surface",
                {"axis_name": "Axis.1", "profile_name": "Circle.1", "angle": -90},
            )


class TestCreateOffsetSurface:
    def test_offset_surface_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_offset_surface",
            {"surface_name": "Sheet.1", "distance": 5},
        )
        assert isinstance(result, str)

    def test_offset_surface_negative(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_offset_surface",
            {"surface_name": "Sheet.1", "distance": -3},
        )
        assert isinstance(result, str)


class TestCreateJoin:
    def test_join_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_join",
            {"surface_names": ["Sheet.1", "Sheet.2"]},
        )
        assert isinstance(result, str)

    def test_join_empty_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="surface"):
            gsd_tools.execute("catia_create_join", {"surface_names": []})


class TestCreateThicken:
    def test_thicken_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_thicken",
            {"surface_name": "Sheet.1", "thickness": 2},
        )
        assert isinstance(result, str)

    def test_thicken_negative_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="positive"):
            gsd_tools.execute(
                "catia_create_thicken",
                {"surface_name": "Sheet.1", "thickness": -1},
            )


class TestCreateSurfaceFromContours:
    def test_surface_from_contours_valid(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_surface_from_contours",
            {"contour_names": ["Circle.1", "Circle.2"]},
        )
        assert isinstance(result, str)

    def test_surface_from_contours_empty_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="contour"):
            gsd_tools.execute(
                "catia_create_surface_from_contours",
                {"contour_names": []},
            )


# ── Advanced Primitives Tests ──────────────────────────────────────────────


class TestCreateSphere:
    def test_create_sphere_full(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_sphere", {
            "cx": 10, "cy": 20, "cz": 30, "radius": 50,
        })
        assert "Sphere created" in result
        assert "50" in result
        part = conn_mock.get_active_part()
        part.HybridShapeFactory.AddNewPointCoord.assert_called_with(10, 20, 30)
        part.HybridShapeFactory.AddNewSphere.assert_called_once()

    def test_create_sphere_partial(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_sphere", {
            "radius": 25,
            "angle_start": 0, "angle_end": 180,
            "lat_start": -45, "lat_end": 45,
        })
        assert "Sphere created" in result
        part = conn_mock.get_active_part()
        call_args = part.HybridShapeFactory.AddNewSphere.call_args
        assert call_args[0][2] == 25  # radius (now 3rd param after point, axis)
        assert call_args[0][4] == 180  # endParallelAngle
        assert call_args[0][5] == -45  # beginMeridianAngle
        assert call_args[0][6] == 45  # endMeridianAngle

    def test_create_sphere_negative_radius_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="must be positive"):
            gsd_tools.execute("catia_create_sphere", {"radius": -5})

    def test_create_sphere_missing_radius_raises(self, gsd_tools, conn_mock):
        with pytest.raises((ValueError, TypeError), match="radius"):
            gsd_tools.execute("catia_create_sphere", {})


class TestCreateCone:
    def test_create_cone_standard(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_cone", {
            "cx": 0, "cy": 0, "cz": 0,
            "base_radius": 30, "height": 100,
        })
        assert "Cone created" in result
        assert "30" in result and "100" in result
        part = conn_mock.get_active_part()
        part.HybridShapeFactory.AddNewRevol.assert_called()

    def test_create_cone_with_top_radius(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_cone", {
            "base_radius": 40, "height": 80, "top_radius": 10, "angle": 270,
        })
        assert "Cone created" in result
        part = conn_mock.get_active_part()
        # Cone now uses AddNewRevol - check it was called
        assert part.HybridShapeFactory.AddNewRevol.call_count >= 1

    def test_create_cone_missing_height_raises(self, gsd_tools, conn_mock):
        with pytest.raises((ValueError, TypeError), match="height"):
            gsd_tools.execute("catia_create_cone", {"base_radius": 20})


class TestCreateTorus:
    def test_create_torus_full(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_torus", {
            "major_radius": 50, "minor_radius": 10,
        })
        assert "Torus created" in result
        assert "50" in result and "10" in result
        part = conn_mock.get_active_part()
        part.HybridShapeFactory.AddNewRevol.assert_called()

    def test_create_torus_partial(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_torus", {
            "major_radius": 60, "minor_radius": 8,
            "angle_start": 0, "angle_end": 180,
        })
        assert "Torus created" in result
        part = conn_mock.get_active_part()
        # Torus now uses AddNewRevol (revolution of circle around axis)
        assert part.HybridShapeFactory.AddNewRevol.call_count >= 1

    def test_create_torus_negative_minor_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="must be positive"):
            gsd_tools.execute("catia_create_torus", {
                "major_radius": 50, "minor_radius": -3,
            })


class TestCreateRuled:
    def test_create_ruled(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_ruled", {
            "profile1": "Line.1", "profile2": "Line.2",
        })
        assert "Ruled surface created" in result
        assert "Line.1" in result and "Line.2" in result
        conn_mock.get_active_part().HybridShapeFactory.AddNewRuled.assert_called_once()

    def test_create_ruled_missing_profile_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="profile1 and profile2"):
            gsd_tools.execute("catia_create_ruled", {"profile1": "Line.1"})


# ── Surface Manipulation Tests ─────────────────────────────────────────────


class TestCreateBlend:
    def test_create_blend(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_create_blend", {
            "edge_or_curve_name": "Edge.1", "radius": 5,
        })
        assert "Blend created" in result
        assert "5" in result
        conn_mock.get_active_part().HybridShapeFactory.AddNewBlend.assert_called_once()

    def test_create_blend_negative_radius_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="must be positive"):
            gsd_tools.execute("catia_create_blend", {
                "edge_or_curve_name": "Edge.1", "radius": -2,
            })

    def test_create_blend_missing_radius_raises(self, gsd_tools, conn_mock):
        with pytest.raises((ValueError, TypeError), match="radius"):
            gsd_tools.execute("catia_create_blend", {"edge_or_curve_name": "Edge.1"})


class TestSplitSurface:
    def test_split_surface(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_split_surface", {
            "surface_name": "Sheet.1", "tool_name": "Plane.1",
        })
        assert "Split created" in result
        conn_mock.get_active_part().HybridShapeFactory.AddNewSplit.assert_called_once()

    def test_split_surface_missing_tool_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="tool"):
            gsd_tools.execute("catia_split_surface", {"surface_name": "Sheet.1"})


class TestExtendSurface:
    def test_extend_surface(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_extend_surface", {
            "surface_name": "Sheet.1", "distance": 20,
        })
        assert "Extend created" in result
        conn_mock.get_active_part().HybridShapeFactory.AddNewExtend.assert_called_once()

    def test_extend_surface_default_distance(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_extend_surface", {
            "surface_name": "Sheet.1",
        })
        assert "Extend created" in result
        part = conn_mock.get_active_part()
        call_args = part.HybridShapeFactory.AddNewExtend.call_args
        assert call_args[0][1] == 10  # default distance

    def test_extend_surface_zero_distance_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="must be positive"):
            gsd_tools.execute("catia_extend_surface", {
                "surface_name": "Sheet.1", "distance": 0,
            })


class TestTrimSurface:
    def test_trim_surface_keep_1(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_trim_surface", {
            "surface_name": "Sheet.1", "tool_name": "Plane.1", "keep_part": 1,
        })
        assert "Trim created" in result
        conn_mock.get_active_part().HybridShapeFactory.AddNewTrim.assert_called_once()

    def test_trim_surface_default_keep_part(self, gsd_tools, conn_mock):
        result = gsd_tools.execute("catia_trim_surface", {
            "surface_name": "Sheet.1", "tool_name": "Plane.1",
        })
        assert "Trim created" in result
        part = conn_mock.get_active_part()
        call_args = part.HybridShapeFactory.AddNewTrim.call_args
        assert call_args[0][2] == 1  # default keep_part

    def test_trim_surface_missing_tool_raises(self, gsd_tools, conn_mock):
        with pytest.raises(ValueError, match="tool"):
            gsd_tools.execute("catia_trim_surface", {"surface_name": "Sheet.1"})


# ── Integration: execute() dispatch ───────────────────────────────────────


class TestExecuteDispatch:
    def test_unknown_tool_raises(self, gsd_tools):
        with pytest.raises(ValueError, match="Unknown GSD tool"):
            gsd_tools.execute("catia_fake_tool", {})

    def test_dispatch_point_coord(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_point_coord",
            {"x": 0, "y": 0, "z": 0},
        )
        assert isinstance(result, str)

    def test_dispatch_fill(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_fill",
            {"contour_names": ["Circle.1"]},
        )
        assert isinstance(result, str)

    def test_dispatch_join(self, gsd_tools, conn_mock):
        result = gsd_tools.execute(
            "catia_create_join",
            {"surface_names": ["Sheet.1"]},
        )
        assert isinstance(result, str)


# ── Helper methods ────────────────────────────────────────────────────────


class TestHelpers:
    def test_get_or_create_set_default(self, gsd_tools, conn_mock):
        part = conn_mock.get_active_part()
        result = gsd_tools._get_or_create_set(part, None)
        assert result is not None

    def test_get_or_create_set_by_name(self, gsd_tools, conn_mock):
        part = conn_mock.get_active_part()
        result = gsd_tools._get_or_create_set(part, "ExistingSet")
        assert result is not None

    def test_ref_standard_plane(self, gsd_tools, conn_mock):
        part = conn_mock.get_active_part()
        ref = gsd_tools._ref(part, "xy")
        assert ref is not None

    def test_ref_standard_axis(self, gsd_tools, conn_mock):
        part = conn_mock.get_active_part()
        ref = gsd_tools._ref(part, "z")
        assert ref is not None


# ── Ensure CATIA connection ───────────────────────────────────────────────


class TestConnection:
    def test_ensure_connected_called(self, gsd_tools, conn_mock):
        gsd_tools.execute("catia_create_point_coord", {"x": 0, "y": 0, "z": 0})
        assert conn_mock.ensure_connected.called

    def test_disconnected_raises(self):
        mock = MagicMock()
        mock.is_connected = False
        mock.ensure_connected.side_effect = RuntimeError("CATIA not connected")
        from catia_mcp.tools.gsd import GSDTools

        tools = GSDTools(mock)
        with pytest.raises(RuntimeError, match="CATIA not connected"):
            tools.execute("catia_create_point_coord", {"x": 0, "y": 0, "z": 0})
