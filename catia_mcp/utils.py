"""Common utilities shared across CATIA V5 MCP tool modules.

Input validation, error formatting, and COM helper functions.
"""

from __future__ import annotations

import re
from typing import Any


def validate_positive_float(value: Any, name: str) -> float:
    """Validate that a numeric value is a positive float.

    Raises ValueError with a helpful message if not.
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"'{name}' must be a number, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"'{name}' must be positive, got {value}")
    return float(value)


def validate_non_negative_float(value: Any, name: str) -> float:
    """Validate that a numeric value is a non-negative float.

    Raises ValueError with a helpful message if not.
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"'{name}' must be a number, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"'{name}' must be non-negative, got {value}")
    return float(value)


def validate_positive_int(value: Any, name: str) -> int:
    """Validate that a numeric value is a positive integer.

    Raises ValueError with a helpful message if not.
    """
    if not isinstance(value, int):
        raise ValueError(f"'{name}' must be an integer, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"'{name}' must be positive, got {value}")
    return value


def validate_file_path(value: Any, name: str) -> str:
    """Validate that a file path is a non-empty string.

    Raises ValueError with a helpful message if not.
    """
    if not isinstance(value, str):
        raise ValueError(f"'{name}' must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"'{name}' must not be empty")
    # Normalize path separators (accept both / and \)
    normalized = value.replace("\\", "/")
    # Check for obvious issues
    if not re.match(r"^[A-Za-z]:/", normalized) and not normalized.startswith("/"):
        raise ValueError(
            f"'{name}' does not appear to be a valid file path: '{value}'\n"
            "On Windows, use a full path like 'C:/path/to/file.CATPart'"
        )
    return value


def validate_plane(value: Any) -> str:
    """Validate a plane name (xy, yz, or zx).

    Raises ValueError if not a valid plane.
    """
    if not isinstance(value, str):
        raise ValueError(f"Plane must be a string, got {type(value).__name__}")
    plane = value.lower().strip()
    if plane not in ("xy", "yz", "zx"):
        raise ValueError(
            f"Invalid plane '{value}'. Must be one of: 'xy', 'yz', 'zx'"
        )
    return plane


def validate_sketch_name(value: Any | None) -> str | None:
    """Validate an optional sketch name.

    Returns the name or None. Raises ValueError if provided but empty.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Sketch name must be a string")
    if not value.strip():
        raise ValueError("Sketch name must not be empty")
    return value


def format_catia_error(op: str, e: Exception) -> str:
    """Format a CATIA COM error into a helpful message.

    Adds context about the operation, backend, and suggests common fixes.
    """
    error_str = str(e)
    if not error_str or error_str == "None":
        error_str = "Unknown CATIA COM error (no error message from CATIA)"

    # Detect if pycatia is involved
    is_pycatia = any(m in error_str.lower() for m in ['pycatia', 'catia_interface'])

    hints = (
        "  • CATIA may have a modal dialog open blocking automation\n"
        "  • The document may be in an invalid state (close and reopen)\n"
        "  • Try running catia_update_part to rebuild before retrying"
    )
    if is_pycatia:
        hints += "\n  • pycatia backend error — try catia_disconnect then catia_connect"

    return (
        f"CATIA operation '{op}' failed: {error_str}\n"
        "Common causes:\n"
        f"{hints}"
    )