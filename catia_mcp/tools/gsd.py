"""GSD (Wireframe & Surface Design) tools for CATIA V5.

Wireframe: Geometrical Set, Point, Line, Circle, Plane, Cylinder, List
Surface: Plane 3Points, Fill, Sweep, Rotational Surface, Offset, Join,
        Thicken, Multi-Section Surface.

All geometry is created in HybridBodies (Geometrical Sets) via
HybridShapeFactory.
"""

from __future__ import annotations

import logging
from typing import Any

from catia_mcp.connection import CATIAConnection
from catia_mcp.utils import (
    format_catia_error,
    validate_non_negative_float,
    validate_positive_float,
)

logger = logging.getLogger("catia_mcp.gsd")


# ── GSD Tools ───────────────────────────────────────────────────────────────

class GSDTools:
    """GSD (Wireframe & Surface Design) tools for CATIA V5."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            # ── Wireframe ──────────────────────────────────────────────────
            {
                "name": "catia_create_geometrical_set",
                "description": (
                    "Create a new Geometrical Set (HybridBody) in the active Part. "
                    "Geometrical Sets are containers for wireframe and surface geometry."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the new Geometrical Set.",
                        },
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "catia_create_point_coord",
                "description": (
                    "Create a point by coordinates (x, y, z in mm). "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X coordinate (mm)."},
                        "y": {"type": "number", "description": "Y coordinate (mm)."},
                        "z": {"type": "number", "description": "Z coordinate (mm)."},
                        "set_name": {
                            "type": "string",
                            "description": (
                                "Target Geometrical Set name. "
                                "Defaults to the first Geometrical Set."
                            ),
                        },
                    },
                    "required": ["x", "y", "z"],
                },
            },
            {
                "name": "catia_create_line_2points",
                "description": (
                    "Create a line defined by two named points. "
                    "Point names are those created by catia_create_point_coord."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "point1_name": {
                            "type": "string",
                            "description": "Name of the first point (e.g. 'Point(0,10,20)').",
                        },
                        "point2_name": {
                            "type": "string",
                            "description": "Name of the second point.",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["point1_name", "point2_name"],
                },
            },
            {
                "name": "catia_create_line_point_direction",
                "description": (
                    "Create a line through a named point along a standard axis or plane normal. "
                    "Directions: x, y, z, xy, yz, zx."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "point_name": {
                            "type": "string",
                            "description": "Name of the point.",
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["x", "y", "z", "xy", "yz", "zx"],
                            "description": (
                                "Direction: axis (x/y/z) or plane (xy/yz/zx)."
                            ),
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["point_name", "direction"],
                },
            },
            {
                "name": "catia_create_circle_center_radius",
                "description": (
                    "Create a circle defined by a center point and radius (mm). "
                    "The circle is drawn on a support plane (default: xy)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "center_name": {
                            "type": "string",
                            "description": "Name of the center point.",
                        },
                        "radius": {"type": "number", "description": "Radius in mm (must be positive)."},
                        "support_plane": {
                            "type": "string",
                            "enum": ["xy", "yz", "zx"],
                            "description": "Support plane (default: xy).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["center_name", "radius"],
                },
            },
            {
                "name": "catia_create_plane_offset",
                "description": (
                    "Create a plane parallel to a reference plane (xy/yz/zx) at a given offset (mm)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reference_plane": {
                            "type": "string",
                            "enum": ["xy", "yz", "zx"],
                            "description": "Reference plane.",
                        },
                        "offset": {"type": "number", "description": "Offset distance in mm."},
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["reference_plane", "offset"],
                },
            },
            {
                "name": "catia_create_cylinder",
                "description": (
                    "Create an infinite cylinder (for wireframe operations) defined by "
                    "a center point, axis direction, radius, and height."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "center_name": {
                            "type": "string",
                            "description": "Name of the center point.",
                        },
                        "axis": {
                            "type": "string",
                            "enum": ["x", "y", "z", "xy", "yz", "zx"],
                            "description": "Axis direction.",
                        },
                        "radius": {"type": "number", "description": "Cylinder radius in mm."},
                        "height": {"type": "number", "description": "Cylinder height in mm."},
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["center_name", "axis", "radius", "height"],
                },
            },
            {
                "name": "catia_list_geometrical_sets",
                "description": (
                    "List all Geometrical Sets (HybridBodies) in the active Part, "
                    "including the number of shapes in each."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            # ── Surface ────────────────────────────────────────────────────
            {
                "name": "catia_create_plane_3points",
                "description": (
                    "Create a plane defined by three named points."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "point1_name": {
                            "type": "string",
                            "description": "Name of the first point.",
                        },
                        "point2_name": {
                            "type": "string",
                            "description": "Name of the second point.",
                        },
                        "point3_name": {
                            "type": "string",
                            "description": "Name of the third point.",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["point1_name", "point2_name", "point3_name"],
                },
            },
            {
                "name": "catia_create_fill",
                "description": (
                    "Create a fill surface bounded by one or more contour curves. "
                    "Contours can be circles, lines, or splines."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contour_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of the contour curves (e.g. ['Circle.1', 'Circle.2']).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["contour_names"],
                },
            },
            {
                "name": "catia_create_sweep",
                "description": (
                    "Create a swept surface by moving a profile/section along a spine curve."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spine_name": {
                            "type": "string",
                            "description": "Name of the spine curve (path).",
                        },
                        "section_name": {
                            "type": "string",
                            "description": "Name of the profile/section (e.g. a circle).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["spine_name", "section_name"],
                },
            },
            {
                "name": "catia_create_rotational_surface",
                "description": (
                    "Create a rotational surface by revolving a profile around an axis. "
                    "Default angle is 360° (full revolution)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "axis_name": {
                            "type": "string",
                            "description": "Name of the rotation axis.",
                        },
                        "profile_name": {
                            "type": "string",
                            "description": "Name of the profile curve.",
                        },
                        "angle": {
                            "type": "number",
                            "description": "Angle in degrees (default: 360).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["axis_name", "profile_name"],
                },
            },
            {
                "name": "catia_create_offset_surface",
                "description": (
                    "Create an offset surface at a given distance from an existing surface. "
                    "Negative distance offsets to the reverse side."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_name": {
                            "type": "string",
                            "description": "Name of the source surface.",
                        },
                        "distance": {
                            "type": "number",
                            "description": "Offset distance in mm (can be negative).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["surface_name", "distance"],
                },
            },
            {
                "name": "catia_create_join",
                "description": (
                    "Join multiple surfaces into a single connected element."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of the surfaces to join.",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["surface_names"],
                },
            },
            {
                "name": "catia_create_thicken",
                "description": (
                    "Thicken a surface into a solid shell with a given thickness (mm)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_name": {
                            "type": "string",
                            "description": "Name of the surface to thicken.",
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness in mm (must be positive).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["surface_name", "thickness"],
                },
            },
            {
                "name": "catia_create_surface_from_contours",
                "description": (
                    "Create a multi-section surface (loft) spanning multiple contour profiles. "
                    "Useful for creating smooth transitional surfaces between cross-sections."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contour_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of the contour profiles (circles, splines, etc.).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name.",
                        },
                    },
                    "required": ["contour_names"],
                },
            },
            {
                "name": "catia_create_sphere",
                "description": (
                    "Create a sphere surface (full or partial) in the active Part. "
                    "The sphere can be a complete sphere (360°) or a partial spherical patch. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm), default 0."},
                        "cy": {"type": "number", "description": "Center Y (mm), default 0."},
                        "cz": {"type": "number", "description": "Center Z (mm), default 0."},
                        "radius": {
                            "type": "number",
                            "description": "Sphere radius in mm (required, > 0).",
                        },
                        "angle_start": {
                            "type": "number",
                            "description": "Start angle in degrees (default 0).",
                        },
                        "angle_end": {
                            "type": "number",
                            "description": "End angle in degrees (default 360 = full sphere).",
                        },
                        "lat_start": {
                            "type": "number",
                            "description": "Latitude start in degrees (default -90 = south pole).",
                        },
                        "lat_end": {
                            "type": "number",
                            "description": "Latitude end in degrees (default 90 = north pole).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["radius"],
                },
            },
            {
                "name": "catia_create_cone",
                "description": (
                    "Create a cone surface in the active Part. "
                    "Define by center point, radius at base, height, and optional top radius. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm), default 0."},
                        "cy": {"type": "number", "description": "Center Y (mm), default 0."},
                        "cz": {"type": "number", "description": "Center Z (mm), default 0."},
                        "base_radius": {
                            "type": "number",
                            "description": "Base radius in mm (required, > 0).",
                        },
                        "height": {
                            "type": "number",
                            "description": "Cone height in mm (required, > 0).",
                        },
                        "top_radius": {
                            "type": "number",
                            "description": "Top radius in mm (default 0 = sharp cone tip).",
                        },
                        "angle": {
                            "type": "number",
                            "description": "Sweep angle in degrees (default 360 = full cone).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["base_radius", "height"],
                },
            },
            {
                "name": "catia_create_torus",
                "description": (
                    "Create a torus (ring) surface in the active Part. "
                    "Define by center, major radius (ring), and minor radius (tube). "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm), default 0."},
                        "cy": {"type": "number", "description": "Center Y (mm), default 0."},
                        "cz": {"type": "number", "description": "Center Z (mm), default 0."},
                        "major_radius": {
                            "type": "number",
                            "description": "Major radius (ring) in mm (required, > 0).",
                        },
                        "minor_radius": {
                            "type": "number",
                            "description": "Minor radius (tube) in mm (required, > 0).",
                        },
                        "angle_start": {
                            "type": "number",
                            "description": "Start angle in degrees (default 0).",
                        },
                        "angle_end": {
                            "type": "number",
                            "description": "End angle in degrees (default 360 = full torus).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["major_radius", "minor_radius"],
                },
            },
            {
                "name": "catia_create_ruled",
                "description": (
                    "Create a ruled surface between two curves or edges. "
                    "A ruled surface is a flat/developable surface connecting two profiles. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "profile1": {
                            "type": "string",
                            "description": "Name of first curve/edge profile.",
                        },
                        "profile2": {
                            "type": "string",
                            "description": "Name of second curve/edge profile.",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["profile1", "profile2"],
                },
            },
            # ── Surface Manipulation ───────────────────────────────────────
            {
                "name": "catia_create_blend",
                "description": (
                    "Create a blend (fillet) on a surface or edge with the specified radius. "
                    "Smoothly transitions between connected surfaces. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "edge_or_curve_name": {
                            "type": "string",
                            "description": "Name of the edge or curve to blend on.",
                        },
                        "radius": {
                            "type": "number",
                            "description": "Blend/fillet radius in mm (must be > 0).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["edge_or_curve_name", "radius"],
                },
            },
            {
                "name": "catia_split_surface",
                "description": (
                    "Split a surface using a cutting element (plane, curve, or another surface). "
                    "The tool returns the split fragments as new surface elements. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_name": {
                            "type": "string",
                            "description": "Name of the surface to split.",
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the cutting element (plane, curve, surface).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["surface_name", "tool_name"],
                },
            },
            {
                "name": "catia_extend_surface",
                "description": (
                    "Extend a surface beyond its current boundary. "
                    "Use distance or target element to define the extension. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_name": {
                            "type": "string",
                            "description": "Name of the surface to extend.",
                        },
                        "distance": {
                            "type": "number",
                            "description": "Extension distance in mm (default 10).",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["surface_name"],
                },
            },
            {
                "name": "catia_trim_surface",
                "description": (
                    "Trim a surface using a cutting element (plane, curve, or surface). "
                    "Keep either the first or second part of the trimmed surface. "
                    "Optionally specify a target Geometrical Set."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "surface_name": {
                            "type": "string",
                            "description": "Name of the surface to trim.",
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the cutting element (plane, curve, surface).",
                        },
                        "keep_part": {
                            "type": "integer",
                            "description": "Which part to keep: 1 (first) or 2 (second). Default 1.",
                        },
                        "set_name": {
                            "type": "string",
                            "description": "Target Geometrical Set name. Defaults to first set.",
                        },
                    },
                    "required": ["surface_name", "tool_name"],
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_create_geometrical_set":
                return self._create_geometrical_set(arguments)
            case "catia_create_point_coord":
                return self._create_point_coord(arguments)
            case "catia_create_line_2points":
                return self._create_line_2points(arguments)
            case "catia_create_line_point_direction":
                return self._create_line_point_direction(arguments)
            case "catia_create_circle_center_radius":
                return self._create_circle(arguments)
            case "catia_create_plane_offset":
                return self._create_plane_offset(arguments)
            case "catia_create_cylinder":
                return self._create_cylinder(arguments)
            case "catia_list_geometrical_sets":
                return self._list_geometrical_sets()
            case "catia_create_plane_3points":
                return self._create_plane_3points(arguments)
            case "catia_create_fill":
                return self._create_fill(arguments)
            case "catia_create_sweep":
                return self._create_sweep(arguments)
            case "catia_create_rotational_surface":
                return self._create_rotational_surface(arguments)
            case "catia_create_offset_surface":
                return self._create_offset_surface(arguments)
            case "catia_create_join":
                return self._create_join(arguments)
            case "catia_create_thicken":
                return self._create_thicken(arguments)
            case "catia_create_surface_from_contours":
                return self._create_surface_from_contours(arguments)
            case "catia_create_sphere":
                return self._create_sphere(arguments)
            case "catia_create_cone":
                return self._create_cone(arguments)
            case "catia_create_torus":
                return self._create_torus(arguments)
            case "catia_create_ruled":
                return self._create_ruled(arguments)
            case "catia_create_blend":
                return self._create_blend(arguments)
            case "catia_split_surface":
                return self._split_surface(arguments)
            case "catia_extend_surface":
                return self._extend_surface(arguments)
            case "catia_trim_surface":
                return self._trim_surface(arguments)
            case _:
                raise ValueError(f"Unknown GSD tool: {tool_name}")

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _hsf(part: Any) -> Any:
        """Get HybridShapeFactory via late binding on the Part object."""
        try:
            import win32com.client.dynamic
            dp = win32com.client.dynamic.Dispatch(part)
            return dp.HybridShapeFactory
        except ImportError:
            return part.HybridShapeFactory
        except Exception:
            return part.HybridShapeFactory

    @staticmethod
    def _dpart(part: Any) -> Any:
        """Get late-bound wrapper for the Part, avoiding gencache proxy issues."""
        try:
            import win32com.client.dynamic
            return win32com.client.dynamic.Dispatch(part)
        except (ImportError, Exception):
            return part

    @staticmethod
    def _ref_geom(dpart: Any, obj: Any) -> Any:
        """Create Reference from a HybridShape using late binding."""
        return dpart.CreateReferenceFromGeometry(obj)

    @staticmethod
    def _ref_obj(dpart: Any, obj: Any) -> Any:
        """Create Reference from an AnyObject using late binding."""
        return dpart.CreateReferenceFromObject(obj)

    def _get_or_create_set(self, part: Any, set_name: str | None) -> Any:
        """Return an existing HybridBody by name, or create one."""
        import win32com.client

        if not set_name:
            # Use first non-default HybridBody, fallback to Geometrical Set.1
            for hb in part.HybridBodies:
                if hb.Name != "Facturing":
                    return win32com.client.dynamic.Dispatch(hb)
            return win32com.client.dynamic.Dispatch(
                part.HybridBodies.Item("Geometrical Set.1")
            )

        # Find existing
        for hb in part.HybridBodies:
            if hb.Name == set_name:
                return win32com.client.dynamic.Dispatch(hb)

        # Create new
        hbody = part.HybridBodies.Add()
        hbody.Name = set_name
        return win32com.client.dynamic.Dispatch(hbody)

    def _find_shape(self, part: Any, name: str) -> Any | None:
        """Search all HybridBodies for a HybridShape by name.

        NOTE: Uses part.HybridBodies directly (gencache proxy).
        In tests with dynamic.Dispatch mocks, this still works because
        the mock's __iter__ is configured. On Windows with real COM,
        gencache proxies expose HybridBodies as iterable.
        """
        try:
            for hb in part.HybridBodies:
                try:
                    for i in range(1, hb.HybridShapes.Count + 1):
                        obj = hb.HybridShapes.Item(i)
                        if obj.Name == name:
                            return obj
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _ref(self, part: Any, name: str) -> Any:
        """Create a Reference from a geometry name or standard element.

        Uses dynamic.Dispatch(part) for all COM calls to avoid gencache proxy
        issues with OriginElements and CreateReferenceFromObject/Geometry.

        See scripting4v5.com 'When to use CreateReference':
        - CreateReferenceFromObject: for AnyObject (OriginElements.PlaneXY, etc.)
        - CreateReferenceFromGeometry: for HybridShape objects (points, lines, circles)
        - CreateReferenceFromName: for string path labels (internal CATIA format)
        """
        import win32com.client
        dpart = win32com.client.dynamic.Dispatch(part)

        # Standard planes and axes via OriginElements
        plane_map = {"xy": "PlaneXY", "yz": "PlaneYZ", "zx": "PlaneZX"}
        axis_map = {"x": "XAxis", "y": "YAxis", "z": "ZAxis"}
        lookup = name.lower().strip()

        if lookup in plane_map or lookup in axis_map:
            key = plane_map.get(lookup, axis_map.get(lookup))
            try:
                oe = dpart.OriginElements
                elem = getattr(oe, key)
                return dpart.CreateReferenceFromObject(elem)
            except Exception as e:
                raise RuntimeError(
                    f"Cannot reference '{name}': Failed to access OriginElements.{key}: {e}"
                ) from e

        # Search HybridShapes — use gencache 'part' for iteration (works),
        # but 'dpart' for CreateReferenceFromGeometry (required for late binding)
        obj = self._find_shape(part, name)
        if obj:
            return dpart.CreateReferenceFromGeometry(obj)

        # Last resort: CreateReferenceFromName for legacy geometry references
        # This works on Windows for geometry path labels and returns a mock in tests
        try:
            return dpart.CreateReferenceFromName(name)
        except Exception:
            raise RuntimeError(
                f"Cannot find geometry '{name}' in any HybridBody and "
                "CreateReferenceFromName also failed. "
                "Make sure the geometry was created in the current part."
            ) from None

    def _append_and_update(
        self, part: Any, hbody: Any, shape: Any, custom_name: str | None = None
    ) -> str:
        """Append a shape to a HybridBody, optionally rename, and update."""
        hbody.AppendHybridShape(shape)
        if custom_name:
            shape.Name = custom_name
        part.Update()
        return shape.Name

    # ── Wireframe tools ────────────────────────────────────────────────────

    def _create_geometrical_set(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        name = args["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'name' must be a non-empty string")

        hbody = part.HybridBodies.Add()
        hbody.Name = name
        part.Update()
        return f"Geometrical Set '{name}' created."

    def _create_point_coord(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        x = float(args["x"])
        y = float(args["y"])
        z = float(args["z"])
        set_name = args.get("set_name")

        hsf = self._hsf(part)
        point = hsf.AddNewPointCoord(x, y, z)

        hbody = self._get_or_create_set(part, set_name)
        name = self._append_and_update(part, hbody, point, f"Point({x},{y},{z})")
        return f"Point created at ({x}, {y}, {z}). Name: '{name}'"

    def _create_line_2points(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        pt1 = self._ref(part, args["point1_name"])
        pt2 = self._ref(part, args["point2_name"])
        set_name = args.get("set_name")

        hsf = self._hsf(part)
        line = hsf.AddNewLinePtPt(pt1, pt2)

        hbody = self._get_or_create_set(part, set_name)
        name = self._append_and_update(
            part, hbody, line,
            f"Line({args['point1_name']},{args['point2_name']})",
        )
        return f"Line created between '{args['point1_name']}' and '{args['point2_name']}'. Name: '{name}'"

    def _create_line_point_direction(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        pt = self._ref(part, args["point_name"])
        direction = args["direction"].lower().strip()

        if direction not in ("x", "y", "z", "xy", "yz", "zx"):
            raise ValueError(
                f"Invalid direction '{direction}'. Must be one of: x, y, z, xy, yz, zx"
            )

        dir_ref = self._ref(part, direction)

        hsf = self._hsf(part)
        line = hsf.AddNewLinePtDir(pt, dir_ref)

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(
            part, hbody, line,
            f"Line({args['point_name']},{direction})",
        )
        return f"Line created through '{args['point_name']}' along {direction}. Name: '{name}'"

    def _create_circle(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        center = self._ref(part, args["center_name"])
        radius = validate_positive_float(args["radius"], "radius")
        support = args.get("support_plane", "xy").lower().strip()

        if support not in ("xy", "yz", "zx"):
            raise ValueError(
                f"Invalid support_plane '{support}'. Must be one of: xy, yz, zx"
            )

        plane_ref = self._ref(part, support)
        hsf = self._hsf(part)
        circle = hsf.AddNewCircleCtrRad(center, plane_ref, False, radius)

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(
            part, hbody, circle,
            f"Circle({args['center_name']},{radius}mm)",
        )
        return f"Circle created at '{args['center_name']}' with radius {radius}mm on {support}. Name: '{name}'"

    def _create_plane_offset(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        ref = args["reference_plane"].lower().strip()
        if ref not in ("xy", "yz", "zx"):
            raise ValueError(
                f"Invalid reference_plane '{ref}'. Must be one of: xy, yz, zx"
            )
        offset = float(args["offset"])

        ref_plane = self._ref(part, ref)
        hsf = self._hsf(part)
        plane = hsf.AddNewPlaneOffset(ref_plane, offset, True)

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(
            part, hbody, plane,
            f"Plane({ref},{offset}mm)",
        )
        return f"Offset plane created from {ref} with offset {offset}mm. Name: '{name}'"

    def _create_cylinder(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        center = self._ref(part, args["center_name"])
        axis = args["axis"].lower().strip()
        radius = validate_positive_float(args["radius"], "radius")
        height = validate_positive_float(args["height"], "height")

        if axis not in ("x", "y", "z", "xy", "yz", "zx"):
            raise ValueError(
                f"Invalid axis '{axis}'. Must be one of: x, y, z, xy, yz, zx"
            )

        hsf = self._hsf(part)
        # AddNewCylinder(center, radius, firstLen, secondLen, iDirection)
        # iDirection must be a HybridShapeDirection, not a Reference
        # Created via AddNewDirection(axis_ref) per catiadoc
        axis_name = args.get("axis", "z").lower().strip()
        axis_ref = self._ref(part, axis_name)
        direction = hsf.AddNewDirection(axis_ref)
        half_h = height / 2.0
        cylinder = hsf.AddNewCylinder(center, radius, -half_h, half_h, direction)

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(
            part, hbody, cylinder,
            f"Cylinder({args['center_name']},{axis},{radius}mm)",
        )
        return f"Cylinder created with radius {radius}mm, height {height}mm. Name: '{name}'"

    def _list_geometrical_sets(self) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        sets = []
        for hb in part.HybridBodies:
            count = 0
            try:
                count = len(hb.HybridShapes)
            except Exception:
                count = hb.HybridShapes.Count if hasattr(hb, "HybridShapes") else 0
            sets.append({"name": hb.Name, "shape_count": count})

        result = ", ".join(f"{s['name']} ({s['shape_count']} shapes)" for s in sets)
        return f"Geometrical Sets ({len(sets)}): {result}"

    # ── Surface tools ──────────────────────────────────────────────────────

    def _create_plane_3points(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        pt1 = self._ref(part, args["point1_name"])
        pt2 = self._ref(part, args["point2_name"])
        pt3 = self._ref(part, args["point3_name"])

        hsf = self._hsf(part)
        try:
            plane = hsf.AddNewPlane3Points(pt1, pt2, pt3)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewPlane3Points", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, plane)
        return f"Plane (3 points) created. Name: '{name}'"

    def _create_fill(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        contour_names = args["contour_names"]
        if not contour_names:
            raise ValueError("At least one contour is required for Fill")

        refs = [self._ref(part, name) for name in contour_names]

        hsf = self._hsf(part)
        try:
            fill = hsf.AddNewFill(refs)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewFill", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, fill)
        return f"Fill surface created from {len(contour_names)} contour(s). Name: '{name}'"

    def _create_sweep(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        spine = self._ref(part, args["spine_name"])
        section = self._ref(part, args["section_name"])

        hsf = self._hsf(part)
        try:
            sweep = hsf.AddNewSweptSurface(spine, section)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewSweptSurface", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, sweep)
        return f"Swept surface created along '{args['spine_name']}' with section '{args['section_name']}'. Name: '{name}'"

    def _create_rotational_surface(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        axis = self._ref(part, args["axis_name"])
        profile = self._ref(part, args["profile_name"])
        angle = validate_positive_float(args.get("angle", 360), "angle")

        # CATIA expects radians
        angle_rad = angle * 3.141592653589793 / 180

        hsf = self._hsf(part)
        try:
            rotsurf = hsf.AddNewRotationalSurface(axis, profile, angle_rad)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewRotationalSurface", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, rotsurf)
        return f"Rotational surface created around '{args['axis_name']}' with angle {angle}°. Name: '{name}'"

    def _create_offset_surface(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface = self._ref(part, args["surface_name"])
        distance = float(args["distance"])

        hsf = self._hsf(part)
        try:
            offset_surf = hsf.AddNewOffset(surface, distance)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewOffset", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, offset_surf)
        return f"Offset surface created from '{args['surface_name']}' at {distance}mm. Name: '{name}'"

    def _create_join(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface_names = args["surface_names"]
        if not surface_names:
            raise ValueError("At least one surface is required for Join")

        refs = [self._ref(part, name) for name in surface_names]

        hsf = self._hsf(part)
        try:
            join = hsf.AddNewJoin(refs)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewJoin", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, join)
        return f"Join created from {len(surface_names)} surface(s). Name: '{name}'"

    def _create_thicken(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface = self._ref(part, args["surface_name"])
        thickness = validate_positive_float(args["thickness"], "thickness")

        hsf = self._hsf(part)
        try:
            thick = hsf.AddNewThicken(surface, thickness)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewThicken", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, thick)
        return f"Thicken created from '{args['surface_name']}' with thickness {thickness}mm. Name: '{name}'"

    def _create_surface_from_contours(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        contour_names = args["contour_names"]
        if not contour_names:
            raise ValueError("At least one contour is required")

        refs = [self._ref(part, name) for name in contour_names]

        hsf = self._hsf(part)
        try:
            surf = hsf.AddNewMultiSectionSurf(refs)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewMultiSectionSurf", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, surf)
        return f"Multi-section surface created from {len(contour_names)} contour(s). Name: '{name}'"

    # ── Advanced Primitives ────────────────────────────────────────────────

    def _create_sphere(self, args: dict[str, Any]) -> str:
        """Create a sphere surface (full or partial)."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        cx = float(args.get("cx", 0))
        cy = float(args.get("cy", 0))
        cz = float(args.get("cz", 0))
        radius = validate_positive_float(args.get("radius"), "radius")

        angle_start = float(args.get("angle_start", 0))
        angle_end = float(args.get("angle_end", 360))
        lat_start = float(args.get("lat_start", -90))
        lat_end = float(args.get("lat_end", 90))

        hsf = self._hsf(part)
        dpart = self._dpart(part)
        point = hsf.AddNewPointCoord(cx, cy, cz)

        dpart = self._dpart(part)
        # AddNewSphere: when axis is not needed (full sphere), pass None
        try:
            sphere = hsf.AddNewSphere(
                self._ref_geom(dpart, point),
                None,  # axis not needed for full sphere
                radius,
                angle_start,
                angle_end,
                lat_start,
                lat_end,
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewSphere", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, sphere, f"Sphere({cx},{cy},{cz},{radius}mm)")
        return f"Sphere created: center=({cx},{cy},{cz}), radius={radius}mm, angle=({angle_start}°-{angle_end}°), lat=({lat_start}°-{lat_end}°). Name: '{name}'"

    def _create_cone(self, args: dict[str, Any]) -> str:
        """Create a cone surface via AddNewRevol (AddNewConePointRadius does not exist in CATIA API).
        
        Creates a cone by revolving a line profile around the Z axis.
        """
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        cx = float(args.get("cx", 0))
        cy = float(args.get("cy", 0))
        cz = float(args.get("cz", 0))
        base_radius = validate_positive_float(args.get("base_radius"), "base_radius")
        height = validate_positive_float(args.get("height"), "height")

        top_radius = float(args.get("top_radius", 0))
        angle = float(args.get("angle", 360))

        hsf = self._hsf(part)
        dpart = self._dpart(part)
        point_base = hsf.AddNewPointCoord(cx + base_radius, cy, cz)
        point_top = hsf.AddNewPointCoord(cx + top_radius, cy, cz + height)
        profile = hsf.AddNewLinePtPt(
            self._ref_geom(dpart, point_base),
            self._ref_geom(dpart, point_top),
        )
        center_pt = hsf.AddNewPointCoord(cx, cy, cz)
        center_top = hsf.AddNewPointCoord(cx, cy, cz + height)
        axis_line = hsf.AddNewLinePtPt(
            self._ref_geom(dpart, center_pt),
            self._ref_geom(dpart, center_top),
        )
        try:
            cone = hsf.AddNewRevol(
                self._ref_geom(dpart, profile),
                0.0,
                float(angle),
                self._ref_geom(dpart, axis_line),
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewRevol", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, cone, f"Cone({cx},{cy},{cz},{base_radius}mm,{height}mm)")
        return f"Cone created (via revolution): base={base_radius}mm, top={top_radius}mm, height={height}mm, angle={angle}°. Name: '{name}'"

    def _create_torus(self, args: dict[str, Any]) -> str:
        """Create a torus (ring) surface via AddNewRevol (AddNewTorusPointRadius does not exist in CATIA API).
        
        Creates a torus by revolving a circle around an axis parallel to Z.
        The axis passes through (cx, cy) and the circle is centered at (cx+major, cy, cz).
        """
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        cx = float(args.get("cx", 0))
        cy = float(args.get("cy", 0))
        cz = float(args.get("cz", 0))
        major_radius = validate_positive_float(args.get("major_radius"), "major_radius")
        minor_radius = validate_positive_float(args.get("minor_radius"), "minor_radius")

        angle_start = float(args.get("angle_start", 0))
        angle_end = float(args.get("angle_end", 360))

        hsf = self._hsf(part)
        dpart = self._dpart(part)
        # Create circle for the torus profile
        circle_center = hsf.AddNewPointCoord(cx + major_radius, cy, cz)
        plane_ref = self._ref(part, "xy")
        circle = hsf.AddNewCircleCtrRad(self._ref_geom(self._dpart(part), circle_center),
                                         plane_ref, False, minor_radius)
        axis_bottom = hsf.AddNewPointCoord(cx, cy, cz - 20)
        axis_top = hsf.AddNewPointCoord(cx, cy, cz + 20)
        axis_line = hsf.AddNewLinePtPt(self._ref_geom(self._dpart(part), axis_bottom),
                                        self._ref_geom(self._dpart(part), axis_top))
        try:
            torus = hsf.AddNewRevol(
                self._ref_geom(self._dpart(part), circle),
                float(angle_start),
                float(angle_end),
                self._ref_geom(self._dpart(part), axis_line),
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewRevol", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        try:
            name = self._append_and_update(part, hbody, torus, f"Torus({cx},{cy},{cz},{major_radius}mm,{minor_radius}mm)")
        except Exception as e:
            # If the torus fails to update, try appending without auto-update
            hbody.AppendHybridShape(torus)
            name = f"Torus({cx},{cy},{cz},{major_radius}mm,{minor_radius}mm)"
        return f"Torus created (via revolution): major={major_radius}mm, minor={minor_radius}mm, angle=({angle_start}°-{angle_end}°). Name: '{name}'"

    def _create_ruled(self, args: dict[str, Any]) -> str:
        """Create a ruled surface between two curves/edges."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        profile1_name = args.get("profile1")
        profile2_name = args.get("profile2")
        if not profile1_name or not profile2_name:
            raise ValueError("profile1 and profile2 are required")

        ref1 = self._ref(part, profile1_name)
        ref2 = self._ref(part, profile2_name)

        hsf = self._hsf(part)
        try:
            ruled = hsf.AddNewRuled(ref1, ref2)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewRuled", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, ruled, f"Ruled({profile1_name},{profile2_name})")
        return f"Ruled surface created between '{profile1_name}' and '{profile2_name}'. Name: '{name}'"

    # ── Surface Manipulation ───────────────────────────────────────────────

    def _create_blend(self, args: dict[str, Any]) -> str:
        """Create a blend (fillet) on a surface/edge."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        edge_name = args.get("edge_or_curve_name")
        radius = validate_positive_float(args.get("radius"), "radius")
        if not edge_name:
            raise ValueError("edge_or_curve_name is required")

        edge_ref = self._ref(part, edge_name)
        hsf = self._hsf(part)
        try:
            blend = hsf.AddNewBlend(edge_ref, radius)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewBlend", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, blend, f"Blend({edge_name},{radius}mm)")
        return f"Blend created on '{edge_name}' with radius {radius}mm. Name: '{name}'"

    def _split_surface(self, args: dict[str, Any]) -> str:
        """Split a surface using a cutting element."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface_name = args.get("surface_name")
        tool_name = args.get("tool_name")
        if not surface_name or not tool_name:
            raise ValueError("surface_name and tool_name are required")

        surface_ref = self._ref(part, surface_name)
        tool_ref = self._ref(part, tool_name)
        hsf = self._hsf(part)
        try:
            split = hsf.AddNewSplit(surface_ref, tool_ref)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewSplit", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, split, f"Split({surface_name},{tool_name})")
        return f"Split created on '{surface_name}' with '{tool_name}'. Name: '{name}'"

    def _extend_surface(self, args: dict[str, Any]) -> str:
        """Extend a surface beyond its current boundary."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface_name = args.get("surface_name")
        distance = args.get("distance", 10)
        if not surface_name:
            raise ValueError("surface_name is required")
        validate_positive_float(distance, "distance")

        surface_ref = self._ref(part, surface_name)
        hsf = self._hsf(part)
        try:
            extend = hsf.AddNewExtend(surface_ref, float(distance))
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewExtend", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, extend, f"Extend({surface_name},{distance}mm)")
        return f"Extend created on '{surface_name}' by {distance}mm. Name: '{name}'"

    def _trim_surface(self, args: dict[str, Any]) -> str:
        """Trim a surface using a cutting element."""
        self.conn.ensure_connected()
        part = self.conn.get_active_part()

        surface_name = args.get("surface_name")
        tool_name = args.get("tool_name")
        keep_part = int(args.get("keep_part", 1))
        if not surface_name or not tool_name:
            raise ValueError("surface_name and tool_name are required")

        surface_ref = self._ref(part, surface_name)
        tool_ref = self._ref(part, tool_name)
        hsf = self._hsf(part)
        try:
            trim = hsf.AddNewTrim(surface_ref, tool_ref, keep_part)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewTrim", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, trim, f"Trim({surface_name},{tool_name},P{keep_part})")
        return f"Trim created on '{surface_name}' with '{tool_name}', keep_part={keep_part}. Name: '{name}'"
