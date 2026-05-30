"""Measurement and analysis tools for CATIA V5.

Distance, angle, inertia, bounding box, and part property queries.
"""

from __future__ import annotations

import json
from typing import Any

from catia_mcp.connection import CATIAConnection
from catia_mcp.utils import (
    format_catia_error,
    validate_non_negative_float,
    validate_positive_float,
)

# ── ByRef array helpers for win32com late binding ──
#
# CATIA's MeasurablePart interface methods (GetCOG, GetInertia, GetBoundingBox)
# accept output arrays via ByRef.  win32com.client late binding cannot pass
# mutable arrays, so we use early binding (DispatchWithSpecs) when available,
# otherwise fall back to reading individual properties that don't require ByRef.

def _get_cog_com(measurable: Any) -> tuple[float, float, float]:
    """Return center-of-gravity via win32com Dispatch.

    Uses early-binding dispatch to satisfy the ByRef requirement.
    Falls back to reading COG properties directly.
    """
    try:
        import pythoncom
        import win32com.client
        # Create a DispatchWithSpecs to get a typed interface
        dws = win32com.client.dynamic.DispatchWithSpecs(measurable._oleobj_.QueryInterface(
            pythoncom.IID_IDispatch, pythoncom.IID_IDispatch))
        cog = [0.0, 0.0, 0.0]
        dws.GetCOG(cog)
        return float(cog[0]), float(cog[1]), float(cog[2])
    except Exception:
        pass

    # Fallback: read individual COG properties
    try:
        cog = [0.0, 0.0, 0.0]
        measurable.GetCOG(cog)
        return float(cog[0]), float(cog[1]), float(cog[2])
    except Exception:
        pass

    # Last resort: use COG property (CATIA R26+)
    try:
        cog_prop = measurable.COG
        return float(cog_prop[0]), float(cog_prop[1]), float(cog_prop[2])
    except Exception:
        raise RuntimeError(
            "Could not read center of gravity. "
            "ByRef array support may require early binding or pycatia."
        )


def _get_inertia_com(measurable: Any) -> list[list[float]]:
    """Return 3x3 inertia matrix via win32com Dispatch.

    Uses early-binding dispatch to satisfy the ByRef requirement.
    Falls back to reading individual inertia properties.
    """
    try:
        import pythoncom
        import win32com.client
        dws = win32com.client.dynamic.DispatchWithSpecs(measurable._oleobj_.QueryInterface(
            pythoncom.IID_IDispatch, pythoncom.IID_IDispatch))
        inertia = [0.0] * 9
        dws.GetInertia(inertia)
        return [
            [float(inertia[0]), float(inertia[1]), float(inertia[2])],
            [float(inertia[3]), float(inertia[4]), float(inertia[5])],
            [float(inertia[6]), float(inertia[7]), float(inertia[8])],
        ]
    except Exception:
        pass

    # Fallback: late binding (may work on some CATIA versions)
    try:
        inertia = [0.0] * 9
        measurable.GetInertia(inertia)
        return [
            [float(inertia[0]), float(inertia[1]), float(inertia[2])],
            [float(inertia[3]), float(inertia[4]), float(inertia[5])],
            [float(inertia[6]), float(inertia[7]), float(inertia[8])],
        ]
    except Exception:
        pass

    # Last resort: individual properties
    try:
        inertia_prop = measurable.Inertia
        return [
            [float(inertia_prop[0]), float(inertia_prop[1]), float(inertia_prop[2])],
            [float(inertia_prop[3]), float(inertia_prop[4]), float(inertia_prop[5])],
            [float(inertia_prop[6]), float(inertia_prop[7]), float(inertia_prop[8])],
        ]
    except Exception:
        raise RuntimeError(
            "Could not read inertia matrix. "
            "ByRef array support may require early binding or pycatia."
        )


def _get_bounding_box_com(measurable: Any) -> list[float]:
    """Return bounding box (6 floats) via win32com Dispatch.

    Uses early-binding dispatch to satisfy the ByRef requirement.
    Falls back to reading individual bounding box properties.
    """
    try:
        import pythoncom
        import win32com.client
        dws = win32com.client.dynamic.DispatchWithSpecs(measurable._oleobj_.QueryInterface(
            pythoncom.IID_IDispatch, pythoncom.IID_IDispatch))
        bbox = [0.0] * 6
        dws.GetBoundingBox(bbox)
        return [float(bbox[i]) for i in range(6)]
    except Exception:
        pass

    # Fallback: late binding (may work on some CATIA versions)
    try:
        bbox = [0.0] * 6
        measurable.GetBoundingBox(bbox)
        return [float(bbox[i]) for i in range(6)]
    except Exception:
        pass

    # Last resort: individual properties
    try:
        bbox_prop = measurable.BoundingBox
        return [float(bbox_prop[i]) for i in range(6)]
    except Exception:
        raise RuntimeError(
            "Could not read bounding box. "
            "ByRef array support may require early binding or pycatia."
        )


class MeasurementTools:
    """Tools for measurement and analysis in CATIA V5."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_measure_distance",
                "description": (
                    "Measure the minimum distance between two geometry elements. "
                    "Returns distance in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element1": {
                            "type": "string",
                            "description": "Name of first element (feature, face, edge, point)",
                        },
                        "element2": {
                            "type": "string",
                            "description": "Name of second element",
                        },
                    },
                    "required": ["element1", "element2"],
                },
            },
            {
                "name": "catia_get_inertia",
                "description": (
                    "Get inertia properties of the active part: volume, surface area, "
                    "center of gravity, mass (if density is defined), moments of inertia."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "density": {
                            "type": "number",
                            "description": "Material density in kg/m3 (optional, for mass calculation)",
                        },
                    },
                },
            },
            {
                "name": "catia_get_bounding_box",
                "description": (
                    "Get the bounding box of the active part. "
                    "Returns min/max coordinates in mm."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "catia_get_parameters",
                "description": (
                    "List all user-defined and computed parameters of the active part. "
                    "Includes dimensions, formulas, and design tables."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Optional name filter (partial match)",
                        },
                    },
                },
            },
            {
                "name": "catia_set_parameter",
                "description": (
                    "Set the value of a named parameter in the active part. "
                    "Useful for parametric design modifications."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Full parameter name (e.g., 'Part1\\\\\\\\Pad.1\\\\\\\\FirstLimit\\\\\\\\Length')",
                        },
                        "value": {
                            "type": "number",
                            "description": "New value for the parameter",
                        },
                    },
                    "required": ["name", "value"],
                },
            },
            {
                "name": "catia_update_part",
                "description": "Force update/rebuild of the active part. Recalculates all features.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_measure_distance":
                return self._measure_distance(arguments["element1"], arguments["element2"])
            case "catia_get_inertia":
                return self._get_inertia(arguments.get("density"))
            case "catia_get_bounding_box":
                return self._get_bounding_box()
            case "catia_get_parameters":
                return self._get_parameters(arguments.get("filter"))
            case "catia_set_parameter":
                return self._set_parameter(arguments["name"], arguments["value"])
            case "catia_update_part":
                return self._update_part()
            case _:
                raise ValueError(f"Unknown measurement tool: {tool_name}")

    def _measure_distance(self, elem1_name: str, elem2_name: str) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        try:
            spa = self.conn.app.GetWorkbench("SPAWorkbench")
        except Exception as e:
            raise RuntimeError(format_catia_error("GetWorkbench(SPAWorkbench)", e))

        sel = self.conn.hso
        sel.Clear()

        sel.Search(f"Name={elem1_name},all")
        if sel.Count == 0:
            raise RuntimeError(f"Element '{elem1_name}' not found")
        ref1 = part.CreateReferenceFromObject(sel.Item(1).Value)

        sel.Clear()
        sel.Search(f"Name={elem2_name},all")
        if sel.Count == 0:
            raise RuntimeError(f"Element '{elem2_name}' not found")
        ref2 = part.CreateReferenceFromObject(sel.Item(1).Value)
        sel.Clear()

        try:
            measurable = spa.GetMeasurable(ref1)
            distance = measurable.GetMinimumDistance(ref2)
        except Exception as e:
            raise RuntimeError(format_catia_error("GetMinimumDistance", e))

        return f"Minimum distance between '{elem1_name}' and '{elem2_name}': {distance:.4f} mm"

    def _get_inertia(self, density: float | None = None) -> str:
        self.conn.ensure_connected()
        if density is not None:
            validate_non_negative_float(density, "density")
        try:
            spa = self.conn.app.GetWorkbench("SPAWorkbench")
        except Exception as e:
            raise RuntimeError(format_catia_error("GetWorkbench(SPAWorkbench)", e))
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()
        ref = part.CreateReferenceFromObject(body)

        measurable = spa.GetMeasurable(ref)

        result: dict[str, Any] = {}

        try:
            result["volume_mm3"] = round(float(measurable.Volume), 4)
            result["volume_cm3"] = round(float(measurable.Volume) / 1000, 4)
        except Exception:
            pass

        try:
            result["area_mm2"] = round(float(measurable.Area), 4)
            result["area_cm2"] = round(float(measurable.Area) / 100, 4)
        except Exception:
            pass

        try:
            cog_x, cog_y, cog_z = _get_cog_com(measurable)
            result["center_of_gravity_mm"] = {
                "x": round(cog_x, 4),
                "y": round(cog_y, 4),
                "z": round(cog_z, 4),
            }
        except Exception as e:
            result["center_of_gravity_mm"] = {"error": str(e)}

        if density:
            if "volume_mm3" not in result:
                raise RuntimeError(
                    "Cannot calculate mass: volume measurement failed. "
                    "Make sure the part has a valid solid body."
                )
            volume_m3 = result["volume_mm3"] * 1e-9  # mm³ to m³
            mass_kg = density * volume_m3
            result["mass_kg"] = round(mass_kg, 6)
            result["mass_g"] = round(mass_kg * 1000, 3)
            result["density_kg_m3"] = density

        try:
            inertia = _get_inertia_com(measurable)
            result["inertia_matrix"] = [
                [round(v, 4) for v in row] for row in inertia
            ]
        except Exception as e:
            result["inertia_matrix"] = {"error": str(e)}

        return json.dumps(result, indent=2)

    def _get_bounding_box(self) -> str:
        self.conn.ensure_connected()
        try:
            spa = self.conn.app.GetWorkbench("SPAWorkbench")
        except Exception as e:
            raise RuntimeError(format_catia_error("GetWorkbench(SPAWorkbench)", e))
        part = self.conn.get_active_part()
        body = self.conn.get_active_part_body()
        ref = part.CreateReferenceFromObject(body)

        measurable = spa.GetMeasurable(ref)

        try:
            bbox = _get_bounding_box_com(measurable)
        except Exception as e:
            raise RuntimeError(format_catia_error("GetBoundingBox", e))

        result = {
            "min": {"x": round(bbox[0], 4), "y": round(bbox[1], 4), "z": round(bbox[2], 4)},
            "max": {"x": round(bbox[3], 4), "y": round(bbox[4], 4), "z": round(bbox[5], 4)},
            "dimensions": {
                "length_x": round(bbox[3] - bbox[0], 4),
                "length_y": round(bbox[4] - bbox[1], 4),
                "length_z": round(bbox[5] - bbox[2], 4),
            },
        }
        return json.dumps(result, indent=2)

    def _get_parameters(self, name_filter: str | None = None) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        params = part.Parameters

        result = []
        for i in range(1, params.Count + 1):
            param = params.Item(i)
            name = param.Name

            if name_filter and name_filter.lower() not in name.lower():
                continue

            info: dict[str, Any] = {"name": name}
            try:
                info["value"] = param.Value
            except Exception:
                info["value"] = "N/A"
            try:
                info["comment"] = param.Comment
            except Exception:
                pass

            result.append(info)

        if not result:
            return "No parameters found" + (f" matching '{name_filter}'" if name_filter else "")
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _set_parameter(self, name: str, value: float) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        params = part.Parameters

        try:
            param = params.Item(name)
        except Exception:
            raise ValueError(f"Parameter '{name}' not found in the active part.")

        old_value = param.Value
        try:
            param.Value = value
            part.Update()
        except Exception as e:
            raise RuntimeError(format_catia_error("SetParameter", e))

        self.conn.refresh_display()
        return f"Parameter '{name}' changed: {old_value} -> {value}"

    def _update_part(self) -> str:
        self.conn.ensure_connected()
        part = self.conn.get_active_part()
        try:
            part.Update()
        except Exception as e:
            raise RuntimeError(format_catia_error("Update", e))
        self.conn.refresh_display()
        return "Part updated successfully"