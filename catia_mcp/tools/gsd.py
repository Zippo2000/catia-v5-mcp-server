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
            case _:
                raise ValueError(f"Unknown GSD tool: {tool_name}")

    # ── Helpers ────────────────────────────────────────────────────────────

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
        """Search all HybridBodies for a HybridShape by name."""
        for hb in part.HybridBodies:
            try:
                for i in range(1, hb.HybridShapes.Count + 1):
                    obj = hb.HybridShapes.Item(i)
                    if obj.Name == name:
                        return obj
            except Exception:
                pass
        return None

    def _ref(self, part: Any, name: str) -> Any:
        """Create a Reference from a geometry name or standard element."""
        import win32com.client

        # Standard planes and axes
        plane_map = {"xy": "xy_plane", "yz": "yz_plane", "zx": "zx_plane"}
        axis_map = {"x": "x_axis", "y": "y_axis", "z": "z_axis"}
        lookup = name.lower().strip()

        if lookup in plane_map:
            return part.CreateReferenceFromName(plane_map[lookup])
        if lookup in axis_map:
            return part.CreateReferenceFromName(axis_map[lookup])

        # Search HybridShapes
        obj = self._find_shape(part, name)
        if obj:
            return part.CreateReferenceFromObject(obj)

        # Fallback: try name as-is
        return part.CreateReferenceFromName(name)

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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
        line = hsf.AddNewLine2Points(pt1, pt2)

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

        if direction in ("xy", "yz", "zx"):
            dir_ref = part.CreateReferenceFromName(f"{direction}_plane")
        else:
            dir_ref = part.CreateReferenceFromName(f"{direction}_axis")

        hsf = part.HybridShapeFactory
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

        plane_ref = part.CreateReferenceFromName(f"{support}_plane")
        hsf = part.HybridShapeFactory
        circle = hsf.AddNewCircle(center, radius, plane_ref)

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

        ref_plane = part.CreateReferenceFromName(f"{ref}_plane")
        hsf = part.HybridShapeFactory
        plane = hsf.AddNewPlaneOffset(ref_plane, offset)

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

        hsf = part.HybridShapeFactory
        cylinder = hsf.AddNewCylinder(center, axis, radius, height)

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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
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

        hsf = part.HybridShapeFactory
        try:
            surf = hsf.AddNewMultiSectionSurf(refs)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewMultiSectionSurf", e))

        hbody = self._get_or_create_set(part, args.get("set_name"))
        name = self._append_and_update(part, hbody, surf)
        return f"Multi-section surface created from {len(contour_names)} contour(s). Name: '{name}'"
