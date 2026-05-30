"""Sketcher tools for CATIA V5.

2D sketch creation and editing: lines, circles, rectangles, arcs, splines, constraints.
All dimensions are in millimeters. CATIA COM API uses millimeters natively.
"""

from __future__ import annotations

import json
from typing import Any

from catia_mcp.connection import CATIAConnection
from catia_mcp.utils import (
    format_catia_error,
    validate_positive_float,
    validate_plane,
)

# Plane name mapping
PLANE_MAP = {
    "xy": "PlaneXY",
    "yz": "PlaneYZ",
    "zx": "PlaneZX",
    "xz": "PlaneZX",  # alias
}


class SketcherTools:
    """Tools for 2D sketch operations in CATIA V5."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection
        self._active_sketch: Any | None = None
        self._active_factory: Any | None = None

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_create_sketch",
                "description": (
                    "Create a new 2D sketch on a reference plane (xy, yz, or zx). "
                    "The sketch is opened for editing. You must close it with catia_close_sketch "
                    "before creating 3D features."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plane": {
                            "type": "string",
                            "description": "Reference plane: 'xy' (front), 'yz' (right), 'zx' (top)",
                            "enum": ["xy", "yz", "zx"],
                            "default": "xy",
                        },
                    },
                },
            },
            {
                "name": "catia_close_sketch",
                "description": (
                    "Close the active sketch and return to Part Design. "
                    "Must be called after finishing sketch geometry before applying 3D features."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "catia_sketch_line",
                "description": (
                    "Draw a line in the active sketch from (x1, y1) to (x2, y2). "
                    "Coordinates in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x1": {"type": "number", "description": "Start X coordinate (mm)"},
                        "y1": {"type": "number", "description": "Start Y coordinate (mm)"},
                        "x2": {"type": "number", "description": "End X coordinate (mm)"},
                        "y2": {"type": "number", "description": "End Y coordinate (mm)"},
                    },
                    "required": ["x1", "y1", "x2", "y2"],
                },
            },
            {
                "name": "catia_sketch_rectangle",
                "description": (
                    "Draw a rectangle in the active sketch defined by two opposite corners. "
                    "Creates 4 lines forming a closed profile. Coordinates in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x1": {"type": "number", "description": "First corner X (mm)"},
                        "y1": {"type": "number", "description": "First corner Y (mm)"},
                        "x2": {"type": "number", "description": "Opposite corner X (mm)"},
                        "y2": {"type": "number", "description": "Opposite corner Y (mm)"},
                    },
                    "required": ["x1", "y1", "x2", "y2"],
                },
            },
            {
                "name": "catia_sketch_centered_rectangle",
                "description": (
                    "Draw a rectangle centered at (cx, cy) with given width and height. "
                    "Coordinates and dimensions in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm)", "default": 0},
                        "cy": {"type": "number", "description": "Center Y (mm)", "default": 0},
                        "width": {"type": "number", "description": "Width in mm"},
                        "height": {"type": "number", "description": "Height in mm"},
                    },
                    "required": ["width", "height"],
                },
            },
            {
                "name": "catia_sketch_circle",
                "description": "Draw a circle in the active sketch. Coordinates and radius in mm.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm)", "default": 0},
                        "cy": {"type": "number", "description": "Center Y (mm)", "default": 0},
                        "radius": {"type": "number", "description": "Radius in mm"},
                    },
                    "required": ["radius"],
                },
            },
            {
                "name": "catia_sketch_arc",
                "description": (
                    "Draw a circular arc defined by center, radius, and start/end angles (degrees). "
                    "Angles are measured counter-clockwise from the positive X axis."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm)"},
                        "cy": {"type": "number", "description": "Center Y (mm)"},
                        "radius": {"type": "number", "description": "Radius (mm)"},
                        "start_angle": {"type": "number", "description": "Start angle (degrees)"},
                        "end_angle": {"type": "number", "description": "End angle (degrees)"},
                    },
                    "required": ["cx", "cy", "radius", "start_angle", "end_angle"],
                },
            },
            {
                "name": "catia_sketch_ellipse",
                "description": (
                    "Draw an ellipse in the active sketch centered at (cx, cy) with "
                    "given major and minor semi-axes. Angle rotates the major axis "
                    "counter-clockwise from the X axis. Dimensions in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm)", "default": 0},
                        "cy": {"type": "number", "description": "Center Y (mm)", "default": 0},
                        "major_axis": {"type": "number", "description": "Half of major axis length (mm)"},
                        "minor_axis": {"type": "number", "description": "Half of minor axis length (mm)"},
                        "angle": {
                            "type": "number",
                            "description": "Rotation angle of major axis counter-clockwise from X (degrees)",
                            "default": 0,
                        },
                    },
                    "required": ["major_axis", "minor_axis"],
                },
            },
            {
                "name": "catia_sketch_hyperbola",
                "description": (
                    "Draw a hyperbola in the active sketch centered at (cx, cy) with "
                    "transverse semi-axis a and conjugate semi-axis b. "
                    "Angle rotates the transverse axis counter-clockwise from X. Dimensions in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Center X (mm)", "default": 0},
                        "cy": {"type": "number", "description": "Center Y (mm)", "default": 0},
                        "transverse_axis": {"type": "number", "description": "Transverse semi-axis a (mm)"},
                        "conjugate_axis": {"type": "number", "description": "Conjugate semi-axis b (mm)"},
                        "angle": {
                            "type": "number",
                            "description": "Rotation angle counter-clockwise from X (degrees)",
                            "default": 0,
                        },
                    },
                    "required": ["transverse_axis", "conjugate_axis"],
                },
            },
            {
                "name": "catia_sketch_parabola",
                "description": (
                    "Draw a parabola in the active sketch with vertex at (cx, cy) and given "
                    "focal length (distance from vertex to focus). "
                    "Angle rotates the parabola counter-clockwise from X. Dimensions in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cx": {"type": "number", "description": "Vertex X (mm)", "default": 0},
                        "cy": {"type": "number", "description": "Vertex Y (mm)", "default": 0},
                        "focal_length": {"type": "number", "description": "Distance from vertex to focus (mm)"},
                        "angle": {
                            "type": "number",
                            "description": "Rotation angle counter-clockwise from X (degrees)",
                            "default": 0,
                        },
                    },
                    "required": ["focal_length"],
                },
            },
            {
                "name": "catia_sketch_spline",
                "description": (
                    "Draw a spline through a list of control points. "
                    "Each point is [x, y] in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "points": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                            },
                            "description": "List of [x, y] control points in mm",
                            "minItems": 2,
                        },
                        "closed": {
                            "type": "boolean",
                            "description": "Whether to close the spline (default: false)",
                            "default": False,
                        },
                    },
                    "required": ["points"],
                },
            },
            {
                "name": "catia_sketch_point",
                "description": "Create a point in the active sketch. Coordinates in mm.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X coordinate (mm)"},
                        "y": {"type": "number", "description": "Y coordinate (mm)"},
                    },
                    "required": ["x", "y"],
                },
            },
            {
                "name": "catia_sketch_constraint",
                "description": (
                    "Add a dimensional constraint to the active sketch. "
                    "Supported types: distance, radius, angle, coincidence, tangent, "
                    "perpendicular, parallel, horizontal, vertical, fix."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Constraint type",
                            "enum": [
                                "distance", "radius", "angle",
                                "coincidence", "tangent", "perpendicular",
                                "parallel", "horizontal", "vertical", "fix",
                            ],
                        },
                        "value": {
                            "type": "number",
                            "description": "Constraint value (mm or degrees). Required for distance, radius, angle.",
                        },
                        "geometry_index_1": {
                            "type": "integer",
                            "description": "Index of first geometry element (1-based, from sketch geometry list)",
                        },
                        "geometry_index_2": {
                            "type": "integer",
                            "description": "Index of second geometry element (for relational constraints)",
                        },
                    },
                    "required": ["type"],
                },
            },
            {
                "name": "catia_sketch_get_geometry",
                "description": "List all geometry elements in the active sketch with their indices and types.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_create_sketch":
                return self._create_sketch(arguments.get("plane", "xy"))
            case "catia_close_sketch":
                return self._close_sketch()
            case "catia_sketch_line":
                return self._draw_line(
                    arguments["x1"], arguments["y1"],
                    arguments["x2"], arguments["y2"],
                )
            case "catia_sketch_rectangle":
                return self._draw_rectangle(
                    arguments["x1"], arguments["y1"],
                    arguments["x2"], arguments["y2"],
                )
            case "catia_sketch_centered_rectangle":
                return self._draw_centered_rectangle(
                    arguments.get("cx", 0), arguments.get("cy", 0),
                    arguments["width"], arguments["height"],
                )
            case "catia_sketch_circle":
                return self._draw_circle(
                    arguments.get("cx", 0), arguments.get("cy", 0),
                    arguments["radius"],
                )
            case "catia_sketch_arc":
                return self._draw_arc(
                    arguments["cx"], arguments["cy"], arguments["radius"],
                    arguments["start_angle"], arguments["end_angle"],
                )
            case "catia_sketch_ellipse":
                return self._draw_ellipse(
                    arguments.get("cx", 0), arguments.get("cy", 0),
                    arguments["major_axis"], arguments["minor_axis"],
                    arguments.get("angle", 0),
                )
            case "catia_sketch_hyperbola":
                return self._draw_hyperbola(
                    arguments.get("cx", 0), arguments.get("cy", 0),
                    arguments["transverse_axis"], arguments["conjugate_axis"],
                    arguments.get("angle", 0),
                )
            case "catia_sketch_parabola":
                return self._draw_parabola(
                    arguments.get("cx", 0), arguments.get("cy", 0),
                    arguments["focal_length"],
                    arguments.get("angle", 0),
                )
            case "catia_sketch_spline":
                return self._draw_spline(
                    arguments["points"], arguments.get("closed", False),
                )
            case "catia_sketch_point":
                return self._draw_point(arguments["x"], arguments["y"])
            case "catia_sketch_constraint":
                return self._add_constraint(arguments)
            case "catia_sketch_get_geometry":
                return self._get_geometry()
            case _:
                raise ValueError(f"Unknown sketcher tool: {tool_name}")

    def _ensure_sketch_open(self) -> None:
        if self._active_sketch is None:
            raise RuntimeError(
                "No active sketch. Use catia_create_sketch first to open a sketch."
            )

    def _create_sketch(self, plane: str = "xy") -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()

        plane_key = validate_plane(plane)

        # Get the reference plane
        origin = part.OriginElements
        plane_attr = PLANE_MAP[plane_key]
        ref_plane = getattr(origin, plane_attr)
        ref = part.CreateReferenceFromObject(ref_plane)

        # Create the sketch on the plane
        sketches = body.Sketches
        try:
            sketch = sketches.Add(ref)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateSketch", e))

        # Open the sketch for editing
        self._active_sketch = sketch
        try:
            self._active_factory = sketch.OpenEdition()
        except Exception as e:
            raise RuntimeError(format_catia_error("OpenSketchEdition", e))

        plane_names = {"xy": "XY (front)", "yz": "YZ (right)", "zx": "ZX (top)"}
        return f"Sketch created on {plane_names.get(plane_key, plane)} plane. Ready for geometry."

    def _close_sketch(self) -> str:
        self._ensure_sketch_open()
        sketch = self._active_sketch
        try:
            sketch.CloseEdition()
        except Exception as e:
            raise RuntimeError(format_catia_error("CloseSketch", e))
        self.conn.get_active_part().Update()
        self._active_sketch = None
        self._active_factory = None
        self.conn.refresh_display()
        return "Sketch closed. You can now apply Part Design features (pad, pocket, etc.)."

    def _draw_line(self, x1: float, y1: float, x2: float, y2: float) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        try:
            line = factory.CreateLine(x1, y1, x2, y2)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateLine", e))
        return f"Line created from ({x1}, {y1}) to ({x2}, {y2}) mm"

    def _draw_rectangle(self, x1: float, y1: float, x2: float, y2: float) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory

        # Create 4 lines forming a closed rectangle
        try:
            factory.CreateLine(x1, y1, x2, y1)  # bottom
            factory.CreateLine(x2, y1, x2, y2)  # right
            factory.CreateLine(x2, y2, x1, y2)  # top
            factory.CreateLine(x1, y2, x1, y1)  # left
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateLine (rectangle)", e))

        return (
            f"Rectangle created from ({x1}, {y1}) to ({x2}, {y2}) mm "
            f"[{abs(x2-x1):.1f} x {abs(y2-y1):.1f} mm]"
        )

    def _draw_centered_rectangle(
        self, cx: float, cy: float, width: float, height: float
    ) -> str:
        validate_positive_float(width, "width")
        validate_positive_float(height, "height")
        hw, hh = width / 2, height / 2
        return self._draw_rectangle(cx - hw, cy - hh, cx + hw, cy + hh)

    def _draw_circle(self, cx: float, cy: float, radius: float) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        validate_positive_float(radius, "radius")
        try:
            factory.CreateClosedCircle(cx, cy, radius)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateClosedCircle", e))
        return f"Circle created at ({cx}, {cy}) with radius {radius} mm"

    def _draw_arc(
        self, cx: float, cy: float, radius: float,
        start_angle: float, end_angle: float,
    ) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        validate_positive_float(radius, "radius")
        import math
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        try:
            factory.CreateArc(cx, cy, radius, start_rad, end_rad)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateArc", e))
        return (
            f"Arc created at ({cx}, {cy}), radius={radius} mm, "
            f"from {start_angle}° to {end_angle}°"
        )

    def _draw_spline(self, points: list[list[float]], closed: bool = False) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory

        if len(points) < 2:
            raise ValueError("Spline requires at least 2 control points.")

        spline_pts = []
        for pt in points:
            ctrl_pt = factory.CreatePoint(pt[0], pt[1])
            spline_pts.append(ctrl_pt)

        try:
            spline = factory.CreateSpline(spline_pts)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateSpline", e))

        if closed and len(points) >= 3:
            try:
                factory.CreateLine(points[-1][0], points[-1][1], points[0][0], points[0][1])
            except Exception as e:
                raise RuntimeError(format_catia_error("CreateLine (close spline)", e))

        pts_str = ", ".join(f"({p[0]}, {p[1]})" for p in points)
        return f"Spline created through {len(points)} points: {pts_str}" + (
            " (closed)" if closed else ""
        )

    def _draw_point(self, x: float, y: float) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        try:
            factory.CreatePoint(x, y)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreatePoint", e))
        return f"Point created at ({x}, {y}) mm"

    def _add_constraint(self, args: dict[str, Any]) -> str:
        self._ensure_sketch_open()
        sketch = self._active_sketch
        constraint_type = args["type"]
        value = args.get("value")
        idx1 = args.get("geometry_index_1")
        idx2 = args.get("geometry_index_2")

        constraints = sketch.Constraints
        geom = sketch.GeometricElements

        # Dimensional constraints (need a geometry reference + value)
        if constraint_type in ("distance", "radius", "angle"):
            if value is None:
                raise ValueError(f"Constraint type '{constraint_type}' requires a 'value' parameter.")
            if idx1 is None:
                raise ValueError(f"Constraint type '{constraint_type}' requires 'geometry_index_1'.")

            ref1 = geom.Item(idx1)

            if constraint_type == "distance" and idx2 is not None:
                ref2 = geom.Item(idx2)
                cst = constraints.AddBiEltCst(0, ref1, ref2)  # catCstTypeDistance = 0
                cst.Dimension.Value = value
            elif constraint_type == "distance":
                cst = constraints.AddMonoEltCst(0, ref1)  # Length constraint
                cst.Dimension.Value = value
            elif constraint_type == "radius":
                cst = constraints.AddMonoEltCst(1, ref1)  # catCstTypeRadius = 1
                cst.Dimension.Value = value
            elif constraint_type == "angle":
                if idx2 is None:
                    raise ValueError("Angle constraint requires 'geometry_index_2'.")
                ref2 = geom.Item(idx2)
                cst = constraints.AddBiEltCst(2, ref1, ref2)  # catCstTypeAngle = 2
                cst.Dimension.Value = value

            return f"{constraint_type.capitalize()} constraint added: {value} {'mm' if constraint_type != 'angle' else '°'}"

        # Geometric constraints (no value needed)
        cst_type_map = {
            "coincidence": 3,   # catCstTypeOn
            "tangent": 4,       # catCstTypeTangent
            "perpendicular": 6, # catCstTypePerpendicular
            "parallel": 7,      # catCstTypeParallel
            "horizontal": 8,    # catCstTypeHorizontality
            "vertical": 9,      # catCstTypeVerticality
            "fix": 10,          # catCstTypeFix
        }

        cst_code = cst_type_map.get(constraint_type)
        if cst_code is None:
            raise ValueError(f"Unknown constraint type: {constraint_type}")

        if constraint_type in ("horizontal", "vertical", "fix"):
            if idx1 is None:
                raise ValueError(f"Constraint '{constraint_type}' requires 'geometry_index_1'.")
            ref1 = geom.Item(idx1)
            constraints.AddMonoEltCst(cst_code, ref1)
        else:
            if idx1 is None or idx2 is None:
                raise ValueError(
                    f"Constraint '{constraint_type}' requires both 'geometry_index_1' and 'geometry_index_2'."
                )
            ref1 = geom.Item(idx1)
            ref2 = geom.Item(idx2)
            constraints.AddBiEltCst(cst_code, ref1, ref2)

        return f"{constraint_type.capitalize()} constraint added"

    def _get_geometry(self) -> str:
        self._ensure_sketch_open()
        sketch = self._active_sketch
        geom = sketch.GeometricElements

        elements = []
        for i in range(1, geom.Count + 1):
            elem = geom.Item(i)
            info = {
                "index": i,
                "name": elem.Name,
            }
            # Try to get the geometry type
            try:
                info["type"] = elem.GeometricType
            except Exception:
                pass
            elements.append(info)

        if not elements:
            return "No geometry elements in the active sketch"
        return json.dumps(elements, indent=2)

    def _draw_ellipse(
        self, cx: float, cy: float, major_axis: float, minor_axis: float, angle: float = 0
    ) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        validate_positive_float(major_axis, "major_axis")
        validate_positive_float(minor_axis, "minor_axis")
        import math
        angle_rad = math.radians(angle)
        try:
            factory.CreateEllipse2(cx, cy, major_axis, minor_axis, angle_rad)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateEllipse2", e))
        return (
            f"Ellipse created at ({cx}, {cy}), "
            f"major_axis={major_axis} mm, minor_axis={minor_axis} mm, "
            f"rotation={angle}°"
        )

    def _draw_hyperbola(
        self, cx: float, cy: float, transverse_axis: float, conjugate_axis: float, angle: float = 0
    ) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        validate_positive_float(transverse_axis, "transverse_axis")
        validate_positive_float(conjugate_axis, "conjugate_axis")
        import math
        angle_rad = math.radians(angle)
        try:
            factory.CreateHyperbola2(cx, cy, transverse_axis, conjugate_axis, angle_rad)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateHyperbola2", e))
        return (
            f"Hyperbola created at ({cx}, {cy}), "
            f"a={transverse_axis} mm, b={conjugate_axis} mm, "
            f"rotation={angle}°"
        )

    def _draw_parabola(
        self, cx: float, cy: float, focal_length: float, angle: float = 0
    ) -> str:
        self._ensure_sketch_open()
        factory = self._active_factory
        validate_positive_float(focal_length, "focal_length")
        import math
        angle_rad = math.radians(angle)
        try:
            factory.CreateParabola2(cx, cy, focal_length, angle_rad)
        except Exception as e:
            raise RuntimeError(format_catia_error("CreateParabola2", e))
        return (
            f"Parabola created at ({cx}, {cy}), "
            f"focal_length={focal_length} mm, rotation={angle}°"
        )
