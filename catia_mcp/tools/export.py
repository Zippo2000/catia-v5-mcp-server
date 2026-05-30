"""Export tools for CATIA V5.

Export to STEP, IGES, STL, 3DXML, and other formats.
Also includes screenshot capture.
"""

from __future__ import annotations

import json
import os
from typing import Any

from catia_mcp.connection import CATIAConnection
from catia_mcp.utils import (
    format_catia_error,
    validate_file_path,
    validate_positive_int,
)

# CATIA export format identifiers
FORMAT_MAP = {
    "step": "stp",
    "stp": "stp",
    "iges": "igs",
    "igs": "igs",
    "stl": "stl",
    "3dxml": "3dxml",
    "wrl": "wrl",
    "vrml": "wrl",
    "pdf": "pdf",
    "cgr": "cgr",
}


class ExportTools:
    """Tools for exporting CATIA V5 data to external formats."""

    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_export",
                "description": (
                    "Export the active document to a file. "
                    "Supported formats: STEP (.stp), IGES (.igs), STL (.stl), "
                    "3DXML (.3dxml), VRML (.wrl), PDF (2D drawings)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": (
                                "Output file path. The format is determined by the extension. "
                                "Example: 'C:/export/my_part.stp'"
                            ),
                        },
                        "format": {
                            "type": "string",
                            "description": (
                                "Export format (optional if file extension is provided). "
                                "One of: step, iges, stl, 3dxml, vrml"
                            ),
                            "enum": ["step", "iges", "stl", "3dxml", "vrml"],
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "catia_screenshot",
                "description": (
                    "Capture a screenshot of the current 3D view and save as image file. "
                    "Supports PNG, JPG, BMP."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Output image path (e.g., 'C:/screenshots/part.png')",
                        },
                        "width": {
                            "type": "integer",
                            "description": "Image width in pixels (default: 1920)",
                            "default": 1920,
                        },
                        "height": {
                            "type": "integer",
                            "description": "Image height in pixels (default: 1080)",
                            "default": 1080,
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "catia_set_view",
                "description": (
                    "Set the 3D view orientation. "
                    "Standard views: front, back, top, bottom, left, right, isometric."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "view": {
                            "type": "string",
                            "description": "View orientation",
                            "enum": [
                                "front", "back", "top", "bottom",
                                "left", "right", "isometric",
                            ],
                        },
                    },
                    "required": ["view"],
                },
            },
            {
                "name": "catia_fit_all",
                "description": "Fit all geometry in the current 3D view (zoom to fit).",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_export":
                return self._export(arguments["file_path"], arguments.get("format"))
            case "catia_screenshot":
                return self._screenshot(
                    arguments["file_path"],
                    arguments.get("width", 1920),
                    arguments.get("height", 1080),
                )
            case "catia_set_view":
                return self._set_view(arguments["view"])
            case "catia_fit_all":
                return self._fit_all()
            case _:
                raise ValueError(f"Unknown export tool: {tool_name}")

    def _export(self, file_path: str, fmt: str | None = None) -> str:
        self.conn.ensure_connected()
        doc = self.conn.active_document

        file_path = validate_file_path(file_path, "file_path")
        file_path = self.conn.normalize_path(file_path)

        # Determine format from extension if not specified
        if fmt is None:
            ext = os.path.splitext(file_path)[1].lstrip(".").lower()
            fmt = ext

        fmt_key = fmt.lower()
        if fmt_key not in FORMAT_MAP:
            supported = ", ".join(sorted(set(FORMAT_MAP.keys())))
            raise ValueError(
                f"Unsupported export format: '{fmt}'. Supported: {supported}"
            )

        # Ensure output directory exists
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # CATIA V5 export via SaveAs with format specification
        try:
            doc.ExportData(file_path, FORMAT_MAP[fmt_key])
        except Exception as e:
            raise RuntimeError(format_catia_error("ExportData", e))

        size_info = ""
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            if size_bytes > 1024 * 1024:
                size_info = f" ({size_bytes / (1024*1024):.1f} MB)"
            elif size_bytes > 1024:
                size_info = f" ({size_bytes / 1024:.1f} KB)"
            else:
                size_info = f" ({size_bytes} bytes)"

        return f"Exported to {file_path}{size_info} (format: {fmt_key.upper()})"

    def _screenshot(self, file_path: str, width: int = 1920, height: int = 1080) -> str:
        self.conn.ensure_connected()

        file_path = validate_file_path(file_path, "file_path")
        file_path = self.conn.normalize_path(file_path)
        validate_positive_int(width, "width")
        validate_positive_int(height, "height")

        # Ensure output directory exists
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Capture via the active viewer
        viewer = self.conn._safe_active_viewer()
        if viewer is None:
            raise RuntimeError("No active 3D viewer available. Make sure a Part or Product document is open.")
        try:
            viewer.CaptureToFile(1, file_path)
        except Exception as e:
            raise RuntimeError(format_catia_error("CaptureToFile", e))

        return f"Screenshot saved to {file_path} ({width}x{height})"

    def _set_view(self, view: str) -> str:
        self.conn.ensure_connected()
        viewer = self.conn._safe_active_viewer()
        if viewer is None:
            raise RuntimeError("No active 3D viewer available. Make sure a Part or Product document is open.")
        viewpoint = viewer.Viewpoint3D

        # Standard view direction vectors and up vectors
        views = {
            "front":     {"sight": (0, 0, -1), "up": (0, 1, 0)},
            "back":      {"sight": (0, 0, 1),  "up": (0, 1, 0)},
            "top":       {"sight": (0, -1, 0), "up": (0, 0, -1)},
            "bottom":    {"sight": (0, 1, 0),  "up": (0, 0, 1)},
            "left":      {"sight": (1, 0, 0),  "up": (0, 1, 0)},
            "right":     {"sight": (-1, 0, 0), "up": (0, 1, 0)},
            "isometric": {"sight": (-1, -1, -1), "up": (0, 1, 0)},
        }

        if view not in views:
            raise ValueError(f"Unknown view: '{view}'")

        v = views[view]
        sight = v["sight"]
        up = v["up"]

        try:
            viewpoint.PutSightDirection(list(sight))
            viewpoint.PutUpDirection(list(up))
            viewer.Reframe()
        except Exception as e:
            raise RuntimeError(format_catia_error("SetView", e))

        return f"View set to: {view}"

    def _fit_all(self) -> str:
        self.conn.ensure_connected()
        viewer = self.conn._safe_active_viewer()
        if viewer is None:
            raise RuntimeError("No active 3D viewer available. Make sure a Part or Product document is open.")
        try:
            viewer.Reframe()
        except Exception as e:
            raise RuntimeError(format_catia_error("Reframe", e))
        return "View fitted to all geometry"
