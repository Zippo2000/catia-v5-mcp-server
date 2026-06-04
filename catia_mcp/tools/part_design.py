"""Part Design tools for CATIA V5.

3D feature creation: Pad, Pocket, Fillet, Chamfer, Shaft, Groove, Hole,
RectPattern, CircPattern, Mirror, Rib, Slot, Shell, Thickness, Draft,
Lifting, Sweep, Loft, Boolean.
"""

from __future__ import annotations

import json
from typing import Any

from catia_mcp.connection import HAS_PYCATIA
from catia_mcp.utils import (
    format_catia_error,
    validate_non_negative_float,
    validate_positive_float,
    validate_positive_int,
    validate_plane,
    validate_sketch_name,
)


class PartDesignTools:
    """Tools for 3D Part Design features in CATIA V5."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_pad",
                "description": (
                    "Create a Pad (extrusion) from the last sketch. "
                    "Extrudes a 2D profile into a 3D solid along the normal to the sketch plane."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "height": {
                            "type": "number",
                            "description": "Extrusion height/depth in mm",
                        },
                        "direction": {
                            "type": "string",
                            "description": "Extrusion direction: 'normal' (default), 'reverse', 'both'",
                            "enum": ["normal", "reverse", "both"],
                            "default": "normal",
                        },
                        "symmetric": {
                            "type": "boolean",
                            "description": "If true, extrude equally on both sides (total = height)",
                            "default": False,
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": "Name of sketch to use. If not specified, uses the last created sketch.",
                        },
                    },
                    "required": ["height"],
                },
            },
            {
                "name": "catia_pocket",
                "description": (
                    "Create a Pocket (cut extrusion) from the last sketch. "
                    "Removes material by extruding a 2D profile inward."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "depth": {
                            "type": "number",
                            "description": "Cut depth in mm",
                        },
                        "direction": {
                            "type": "string",
                            "description": "Cut direction: 'normal' (default), 'reverse'",
                            "enum": ["normal", "reverse"],
                            "default": "normal",
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": "Name of sketch to use. If not specified, uses the last sketch.",
                        },
                    },
                    "required": ["depth"],
                },
            },
            {
                "name": "catia_shaft",
                "description": (
                    "Create a Shaft (revolution) from the last sketch. "
                    "Revolves a 2D profile around an axis to create a solid of revolution. "
                    "The sketch must contain a line to use as the revolution axis."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "angle": {
                            "type": "number",
                            "description": "Revolution angle in degrees (default: 360 for full revolution)",
                            "default": 360,
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": "Name of sketch to use.",
                        },
                    },
                },
            },
            {
                "name": "catia_groove",
                "description": (
                    "Create a Groove (revolution cut). "
                    "Removes material by revolving a 2D profile around an axis."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "angle": {
                            "type": "number",
                            "description": "Revolution angle in degrees (default: 360)",
                            "default": 360,
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": "Name of sketch to use.",
                        },
                    },
                },
            },
            {
                "name": "catia_fillet",
                "description": (
                    "Add a fillet (rounded edge) to one or more edges of the current solid. "
                    "Specify the radius and the edge names or feature to fillet."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "radius": {
                            "type": "number",
                            "description": "Fillet radius in mm",
                        },
                        "edge_name": {
                            "type": "string",
                            "description": (
                                "Name of the edge to fillet (e.g., 'Edge.1'). "
                                "Use catia_list_edges to find edge names."
                            ),
                        },
                    },
                    "required": ["radius"],
                },
            },
            {
                "name": "catia_chamfer",
                "description": "Add a chamfer (beveled edge) to an edge of the current solid.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "length": {
                            "type": "number",
                            "description": "Chamfer length in mm",
                        },
                        "angle": {
                            "type": "number",
                            "description": "Chamfer angle in degrees (default: 45)",
                            "default": 45,
                        },
                        "edge_name": {
                            "type": "string",
                            "description": "Name of the edge to chamfer",
                        },
                    },
                    "required": ["length"],
                },
            },
            {
                "name": "catia_hole",
                "description": (
                    "Create a Hole feature at a point in the active sketch. "
                    "Supports simple, tapered, counterbored, and countersunk holes."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "diameter": {
                            "type": "number",
                            "description": "Hole diameter in mm",
                        },
                        "depth": {
                            "type": "number",
                            "description": "Hole depth in mm",
                        },
                        "type": {
                            "type": "string",
                            "description": "Hole type: 'simple', 'counterbored', 'countersunk', 'tapered'",
                            "enum": ["simple", "counterbored", "countersunk", "tapered"],
                            "default": "simple",
                        },
                        "threaded": {
                            "type": "boolean",
                            "description": "Whether to add threading (default: false)",
                            "default": False,
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": "Sketch containing the hole center point",
                        },
                    },
                    "required": ["diameter", "depth"],
                },
            },
            {
                "name": "catia_rect_pattern",
                "description": (
                    "Create a Rectangular Pattern of the last feature. "
                    "Duplicates a feature in a grid along two directions."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dir1_count": {
                            "type": "integer",
                            "description": "Number of instances in first direction",
                        },
                        "dir1_spacing": {
                            "type": "number",
                            "description": "Spacing in first direction (mm)",
                        },
                        "dir2_count": {
                            "type": "integer",
                            "description": "Number of instances in second direction (default: 1)",
                            "default": 1,
                        },
                        "dir2_spacing": {
                            "type": "number",
                            "description": "Spacing in second direction (mm)",
                            "default": 0,
                        },
                        "feature_name": {
                            "type": "string",
                            "description": "Name of the feature to pattern. Defaults to last feature.",
                        },
                    },
                    "required": ["dir1_count", "dir1_spacing"],
                },
            },
            {
                "name": "catia_circ_pattern",
                "description": (
                    "Create a Circular Pattern of the last feature. "
                    "Duplicates a feature around a central axis."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of instances around the circle",
                        },
                        "angular_spacing": {
                            "type": "number",
                            "description": "Angular spacing in degrees (default: equal spacing = 360/count)",
                        },
                        "feature_name": {
                            "type": "string",
                            "description": "Feature to pattern. Defaults to last feature.",
                        },
                    },
                    "required": ["count"],
                },
            },
            {
                "name": "catia_mirror",
                "description": (
                    "Mirror a feature or body about a plane. "
                    "Creates a symmetric copy of the geometry."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plane": {
                            "type": "string",
                            "description": "Mirror plane: 'xy', 'yz', or 'zx'",
                            "enum": ["xy", "yz", "zx"],
                        },
                        "feature_name": {
                            "type": "string",
                            "description": "Feature to mirror. Defaults to last feature.",
                        },
                    },
                    "required": ["plane"],
                },
            },
            {
                "name": "catia_shell",
                "description": (
                    "Create a Shell feature: hollows out a solid leaving walls of specified thickness. "
                    "Optionally remove faces to create openings."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "thickness": {
                            "type": "number",
                            "description": "Wall thickness in mm",
                        },
                        "faces_to_remove": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of faces to remove (create openings). E.g., ['Face.1']",
                        },
                    },
                    "required": ["thickness"],
                },
            },
            {
                "name": "catia_draft",
                "description": (
                    "Add a Draft Angle to faces for mold-release purposes. "
                    "Tapers faces by a given angle relative to a pulling direction."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "angle": {
                            "type": "number",
                            "description": "Draft angle in degrees",
                        },
                        "face_name": {
                            "type": "string",
                            "description": "Name of the face to draft",
                        },
                        "pulling_direction": {
                            "type": "string",
                            "description": "Pulling direction plane: 'xy', 'yz', 'zx'",
                            "enum": ["xy", "yz", "zx"],
                            "default": "xy",
                        },
                    },
                    "required": ["angle"],
                },
            },
            {
                "name": "catia_thickness",
                "description": (
                    "Add or remove thickness from faces of a solid. "
                    "Offsets faces inward or outward."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "offset": {
                            "type": "number",
                            "description": "Thickness offset in mm (positive = outward, negative = inward)",
                        },
                        "face_name": {
                            "type": "string",
                            "description": "Name of the face to offset",
                        },
                    },
                    "required": ["offset"],
                },
            },
            {
                "name": "catia_lifting",
                "description": (
                    "Create a Lifting (variable-thickness extrusion). "
                    "Extrudes a sketch profile along a guiding curve with variable thickness. "
                    "The sketch must be perpendicular to the guiding curve at the start point. "
                    "Use this for curved extrusions with varying thickness (e.g., bent pipes, variable flanges)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "guiding_curve": {
                            "type": "string",
                            "description": (
                                "Name of the guiding curve/edge (e.g., 'Edge.1', 'Line.1'). "
                                "The sketch profile is extruded along this curve. "
                                "Use catia_list_edges or catia_list_features to find curve names."
                            ),
                        },
                        "sketch_name": {
                            "type": "string",
                            "description": (
                                "Name of the cross-section sketch. If not specified, uses the last created sketch. "
                                "The sketch must be open (not closed) and perpendicular to the curve at its start."
                            ),
                        },
                        "support": {
                            "type": "string",
                            "description": (
                                "Optional name of a support curve/edge for thickness control. "
                                "If provided, the distance from the support defines the variable thickness."
                            ),
                        },
                    },
                    "required": ["guiding_curve"],
                },
            },
            {
                "name": "catia_sweep",
                "description": (
                    "Create a Variable Section Sweep (VSS). "
                    "Generates a 3D solid by sweeping a profile along a spine curve. "
                    "Optionally a second profile (end section) and a direction curve can be provided "
                    "for controlled sweep orientation."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "spine": {
                            "type": "string",
                            "description": (
                                "Name of the spine/guide curve (e.g., 'Edge.1', 'Line.1'). "
                                "The sweep follows this curve."
                            ),
                        },
                        "section": {
                            "type": "string",
                            "description": (
                                "Name of the start cross-section sketch or curve. "
                                "If a sketch name is provided, it will be used as the profile."
                            ),
                        },
                        "profile": {
                            "type": "string",
                            "description": (
                                "Optional name of the end cross-section sketch or curve. "
                                "If omitted, the start section is used along the entire spine (constant section)."
                            ),
                        },
                        "direction": {
                            "type": "string",
                            "description": (
                                "Optional name of a direction curve/edge that controls the "
                                "profile orientation during sweep (normal to spine)."
                            ),
                        },
                    },
                    "required": ["spine", "section"],
                },
            },
            {
                "name": "catia_loft",
                "description": (
                    "Create a Loft feature from multiple sketches. "
                    "Generates a smooth 3D surface/solid between 2 or more profile sketches. "
                    "Sketches should be on parallel planes or different levels. "
                    "The feature interpolates between all provided sketches."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sketch_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Ordered list of sketch names to loft through. "
                                "Minimum 2 sketches required. "
                                "Example: ['Sketch.1', 'Sketch.2'] or ['Sketch.1', 'Sketch.2', 'Sketch.3']"
                            ),
                        },
                    },
                    "required": ["sketch_names"],
                },
            },
            {
                "name": "catia_boolean",
                "description": (
                    "Perform a Boolean operation between two PartBodies. "
                    "Supported operations: 'union' (merge), 'intersection' (common volume only), "
                    "'difference' (subtract body2 from body1). "
                    "Both bodies must exist in the same Part document."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "Boolean operation type",
                            "enum": ["union", "intersection", "difference"],
                        },
                        "body1": {
                            "type": "string",
                            "description": "Name of the first body (target/result body)",
                        },
                        "body2": {
                            "type": "string",
                            "description": "Name of the second body (tool body)",
                        },
                    },
                    "required": ["operation", "body1", "body2"],
                },
            },
            {
                "name": "catia_list_features",
                "description": "List all features in the active Part Body with their names and types.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "catia_list_edges",
                "description": "List all edges of the active solid body with their names for use with fillet/chamfer.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_pad":
                return self._pad(arguments)
            case "catia_pocket":
                return self._pocket(arguments)
            case "catia_shaft":
                return self._shaft(arguments)
            case "catia_groove":
                return self._groove(arguments)
            case "catia_fillet":
                return self._fillet(arguments)
            case "catia_chamfer":
                return self._chamfer(arguments)
            case "catia_hole":
                return self._hole(arguments)
            case "catia_rect_pattern":
                return self._rect_pattern(arguments)
            case "catia_circ_pattern":
                return self._circ_pattern(arguments)
            case "catia_mirror":
                return self._mirror(arguments)
            case "catia_shell":
                return self._shell(arguments)
            case "catia_draft":
                return self._draft(arguments)
            case "catia_thickness":
                return self._thickness(arguments)
            case "catia_lifting":
                return self._lifting(arguments)
            case "catia_sweep":
                return self._sweep(arguments)
            case "catia_loft":
                return self._loft(arguments)
            case "catia_boolean":
                return self._boolean(arguments)
            case "catia_list_features":
                return self._list_features()
            case "catia_list_edges":
                return self._list_edges()
            case _:
                raise ValueError(f"Unknown part design tool: {tool_name}")

    def _get_last_sketch(self, sketch_name: str | None = None, part: Any | None = None) -> Any:
        """Get a sketch by name or the last sketch available.

        Searches in this order:
        1. PartBody.Sketches  (normal case)
        2. Part.HybridBodies  (Geometrical Sets — fallback when sketch was
           created while a GeoSet was in-edit instead of the PartBody)

        Uses doc.Part directly to avoid stale cached Part references.
        """
        if part is None:
            part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()

        def _find_sketch_in_collection(sketches: Any, name: str) -> Any | None:
            for i in range(1, sketches.Count + 1):
                try:
                    if sketches.Item(i).Name == name:
                        return sketches.Item(i)
                except Exception:
                    pass
            return None

        def _last_sketch_in_collection(sketches: Any) -> Any | None:
            if sketches.Count > 0:
                return sketches.Item(sketches.Count)
            return None

        # --- 1. Try PartBody first ---
        body_sketches = body.Sketches
        if sketch_name:
            found = _find_sketch_in_collection(body_sketches, sketch_name)
            if found:
                return found
        else:
            last = _last_sketch_in_collection(body_sketches)
            if last:
                return last

        # --- 2. Fallback: search all Geometrical Sets (HybridBodies) ---
        last_sketch = None
        try:
            hybrid_bodies = part.HybridBodies
            for i in range(1, hybrid_bodies.Count + 1):
                hb = hybrid_bodies.Item(i)
                try:
                    if sketch_name:
                        found = _find_sketch_in_collection(hb.Sketches, sketch_name)
                        if found:
                            return found
                    else:
                        hb_last = _last_sketch_in_collection(hb.Sketches)
                        if hb_last:
                            last_sketch = hb_last
                except Exception:
                    pass
        except Exception:
            pass

        if last_sketch is not None:
            return last_sketch

        if sketch_name:
            raise RuntimeError(
                f"Sketch '{sketch_name}' not found in PartBody or any Geometrical Set. "
                "Make sure the sketch exists and is closed."
            )
        raise RuntimeError(
            "No sketches found in the active PartBody or any Geometrical Set. "
            "Create a sketch first."
        )

    def _get_last_shape(self, feature_name: str | None = None) -> Any:
        """Get a shape/feature by name or the last one in the body."""
        body = self.conn.get_active_part_body()
        shapes = body.Shapes

        if feature_name:
            return shapes.Item(feature_name)

        if shapes.Count == 0:
            raise RuntimeError("No features found in the active body.")
        return shapes.Item(shapes.Count)

    def _resolve_geometry(self, name: str) -> Any:
        """Resolve a geometry name to a CATIA object.

        Searches in this order:
        1. Body.Shapes (features, edges within shapes)
        2. Body.Sketches
        3. Part.Bodies (for body names)
        4. Origin elements (planes, axes, lines)
        5. HybridBodies (geometrical sets)
        """
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()

        # 1. Try body shapes (features)
        try:
            shapes = body.Shapes
            for i in range(1, shapes.Count + 1):
                if shapes.Item(i).Name == name:
                    return shapes.Item(i)
        except Exception:
            pass

        # 2. Try body sketches
        try:
            sketches = body.Sketches
            for i in range(1, sketches.Count + 1):
                if sketches.Item(i).Name == name:
                    return sketches.Item(i)
        except Exception:
            pass

        # 3. Try bodies
        try:
            bodies = part.Bodies
            for i in range(1, bodies.Count + 1):
                if bodies.Item(i).Name == name:
                    return bodies.Item(i)
        except Exception:
            pass

        # 4. Try origin elements (planes, axes)
        try:
            origin_elements = self.conn.get_origin_elements()
            for key, elem in origin_elements.items():
                if elem.Name == name or key == name.lower():
                    return elem
        except Exception:
            pass

        # 5. Try HybridBodies (geometrical sets)
        try:
            hybrid_bodies = part.HybridBodies
            for i in range(1, hybrid_bodies.Count + 1):
                hb = hybrid_bodies.Item(i)
                try:
                    shapes = hb.HybridShapes
                    for j in range(1, shapes.Count + 1):
                        if shapes.Item(j).Name == name:
                            return shapes.Item(j)
                except Exception:
                    pass
                # Also check if the HB itself matches
                if hb.Name == name:
                    return hb
        except Exception:
            pass

        # 6. Try Search on the part (fallback)
        hso = self.conn.hso
        hso.Clear()
        try:
            hso.Search(f"Name={name},all")
            if hso.Count > 0:
                return hso.Item(1).Value
        except Exception:
            pass
        finally:
            hso.Clear()  # Always clean up, even on exception

        raise RuntimeError(
            f"Geometry '{name}' not found in active Part (searched shapes, sketches, "
            "bodies, origin elements, and geometrical sets)."
        )

    def _pad(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()

        # Use pycatia backend when available, win32com fallback
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            body = self.conn.get_active_part_body()
            sf = part.shape_factory
            part.in_work_object = body
        else:
            part = self.conn.get_active_part()
            body = self.conn.get_active_part_body()
            try:
                sf = part.ShapeFactory
            except Exception as e:
                raise RuntimeError(
                    f"Could not access ShapeFactory from part: {e}\n"
                    "Ensure the active document is a valid Part document."
                )
            part.InWorkObject = body

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)

        sketch_repr = repr(type(sketch))
        if "IUnknown" in sketch_repr or "unknown" in sketch_repr.lower():
            raise RuntimeError(
                f"Sketch object has invalid COM type: {sketch_repr}. "
                "Try reconnecting to CATIA and recreating the sketch."
            )

        height = validate_positive_float(args["height"], "height")
        direction = args.get("direction", "normal")
        symmetric = args.get("symmetric", False)

        try:
            pad = sf.AddNewPad(sketch, height)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewPad", e))

        if symmetric:
            pad.IsSymmetric = True
        elif direction == "reverse":
            pad.DirectionOrientation = 1
        elif direction == "both":
            pad.IsSymmetric = True

        try:
            if has_pycatia:
                part.update_object(pad)
            else:
                part.UpdateObject(pad)
        except Exception as e:
            raise RuntimeError(f"Failed to update pad feature: {e}")

        self.conn.refresh_display()
        return f"Pad created: {height} mm ({direction}). Feature: '{pad.Name}'"

    def _pocket(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            body = self.conn.get_active_part_body()
            sf = part.shape_factory
            part.in_work_object = body
        else:
            part = self.conn.get_active_part()
            body = self.conn.get_active_part_body()
            sf = part.ShapeFactory
            part.InWorkObject = body

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)
        depth = validate_positive_float(args["depth"], "depth")

        try:
            pocket = sf.AddNewPocket(sketch, depth)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewPocket", e))

        if args.get("direction") == "reverse":
            pocket.DirectionOrientation = 1

        if has_pycatia:
            part.update_object(pocket)
        else:
            part.UpdateObject(pocket)
        self.conn.refresh_display()
        return f"Pocket created: {depth} mm deep. Feature: '{pocket.Name}'"

    def _shaft(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        # Force win32com — pycatia shape_factory returns placeholder objects for Shaft
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()
        sf = part.ShapeFactory
        part.InWorkObject = body

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)
        angle = validate_positive_float(args.get("angle", 360), "angle")

        try:
            shaft = sf.AddNewShaft(sketch)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewShaft", e))
        shaft.FirstAngle = angle

        part.UpdateObject(shaft)
        self.conn.refresh_display()
        return f"Shaft (revolution) created: {angle}°. Feature: '{shaft.Name}'"

    def _groove(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        # Force win32com — pycatia shape_factory returns placeholder objects for Groove
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()
        sf = part.ShapeFactory
        part.InWorkObject = body

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)
        angle = validate_positive_float(args.get("angle", 360), "angle")

        try:
            groove = sf.AddNewGroove(sketch)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewGroove", e))
        groove.FirstAngle = angle

        part.UpdateObject(groove)
        self.conn.refresh_display()
        return f"Groove (revolution cut) created: {angle}°. Feature: '{groove.Name}'"

    def _fillet(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        radius = validate_positive_float(args["radius"], "radius")
        edge_name = args.get("edge_name")

        if edge_name:
            target = self._resolve_geometry(edge_name)
        else:
            target = self._get_last_shape()

        if has_pycatia:
            edge_ref = part.create_reference_from_object(target)
        else:
            edge_ref = part.CreateReferenceFromObject(target)

        try:
            fillet = sf.AddNewSolidEdgeFilletWithConstantRadius(
                edge_ref,
                1,
                radius,
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewSolidEdgeFilletWithConstantRadius", e))

        if has_pycatia:
            part.update_object(fillet)
        else:
            part.UpdateObject(fillet)
        self.conn.refresh_display()
        return f"Fillet created: R{radius} mm. Feature: '{fillet.Name}'"

    def _chamfer(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        length = validate_positive_float(args["length"], "length")
        angle = validate_positive_float(args.get("angle", 45), "angle")
        edge_name = args.get("edge_name")

        if edge_name:
            target = self._resolve_geometry(edge_name)
        else:
            target = self._get_last_shape()

        if has_pycatia:
            edge_ref = part.create_reference_from_object(target)
        else:
            edge_ref = part.CreateReferenceFromObject(target)

        try:
            chamfer = sf.AddNewChamfer(
                edge_ref,
                1,
                0,
                length,
                angle,
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewChamfer", e))

        if has_pycatia:
            part.update_object(chamfer)
        self.conn.refresh_display()
        return f"Chamfer created: {length} mm at {angle}°. Feature: '{chamfer.Name}'"

    def _hole(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        # Force win32com — pycatia shape_factory returns placeholder objects for Hole
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()
        sf = part.ShapeFactory
        part.InWorkObject = body

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)
        diameter = validate_positive_float(args["diameter"], "diameter")
        depth = validate_positive_float(args["depth"], "depth")

        try:
            hole = sf.AddNewHoleFromSketch(sketch, depth)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewHoleFromSketch", e))
        hole.Diameter = diameter
        hole.BottomType = 0
        if args.get("threaded", False):
            hole.ThreadingMode = 1

        part.UpdateObject(hole)
        self.conn.refresh_display()
        return f"Hole created: D{diameter} mm, depth {depth} mm. Feature: '{hole.Name}'"

    def _rect_pattern(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        feature = self._get_last_shape(args.get("feature_name"))
        d1_count = validate_positive_int(args["dir1_count"], "dir1_count")
        d1_spacing = validate_positive_float(args["dir1_spacing"], "dir1_spacing")
        d2_count = validate_positive_int(args.get("dir2_count", 1), "dir2_count")
        d2_spacing = validate_non_negative_float(args.get("dir2_spacing", 0), "dir2_spacing")

        if has_pycatia:
            feat_ref = part.create_reference_from_object(feature)
        else:
            feat_ref = part.CreateReferenceFromObject(feature)

        try:
            pattern = sf.AddNewRectPattern(
                feat_ref,
                d1_count, d2_count,
                d1_spacing, d2_spacing,
                1, 1,
                True,
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewRectPattern", e))

        if has_pycatia:
            part.update_object(pattern)
        else:
            part.UpdateObject(pattern)
        self.conn.refresh_display()
        return (
            f"Rectangular pattern created: {d1_count}x{d2_count}, "
            f"spacing {d1_spacing}x{d2_spacing} mm. Feature: '{pattern.Name}'"
        )

    def _circ_pattern(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        feature = self._get_last_shape(args.get("feature_name"))
        count = validate_positive_int(args["count"], "count")
        angular_spacing = validate_positive_float(
            args.get("angular_spacing", 360.0 / count), "angular_spacing"
        )

        try:
            pattern = sf.AddNewCircPattern(
                feature,
                count,
                1,              # rows
                angular_spacing,
                0,              # row spacing
                1, 1,           # direction specification
                True,           # keep specification
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewCircPattern", e))

        if has_pycatia:
            part.update_object(pattern)
        else:
            part.UpdateObject(pattern)
        self.conn.refresh_display()
        return (
            f"Circular pattern created: {count} instances, "
            f"{angular_spacing}° spacing. Feature: '{pattern.Name}'"
        )

    def _mirror(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        plane_key = validate_plane(args["plane"])
        planes = self.conn.get_origin_elements()
        mirror_plane = planes[plane_key]
        ref = part.CreateReferenceFromObject(mirror_plane)

        feature = self._get_last_shape(args.get("feature_name"))
        try:
            mirror = sf.AddNewMirror(ref)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewMirror", e))

        if has_pycatia:
            part.update_object(mirror)
        else:
            part.UpdateObject(mirror)
        self.conn.refresh_display()
        return f"Mirror created about {plane_key.upper()} plane. Feature: '{mirror.Name}'"

    def _shell(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        thickness = validate_positive_float(args["thickness"], "thickness")

        try:
            shell = sf.AddNewShell(None, thickness, thickness)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewShell", e))

        faces_to_remove = args.get("faces_to_remove", [])
        if faces_to_remove:
            sel = self.conn.hso
            sel.Clear()
            try:
                for face_name in faces_to_remove:
                    sel.Search(f"Name={face_name},all")
                    if sel.Count > 0:
                        try:
                            shell.AddFaceToRemove(
                                part.CreateReferenceFromObject(sel.Item(1).Value)
                            )
                        except Exception:
                            pass
                    sel.Clear()
            finally:
                sel.Clear()

        if has_pycatia:
            part.update_object(shell)
        else:
            part.UpdateObject(shell)
        self.conn.refresh_display()
        return f"Shell created: {thickness} mm wall thickness. Feature: '{shell.Name}'"

    def _draft(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        angle = validate_non_negative_float(args["angle"], "angle")

        plane_key = validate_plane(args.get("pulling_direction", "xy"))
        planes = self.conn.get_origin_elements()
        neutral = planes.get(plane_key)

        last_shape = self._get_last_shape()
        face_ref = part.CreateReferenceFromObject(last_shape)
        neutral_ref = part.CreateReferenceFromObject(neutral)

        try:
            draft = sf.AddNewDraft(
                face_ref,           # i_face_to_draft
                neutral_ref,        # i_neutral
                0,                 # i_neutral_mode: catDraftNeutralNoPropag = 0
                None,              # i_parting: no parting plane
                0.0, 0.0, -1.0,   # i_dir_x/y/z: default pull direction (-Z)
                0,                 # i_mode: catDraftModeAutomatic = 0
                angle,             # i_angle
                0,                 # i_multiselection_mode: catDraftMultiSelectionModeNone = 0
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewDraft", e))

        if has_pycatia:
            part.update_object(draft)
        else:
            part.UpdateObject(draft)
        self.conn.refresh_display()
        return f"Draft created: {angle}° angle. Feature: '{draft.Name}'"

    def _thickness(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        offset = validate_non_negative_float(args["offset"], "offset")
        shape_ref = part.CreateReferenceFromObject(self._get_last_shape())
        try:
            thickness_feat = sf.AddNewThickness(shape_ref, offset)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewThickness", e))

        if has_pycatia:
            part.update_object(thickness_feat)
        else:
            part.UpdateObject(thickness_feat)
        self.conn.refresh_display()
        return f"Thickness added: {offset} mm offset. Feature: '{thickness_feat.Name}'"

    def _lifting(self, args: dict[str, Any]) -> str:
        """Create a Lifting (variable-thickness extrusion along a curve).

        CATIA API: ShapeFactory.AddNewLifting(GuideCurve, Sketch, Support=None)
        The sketch profile is extruded along the guiding curve.  An optional
        support curve controls the variable thickness (distance from support).
        """
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            body = self.conn.get_active_part_body()
            sf = part.shape_factory
            part.in_work_object = body
        else:
            part = self.conn.get_active_part()
            body = self.conn.get_active_part_body()
            sf = part.ShapeFactory
            part.InWorkObject = body

        guiding_curve_name = args.get("guiding_curve")
        if not guiding_curve_name:
            raise RuntimeError("Lifting requires 'guiding_curve' (edge/curve name).")

        sketch_name = validate_sketch_name(args.get("sketch_name"))
        sketch = self._get_last_sketch(sketch_name, part)

        support_name = args.get("support")

        # Resolve guiding curve reference
        try:
            guiding_curve = self._resolve_geometry(guiding_curve_name)
            guide_ref = part.CreateReferenceFromObject(guiding_curve)
        except Exception as e:
            raise RuntimeError(
                f"Could not resolve guiding curve '{guiding_curve_name}': {e}\n"
                "Use catia_list_edges or catia_list_features to find valid curve names."
            ) from None

        # Resolve optional support reference
        support_ref = None
        if support_name:
            try:
                support = self._resolve_geometry(support_name)
                support_ref = part.CreateReferenceFromObject(support)
            except Exception as e:
                raise RuntimeError(
                    f"Could not resolve support '{support_name}': {e}"
                ) from None

        sketch_ref = part.CreateReferenceFromObject(sketch)

        try:
            lifting = sf.AddNewLifting(guide_ref, sketch_ref, support_ref)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewLifting", e))

        try:
            if has_pycatia:
                part.update_object(lifting)
            else:
                part.UpdateObject(lifting)
        except Exception as e:
            raise RuntimeError(f"Failed to update lifting feature: {e}")

        self.conn.refresh_display()
        return f"Lifting created along '{guiding_curve_name}'. Feature: '{lifting.Name}'"

    def _sweep(self, args: dict[str, Any]) -> str:
        """Create a Variable Section Sweep (VSS).

        CATIA API: ShapeFactory.AddNewVariableSectionShape(
            i_spine, i_section, i_profile, i_direction)
        Sweeps a profile along a spine curve.  Optionally a second profile
        (end section) and a direction curve for orientation control.
        """
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            body = self.conn.get_active_part_body()
            sf = part.shape_factory
            part.in_work_object = body
        else:
            part = self.conn.get_active_part()
            body = self.conn.get_active_part_body()
            sf = part.ShapeFactory
            part.InWorkObject = body

        spine_name = args.get("spine")
        section_name = args.get("section")
        if not spine_name:
            raise RuntimeError("Sweep requires 'spine' (spine curve name).")
        if not section_name:
            raise RuntimeError("Sweep requires 'section' (start profile name).")

        # Resolve spine reference
        try:
            spine = self._resolve_geometry(spine_name)
            spine_ref = part.CreateReferenceFromObject(spine)
        except Exception as e:
            raise RuntimeError(
                f"Could not resolve spine '{spine_name}': {e}\n"
                "Use catia_list_edges or catia_list_features to find valid curve names."
            ) from None

        # Resolve section reference
        try:
            section = self._resolve_geometry(section_name)
            section_ref = part.CreateReferenceFromObject(section)
        except Exception as e:
            raise RuntimeError(
                f"Could not resolve section '{section_name}': {e}\n"
                "Provide a valid sketch or curve name."
            ) from None

        # Resolve optional profile (end section)
        profile_name = args.get("profile")
        profile_ref = None
        if profile_name:
            try:
                profile = self._resolve_geometry(profile_name)
                profile_ref = part.CreateReferenceFromObject(profile)
            except Exception as e:
                raise RuntimeError(
                    f"Could not resolve profile '{profile_name}': {e}"
                ) from None

        # Resolve optional direction curve
        direction_name = args.get("direction")
        direction_ref = None
        if direction_name:
            try:
                direction = self._resolve_geometry(direction_name)
                direction_ref = part.CreateReferenceFromObject(direction)
            except Exception as e:
                raise RuntimeError(
                    f"Could not resolve direction '{direction_name}': {e}"
                ) from None

        try:
            sweep = sf.AddNewVariableSectionShape(
                spine_ref, section_ref, profile_ref, direction_ref
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewVariableSectionShape", e))

        try:
            if has_pycatia:
                part.update_object(sweep)
            else:
                part.UpdateObject(sweep)
        except Exception as e:
            raise RuntimeError(f"Failed to update sweep feature: {e}")

        self.conn.refresh_display()
        return f"Sweep (VSS) created along '{spine_name}'. Feature: '{sweep.Name}'"

    def _loft(self, args: dict[str, Any]) -> str:
        """Create a Loft from multiple sketches.

        CATIA API: ShapeFactory.AddNewLoft(i_references: list[Reference])
        Generates a smooth solid between 2 or more profile sketches.
        """
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            body = self.conn.get_active_part_body()
            sf = part.shape_factory
            part.in_work_object = body
        else:
            part = self.conn.get_active_part()
            body = self.conn.get_active_part_body()
            sf = part.ShapeFactory
            part.InWorkObject = body

        sketch_names = args.get("sketch_names", [])
        if not isinstance(sketch_names, list):
            raise RuntimeError("Loft requires 'sketch_names' as a list of strings.")
        if len(sketch_names) < 2:
            raise RuntimeError(
                "Loft requires at least 2 sketches. "
                "Provide a list like ['Sketch.1', 'Sketch.2']."
            )

        # Build list of references from each sketch
        references = []
        for name in sketch_names:
            if not isinstance(name, str) or not name.strip():
                raise RuntimeError(
                    f"Invalid sketch name in list: '{name}'. Must be non-empty strings."
                )
            try:
                sketch = self._get_last_sketch(name, part)
                ref = part.CreateReferenceFromObject(sketch)
                references.append(ref)
            except RuntimeError:
                # Sketch not found — re-raise with context
                raise RuntimeError(
                    f"Could not resolve sketch '{name}' for loft. "
                    "Make sure all sketches exist and are closed."
                ) from None

        try:
            loft = sf.AddNewLoft(references)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewLoft", e))

        try:
            if has_pycatia:
                part.update_object(loft)
            else:
                part.UpdateObject(loft)
        except Exception as e:
            raise RuntimeError(f"Failed to update loft feature: {e}")

        self.conn.refresh_display()
        names_str = ", ".join(sketch_names)
        return f"Loft created from {len(sketch_names)} sketches ([{names_str}]). Feature: '{loft.Name}'"

    def _boolean(self, args: dict[str, Any]) -> str:
        """Perform a Boolean operation between two PartBodies.

        CATIA API: ShapeFactory.AddOperation(i_shape, i_other_body, i_mode)
        Modes: catBooleanUnion (0), catBooleanCut (1), catBooleanIntersect (2)
        """
        self.conn.ensure_connected()
        has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
        if has_pycatia:
            part = self.conn.get_active_part_pycatia()
            sf = part.shape_factory
        else:
            part = self.conn.get_active_part()
            sf = part.ShapeFactory

        operation = args.get("operation")
        body1_name = args.get("body1")
        body2_name = args.get("body2")

        if not operation:
            raise RuntimeError("Boolean requires 'operation' (union, intersection, or difference).")
        if not body1_name:
            raise RuntimeError("Boolean requires 'body1' (target body name).")
        if not body2_name:
            raise RuntimeError("Boolean requires 'body2' (tool body name).")

        if operation not in ("union", "intersection", "difference"):
            raise RuntimeError(
                f"Invalid boolean operation '{operation}'. "
                "Must be one of: 'union', 'intersection', 'difference'."
            )

        if body1_name == body2_name:
            raise RuntimeError(
                f"Boolean operation cannot use the same body for both arguments "
                f"('{body1_name}'). Use two different bodies."
            )

        # Map operation string to CATIA mode
        mode_map = {
            "union": 0,          # catBooleanUnion
            "difference": 1,     # catBooleanCut
            "intersection": 2,   # catBooleanIntersect
        }
        mode = mode_map[operation]

        # Resolve bodies
        try:
            bodies = part.Bodies
            body1 = bodies.Item(body1_name)
        except Exception as e:
            raise RuntimeError(
                f"Body '{body1_name}' not found in Part. {e}\n"
                "Use catia_list_features to check body names."
            ) from None

        try:
            body2 = bodies.Item(body2_name)
        except Exception as e:
            raise RuntimeError(
                f"Body '{body2_name}' not found in Part. {e}\n"
                "Use catia_list_features to check body names."
            ) from None

        try:
            boolean = sf.AddOperation(body1, body2, mode)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddOperation", e))

        try:
            if has_pycatia:
                part.update_object(boolean)
            else:
                part.UpdateObject(boolean)
        except Exception as e:
            raise RuntimeError(f"Failed to update boolean feature: {e}")

        self.conn.refresh_display()
        op_label = {
            "union": "Union (merge)",
            "difference": "Difference (cut)",
            "intersection": "Intersection",
        }[operation]
        return f"Boolean {op_label}: '{body1_name}' ◦ '{body2_name}'. Feature: '{boolean.Name}'"

    def _list_features(self) -> str:
        self.conn.ensure_connected()
        body = self.conn.get_active_part_body()
        shapes = body.Shapes

        features = []
        for i in range(1, shapes.Count + 1):
            shape = shapes.Item(i)
            features.append({
                "index": i,
                "name": shape.Name,
                "type": shape.Type if hasattr(shape, "Type") else "unknown",
            })

        if not features:
            return "No features in the active body"
        return json.dumps(features, indent=2)

    def _list_edges(self) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()

        # Get edges from the last shape
        last_shape = self._get_last_shape()
        edges = []
        try:
            # Access boundary representation
            sel = self.conn.hso
            sel.Clear()
            sel.Add(last_shape)
            sel.Search("Topology.Edge,sel")

            for i in range(1, sel.Count + 1):
                edges.append({
                    "index": i,
                    "name": sel.Item(i).Value.Name if hasattr(sel.Item(i).Value, "Name") else f"Edge.{i}",
                })
            sel.Clear()
        except Exception as e:
            return f"Could not enumerate edges: {e}. Use CATIA selection to identify edge names."

        if not edges:
            return "No edges found on the last feature"
        return json.dumps(edges, indent=2)
