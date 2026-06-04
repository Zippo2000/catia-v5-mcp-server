"""CATIA V5 COM Connection Manager.

Manages the connection to CATIA V5 via Windows COM Automation API (win32com).
Supports connecting to a running instance or launching a new one.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("catia_mcp")

# COM imports are deferred to runtime (Windows only)
try:
    import pythoncom
    import win32com.client

    HAS_COM = True
except ImportError:
    HAS_COM = False

# pycatia import (optional, preferred backend)
try:
    import pycatia
    import pycatia.hydro_shape_interfaces
    import pycatia.part_interfaces
    import pycatia.in_interfaces
    HAS_PYCATIA = True
except ImportError:
    HAS_PYCATIA = False


def _normalize_path(path: str) -> str:
    """Normalize file paths for Windows CATIA.

    Converts forward slashes to backslashes and ensures the path
    is suitable for CATIA's COM API.
    """
    if not isinstance(path, str):
        return path
    # Normalize slashes to Windows format
    normalized = path.replace("/", "\\")
    # Remove trailing slashes
    normalized = normalized.rstrip("\\")
    return normalized


class CATIAConnection:
    """Manages connection to CATIA V5 via COM Automation."""

    # CATIA V5 COM ProgID
    CATIA_PROGID = "CATIA.Application"

    def __init__(self) -> None:
        self.app: Any | None = None
        self._initialized_com = False
        self._launched_instance = False  # Track if we launched CATIA ourselves
        self._locked = False             # Prevent double-connect race

    @property
    def is_connected(self) -> bool:
        """Check if we have an active CATIA connection."""
        if self.app is None:
            return False
        try:
            # Try accessing a property to verify the connection is alive
            _ = self.app.Caption
            return True
        except Exception:
            self.app = None
            return False

    def connect(self) -> str:
        """Connect to CATIA V5. Tries running instance first, then launches new one.

        Returns a status message string.
        """
        if not HAS_COM:
            raise RuntimeError(
                "pywin32 is not installed. Install it with: pip install pywin32\n"
                "Note: This MCP server requires Windows with CATIA V5 installed."
            )

        if self.is_connected:
            version = self._get_version()
            return f"Already connected to CATIA V5 ({version})"

        if self._locked:
            raise RuntimeError("Connection attempt already in progress. Please wait.")

        self._locked = True
        self._launched_instance = False
        try:
            # Initialize COM for this thread
            if not self._initialized_com:
                pythoncom.CoInitialize()
                self._initialized_com = True

            # Phase 1: Try to attach to a running CATIA instance
            try:
                raw_app = win32com.client.GetActiveObject(self.CATIA_PROGID)
                self.app = win32com.client.gencache.EnsureDispatch(raw_app)
                version = self._get_version()
                logger.info("Connected to running CATIA V5 instance (%s)", version)
                return f"Connected to running CATIA V5 instance ({version})"
            except Exception:
                logger.info("No running CATIA instance found, launching new one...")

            # Phase 2: Launch a new CATIA instance
            try:
                self.app = win32com.client.gencache.EnsureDispatch(self.CATIA_PROGID)
                self.app.Visible = True
                self._launched_instance = True
                version = self._get_version()
                logger.info("Launched new CATIA V5 instance (%s)", version)
                return f"Launched new CATIA V5 instance ({version})"
            except Exception as e:
                self.app = None
                raise RuntimeError(
                    f"Failed to connect to CATIA V5: {e}\n"
                    "Make sure CATIA V5 is installed and licensed on this machine."
                ) from e
        finally:
            self._locked = False

    def reconnect(self) -> str:
        """Try to reconnect to a running CATIA instance after a crash.

        First clears any stale references, then tries to attach again.
        Returns a status message string.
        """
        if not HAS_COM:
            raise RuntimeError(
                "pywin32 is not installed. Install it with: pip install pywin32"
            )

        # Release stale reference
        self.app = None

        # Ensure COM is initialized for this thread
        if not self._initialized_com:
            pythoncom.CoInitialize()
            self._initialized_com = True

        # Try to attach to a running CATIA instance
        try:
            self.app = win32com.client.GetActiveObject(self.CATIA_PROGID)
            version = self._get_version()
            logger.info("Reconnected to running CATIA V5 instance (%s)", version)
            return f"Reconnected to running CATIA V5 instance ({version})"
        except Exception:
            logger.info("No running CATIA instance found for reconnection")

        # Fallback: try launching a new one
        try:
            self.app = win32com.client.Dispatch(self.CATIA_PROGID)
            self.app.Visible = True
            version = self._get_version()
            logger.info("Launched new CATIA V5 instance after reconnect (%s)", version)
            return f"Launched new CATIA V5 instance ({version})"
        except Exception as e:
            self.app = None
            raise RuntimeError(
                f"Failed to reconnect to CATIA V5: {e}\n"
                "Start CATIA V5 manually and try again."
            ) from e

    def disconnect(self) -> str:
        """Disconnect from CATIA V5 (does not close CATIA).

        Releases COM references and uninitializes COM for this thread.
        """
        was_connected = self.is_connected
        if self.app is not None:
            try:
                # Release COM reference explicitly
                del self.app
            except Exception:
                pass
            self.app = None
        if self._initialized_com:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            self._initialized_com = False
        self._launched_instance = False
        self._locked = False
        return "Disconnected from CATIA V5"

    def close(self) -> str:
        """Gracefully close CATIA V5 entirely.

        Saves all open documents, then quits the CATIA application.
        Use this for a clean shutdown after finishing work.
        """
        if not self.is_connected:
            return "Not connected to CATIA V5"

        try:
            # Close all open documents without saving (user should save explicitly)
            docs = self.app.Documents
            while docs.Count > 0:
                try:
                    docs.Item(1).Close()
                except Exception:
                    break

            # Quit CATIA
            self.app.Quit()
            logger.info("CATIA V5 has been closed")
        except Exception as e:
            logger.warning("Error closing CATIA: %s", e)
        finally:
            self.disconnect()

        return "CATIA V5 has been closed"

    def ensure_connected(self) -> None:
        """Ensure we have an active CATIA connection, reconnecting if needed."""
        if not self.is_connected:
            # If we had a connection that's now stale, try to reconnect first
            try:
                self.reconnect()
            except Exception:
                # If reconnect fails, fall back to normal connect
                self.connect()

    def _get_version(self) -> str:
        """Get CATIA version string."""
        try:
            # CATIA V5 exposes SystemService.Environ or Caption
            caption = self.app.Caption
            return caption if caption else "unknown version"
        except Exception:
            return "unknown version"

    # ── Helper properties for quick access to CATIA objects ──

    @property
    def documents(self) -> Any:
        """Get the CATIA Documents collection."""
        self.ensure_connected()
        return self.app.Documents

    @property
    def active_document(self) -> Any:
        """Get the active CATIA document."""
        self.ensure_connected()
        try:
            return self.app.ActiveDocument
        except Exception:
            raise RuntimeError("No active document in CATIA. Create or open a document first.")

    @property
    def active_editor(self) -> Any | None:
        """Get the active editor, or None if no editor is available."""
        self.ensure_connected()
        try:
            return self.app.ActiveEditor
        except Exception:
            return None

    @property
    def hso(self) -> Any:
        """Get the Highlighted Set of Objects (selection)."""
        self.ensure_connected()
        return self.active_document.Selection

    def refresh_display(self) -> None:
        """Refresh the CATIA 3D view."""
        try:
            viewer = self._safe_active_viewer()
            if viewer is not None:
                viewer.Reframe()
        except Exception:
            pass

    def _safe_active_viewer(self) -> Any | None:
        """Get the active viewer safely, or None if unavailable."""
        try:
            editor = self.active_editor
            if editor is None:
                return None
            return getattr(editor, "ActiveViewer", None)
        except Exception:
            return None

    # ── Document type detection ──

    def get_active_part(self) -> Any:
        """Get the Part object from the active PartDocument.

        IMPORTANT: Returns dynamic.Dispatch(doc).Part to ensure .Part is accessible
        even when the gencache proxy for Document doesn't expose it.
        The returned Part is late-bound, so callers needing .HybridBodies iteration
        should use gsd._find_shape() which handles both proxy types.
        """
        doc = self.active_document
        import win32com.client.dynamic
        # Always use dynamic.Dispatch for .Part/.Product access —
        # gencache Document proxy doesn't expose these properties
        try:
            return win32com.client.dynamic.Dispatch(doc).Part
        except Exception:
            raise RuntimeError(
                "Active document is not a Part document. "
                "Open or create a Part document first."
            )

    def get_active_product(self) -> Any:
        """Get the Product object from the active ProductDocument."""
        doc = self.active_document
        try:
            return doc.Product
        except Exception:
            raise RuntimeError(
                "Active document is not a Product document. "
                "Open or create an Assembly (Product) document first."
            )

    def get_active_part_body(self) -> Any:
        """Get the main PartBody from the active Part document."""
        part = self.get_active_part()
        return part.MainBody

    def get_origin_elements(self) -> dict[str, Any]:
        """Get the origin planes (XY, YZ, ZX) from the active Part."""
        part = self.get_active_part()
        origin = part.OriginElements
        return {
            "xy": origin.PlaneXY,
            "yz": origin.PlaneYZ,
            "zx": origin.PlaneZX,
        }

    def normalize_path(self, path: str) -> str:
        """Normalize a file path for CATIA COM API (Windows).

        Converts forward slashes to backslashes, which CATIA expects.
        """
        return _normalize_path(path)

    # ── pycatia backend ──────────────────────────────────────────────────────

    def _get_pycatia(self) -> Any:
        """Get the pycatia CATIA application wrapper (lazy init)."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        if self.app is None:
            self.ensure_connected()
        import pycatia
        return pycatia.CATIA(self.app)

    def get_active_part_pycatia(self) -> Any:
        """Get the active part as a pycatia PartInterface."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        import pycatia
        catia = self._get_pycatia()
        return pycatia.part_interfaces.Part(catia.active_document.part)

    def get_active_product_pycatia(self) -> Any:
        """Get the active product as a pycatia ProductInterface."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        import pycatia
        catia = self._get_pycatia()
        return pycatia.product_structure_interfaces.Product(catia.active_document.product)

    def get_hsf_pycatia(self) -> Any:
        """Get the HybridShapeFactory via pycatia."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        part = self.get_active_part_pycatia()
        return part.hybrid_shape_factory

    def get_origin_elements_pycatia(self) -> Any:
        """Get OriginElements via pycatia."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        part = self.get_active_part_pycatia()
        return part.origin_elements

    def get_spa_workbench_pycatia(self) -> Any:
        """Get the SPA Workbench via pycatia (for measurable)."""
        if not HAS_PYCATIA:
            raise RuntimeError("pycatia is not installed")
        import pycatia
        catia = self._get_pycatia()
        return catia.get_workbench("SPAWorkbench")