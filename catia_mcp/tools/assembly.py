"""Assembly tools for CATIA V5.

Product/Assembly management: add components, constraints (Fix, Coincidence,
Contact, Offset, Angle), move components, and manage the product tree.
"""

from __future__ import annotations

import json
from typing import Any

from catia_mcp.connection import CATIAConnection
from catia_mcp.utils import (
    format_catia_error,
    validate_file_path,
    validate_non_negative_float,
    validate_positive_float,
)


class AssemblyTools:
    """Tools for assembly (Product) operations in CATIA V5."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_add_component",
                "description": (
                    "Add an existing CATPart or CATProduct file as a component in the active assembly. "
                    "The component is inserted at the origin."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Full path to the .CATPart or .CATProduct file to add",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "catia_add_new_part",
                "description": (
                    "Create a new empty Part directly inside the active assembly. "
                    "Returns the name of the created component."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the new part component",
                        },
                    },
                },
            },
            {
                "name": "catia_fix_constraint",
                "description": (
                    "Fix a component in place (remove all degrees of freedom). "
                    "Typically applied to the base/reference component."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_name": {
                            "type": "string",
                            "description": "Name of the component to fix",
                        },
                    },
                    "required": ["component_name"],
                },
            },
            {
                "name": "catia_coincidence_constraint",
                "description": (
                    "Create a Coincidence constraint between two components. "
                    "Aligns axes, planes, or points of two components."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "element1": {
                            "type": "string",
                            "description": "Geometry element on component1 (e.g., 'xy plane', 'Face.1')",
                        },
                        "element2": {
                            "type": "string",
                            "description": "Geometry element on component2",
                        },
                    },
                    "required": ["component1", "component2"],
                },
            },
            {
                "name": "catia_offset_constraint",
                "description": (
                    "Create an Offset constraint between two faces/planes of two components. "
                    "Maintains a constant distance between the reference elements."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "offset": {
                            "type": "number",
                            "description": "Offset distance in mm",
                        },
                    },
                    "required": ["component1", "component2", "offset"],
                },
            },
            {
                "name": "catia_angle_constraint",
                "description": "Create an Angle constraint between two components.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "angle": {
                            "type": "number",
                            "description": "Angle in degrees",
                        },
                    },
                    "required": ["component1", "component2", "angle"],
                },
            },
            {
                "name": "catia_move_component",
                "description": (
                    "Move a component by translation and/or rotation. "
                    "Translation in mm, rotation in degrees."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_name": {
                            "type": "string",
                            "description": "Name of the component to move",
                        },
                        "tx": {"type": "number", "description": "Translation X (mm)", "default": 0},
                        "ty": {"type": "number", "description": "Translation Y (mm)", "default": 0},
                        "tz": {"type": "number", "description": "Translation Z (mm)", "default": 0},
                        "rx": {"type": "number", "description": "Rotation around X (degrees)", "default": 0},
                        "ry": {"type": "number", "description": "Rotation around Y (degrees)", "default": 0},
                        "rz": {"type": "number", "description": "Rotation around Z (degrees)", "default": 0},
                    },
                    "required": ["component_name"],
                },
            },
            {
                "name": "catia_list_components",
                "description": "List all components in the active assembly/product with their names and positions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "catia_contact_constraint",
                "description": (
                    "Create a Contact constraint between two components. "
                    "Faces touch without penetration (zero gap)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "element1": {
                            "type": "string",
                            "description": "Geometry element on component1 (optional)",
                        },
                        "element2": {
                            "type": "string",
                            "description": "Geometry element on component2 (optional)",
                        },
                    },
                    "required": ["component1", "component2"],
                },
            },
            {
                "name": "catia_distance_constraint",
                "description": (
                    "Create a Distance constraint between two components. "
                    "Maintains a constant distance between reference elements."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "distance": {
                            "type": "number",
                            "description": "Distance in mm",
                        },
                        "element1": {
                            "type": "string",
                            "description": "Geometry element on component1 (optional)",
                        },
                        "element2": {
                            "type": "string",
                            "description": "Geometry element on component2 (optional)",
                        },
                    },
                    "required": ["component1", "component2", "distance"],
                },
            },
            {
                "name": "catia_tangent_constraint",
                "description": (
                    "Create a Tangency constraint between two components. "
                    "Surfaces touch tangentially without penetration."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component1": {
                            "type": "string",
                            "description": "Name of first component",
                        },
                        "component2": {
                            "type": "string",
                            "description": "Name of second component",
                        },
                        "element1": {
                            "type": "string",
                            "description": "Geometry element on component1 (optional)",
                        },
                        "element2": {
                            "type": "string",
                            "description": "Geometry element on component2 (optional)",
                        },
                    },
                    "required": ["component1", "component2"],
                },
            },
            {
                "name": "catia_remove_component",
                "description": (
                    "Remove a component from the active assembly. "
                    "The component will be deleted from the product tree."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component_name": {
                            "type": "string",
                            "description": "Name of the component to remove",
                        },
                    },
                    "required": ["component_name"],
                },
            },
            {
                "name": "catia_remove_constraint",
                "description": (
                    "Remove a constraint from the active assembly. "
                    "Find the constraint by name and delete it."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "constraint_name": {
                            "type": "string",
                            "description": "Name of the constraint to remove",
                        },
                    },
                    "required": ["constraint_name"],
                },
            },
            {
                "name": "catia_list_constraints",
                "description": "List all assembly constraints in the active product.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_add_component":
                return self._add_component(arguments["file_path"])
            case "catia_add_new_part":
                return self._add_new_part(arguments.get("name"))
            case "catia_fix_constraint":
                return self._fix_constraint(arguments["component_name"])
            case "catia_coincidence_constraint":
                return self._coincidence_constraint(arguments)
            case "catia_offset_constraint":
                return self._offset_constraint(arguments)
            case "catia_angle_constraint":
                return self._angle_constraint(arguments)
            case "catia_move_component":
                return self._move_component(arguments)
            case "catia_contact_constraint":
                return self._contact_constraint(arguments)
            case "catia_distance_constraint":
                return self._distance_constraint(arguments)
            case "catia_tangent_constraint":
                return self._tangent_constraint(arguments)
            case "catia_remove_component":
                return self._remove_component(arguments["component_name"])
            case "catia_remove_constraint":
                return self._remove_constraint(arguments["constraint_name"])
            case "catia_list_components":
                return self._list_components()
            case "catia_list_constraints":
                return self._list_constraints()
            case _:
                raise ValueError(f"Unknown assembly tool: {tool_name}")

    def _add_component(self, file_path: str) -> str:
        product = self.conn.get_active_product()
        file_path = validate_file_path(file_path, "file_path")
        file_path = self.conn.normalize_path(file_path)
        products = product.Products
        try:
            component = products.AddComponentsFromFiles(
                [file_path], "All"
            )
        except Exception as e:
            raise RuntimeError(format_catia_error("AddComponentsFromFiles", e))
        self.conn.refresh_display()
        return f"Component added from: {file_path}"

    def _add_new_part(self, name: str | None = None) -> str:
        product = self.conn.get_active_product()
        products = product.Products
        try:
            new_product = products.AddNewProduct("Part")
        except Exception as e:
            raise RuntimeError(format_catia_error("AddNewProduct", e))
        if name:
            new_product.Name = name
        self.conn.refresh_display()
        return f"New Part component created in assembly: '{new_product.Name}'"

    def _fix_constraint(self, component_name: str) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")

        try:
            component = product.Products.Item(component_name)
        except Exception:
            raise ValueError(f"Component '{component_name}' not found in assembly.")

        try:
            cst = constraints.AddMonoEltCst(0, component)  # Fix constraint
        except Exception as e:
            raise RuntimeError(format_catia_error("AddMonoEltCst (Fix)", e))
        cst.Name = f"Fix.{component_name}"

        self.conn.refresh_display()
        return f"Fix constraint applied to '{component_name}'"

    def _coincidence_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")

        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])

        try:
            cst = constraints.AddBiEltCst(20, comp1, comp2)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Coincidence)", e))
        self.conn.refresh_display()
        return (
            f"Coincidence constraint created between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _offset_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")

        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])
        offset = validate_non_negative_float(args["offset"], "offset")

        try:
            cst = constraints.AddBiEltCst(1, comp1, comp2)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Offset)", e))
        cst.Dimension.Value = offset

        self.conn.refresh_display()
        return (
            f"Offset constraint: {offset} mm between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _angle_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")

        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])
        angle = validate_non_negative_float(args["angle"], "angle")

        try:
            cst = constraints.AddBiEltCst(6, comp1, comp2)
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Angle)", e))
        cst.Dimension.Value = angle

        self.conn.refresh_display()
        return (
            f"Angle constraint: {angle}° between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _move_component(self, args: dict[str, Any]) -> str:
        import math
        product = self.conn.get_active_product()
        try:
            component = product.Products.Item(args["component_name"])
        except Exception:
            raise ValueError(f"Component '{args['component_name']}' not found in assembly.")

        position = component.Position
        matrix = [0.0] * 12
        position.GetComponents(matrix)

        matrix[9] += args.get("tx", 0)
        matrix[10] += args.get("ty", 0)
        matrix[11] += args.get("tz", 0)

        rx = math.radians(args.get("rx", 0))
        ry = math.radians(args.get("ry", 0))
        rz = math.radians(args.get("rz", 0))

        if rx != 0 or ry != 0 or rz != 0:
            cx, sx = math.cos(rx), math.sin(rx)
            cy, sy = math.cos(ry), math.sin(ry)
            cz, sz = math.cos(rz), math.sin(rz)

            r00 = cy * cz
            r01 = cz * sx * sy - cx * sz
            r02 = sx * sz + cx * cz * sy
            r10 = cy * sz
            r11 = cx * cz + sx * sy * sz
            r12 = cx * sy * sz - cz * sx
            r20 = -sy
            r21 = cy * sx
            r22 = cx * cy

            old = matrix[:9]
            matrix[0] = r00 * old[0] + r01 * old[3] + r02 * old[6]
            matrix[1] = r00 * old[1] + r01 * old[4] + r02 * old[7]
            matrix[2] = r00 * old[2] + r01 * old[5] + r02 * old[8]
            matrix[3] = r10 * old[0] + r11 * old[3] + r12 * old[6]
            matrix[4] = r10 * old[1] + r11 * old[4] + r12 * old[7]
            matrix[5] = r10 * old[2] + r11 * old[5] + r12 * old[8]
            matrix[6] = r20 * old[0] + r21 * old[3] + r22 * old[6]
            matrix[7] = r20 * old[1] + r21 * old[4] + r22 * old[7]
            matrix[8] = r20 * old[2] + r21 * old[5] + r22 * old[8]

        try:
            position.SetComponents(matrix)
        except Exception as e:
            raise RuntimeError(format_catia_error("SetComponents", e))
        self.conn.refresh_display()

        return (
            f"Component '{args['component_name']}' moved: "
            f"T=({args.get('tx', 0)}, {args.get('ty', 0)}, {args.get('tz', 0)}) mm, "
            f"R=({args.get('rx', 0)}, {args.get('ry', 0)}, {args.get('rz', 0)})°"
        )

    def _contact_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")
        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])
        try:
            cst = constraints.AddBiEltCst(7, comp1, comp2)  # catCstTypeContact = 7
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Contact)", e))
        self.conn.refresh_display()
        return (
            f"Contact constraint created between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _distance_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")
        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])
        distance = validate_positive_float(args["distance"], "distance")
        try:
            cst = constraints.AddBiEltCst(5, comp1, comp2)  # catCstTypeDistance = 5
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Distance)", e))
        cst.Dimension.Value = distance
        self.conn.refresh_display()
        return (
            f"Distance constraint: {distance} mm between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _tangent_constraint(self, args: dict[str, Any]) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")
        comp1 = product.Products.Item(args["component1"])
        comp2 = product.Products.Item(args["component2"])
        try:
            cst = constraints.AddBiEltCst(8, comp1, comp2)  # catCstTypeTangent = 8
        except Exception as e:
            raise RuntimeError(format_catia_error("AddBiEltCst (Tangent)", e))
        self.conn.refresh_display()
        return (
            f"Tangency constraint created between "
            f"'{args['component1']}' and '{args['component2']}'"
        )

    def _remove_component(self, component_name: str) -> str:
        product = self.conn.get_active_product()
        try:
            component = product.Products.Item(component_name)
        except Exception:
            raise ValueError(f"Component '{component_name}' not found in assembly.")
        try:
            product.RemoveComponent(component)
        except Exception as e:
            raise RuntimeError(format_catia_error("RemoveComponent", e))
        self.conn.refresh_display()
        return f"Component '{component_name}' removed from assembly"

    def _remove_constraint(self, constraint_name: str) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")
        found = False
        for i in range(1, constraints.Count + 1):
            cst = constraints.Item(i)
            if cst.Name == constraint_name:
                try:
                    product.RemoveConstraint(cst)
                except Exception as e:
                    raise RuntimeError(format_catia_error("RemoveConstraint", e))
                self.conn.refresh_display()
                found = True
                return f"Constraint '{constraint_name}' removed from assembly"
        if not found:
            raise ValueError(
                f"Constraint '{constraint_name}' not found in assembly. "
                f"Use catia_list_constraints to see available constraints."
            )

    def _list_components(self) -> str:
        product = self.conn.get_active_product()
        products = product.Products

        components = []
        for i in range(1, products.Count + 1):
            comp = products.Item(i)
            pos = comp.Position
            matrix = [0.0] * 12
            try:
                pos.GetComponents(matrix)
            except Exception:
                pass
            components.append({
                "index": i,
                "name": comp.Name,
                "part_number": comp.PartNumber,
                "position": {
                    "x": round(matrix[9], 3),
                    "y": round(matrix[10], 3),
                    "z": round(matrix[11], 3),
                },
            })

        if not components:
            return "No components in the active assembly"
        return json.dumps(components, indent=2, ensure_ascii=False)

    def _list_constraints(self) -> str:
        product = self.conn.get_active_product()
        constraints = product.Connections("CATIAConstraints")

        cst_list = []
        for i in range(1, constraints.Count + 1):
            cst = constraints.Item(i)
            info = {
                "index": i,
                "name": cst.Name,
                "type": cst.Type if hasattr(cst, "Type") else "unknown",
            }
            try:
                info["status"] = "resolved" if cst.Status == 0 else "broken"
            except Exception:
                pass
            cst_list.append(info)

        if not cst_list:
            return "No constraints in the active assembly"
        return json.dumps(cst_list, indent=2, ensure_ascii=False)
