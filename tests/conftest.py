"""Shared conftest for catia_mcp tests.

Injects pywin32 mocks BEFORE any catia_mcp module is imported,
so HAS_COM is True and tests run on any OS without CATIA.
"""

import sys
from unittest.mock import MagicMock


def _install_com_mocks():
    """Mock pywin32 and force catia_mcp.connection to reimport.

    Preserves any existing side_effect on EnsureDispatch and GetActiveObject
    set by individual tests, so that per-test mock overrides survive
    pytest_runtest_setup module teardown.
    """
    # Save existing mock overrides before clearing modules
    saved_ensure_dispatch = None
    saved_get_active_object = None
    if "win32com.client" in sys.modules:
        _gencache = getattr(sys.modules["win32com.client"], "gencache", None)
        if _gencache is not None:
            _ed = getattr(_gencache, "EnsureDispatch", None)
            if _ed is not None and hasattr(_ed, "side_effect") and _ed.side_effect is not None:
                saved_ensure_dispatch = _ed.side_effect
        _gad = getattr(sys.modules["win32com.client"], "GetActiveObject", None)
        if _gad is not None and hasattr(_gad, "side_effect") and _gad.side_effect is not None:
            saved_get_active_object = _gad.side_effect

    # Clear any prior catia_mcp imports
    for mod in list(sys.modules.keys()):
        if mod.startswith("catia_mcp"):
            del sys.modules[mod]

    # Install mocks
    mock_pythoncom = MagicMock()
    mock_win32com = MagicMock()
    mock_win32com.client = MagicMock()
    mock_win32com.client.gencache = MagicMock()
    mock_win32com.client.dynamic = MagicMock()
    # Make Dispatch() and CDispatch() return their argument unchanged (pass-through for late binding)
    mock_win32com.client.dynamic.Dispatch.side_effect = lambda obj: obj
    mock_win32com.client.dynamic.CDispatch.side_effect = lambda obj, olerepr=None: obj

    # Restore saved overrides or set defaults
    if saved_ensure_dispatch is not None:
        mock_win32com.client.gencache.EnsureDispatch.side_effect = saved_ensure_dispatch
    else:
        def _mock_ensure_dispatch(obj_or_progid):
            if isinstance(obj_or_progid, str):
                raise RuntimeError("ProgID not available in test environment")
            return obj_or_progid
        mock_win32com.client.gencache.EnsureDispatch.side_effect = _mock_ensure_dispatch

    if saved_get_active_object is not None:
        mock_win32com.client.GetActiveObject.side_effect = saved_get_active_object

    sys.modules["pythoncom"] = mock_pythoncom
    sys.modules["win32com"] = mock_win32com
    sys.modules["win32com.client"] = mock_win32com.client
    sys.modules["win32com.client.dynamic"] = mock_win32com.client.dynamic

    # Mock pycatia modules (so HAS_PYCATIA is True in tests)
    mock_pycatia = MagicMock()
    mock_pycatia.CATIA = MagicMock()
    mock_pycatia.part_interfaces = MagicMock()
    mock_pycatia.part_interfaces.Part = MagicMock()
    mock_pycatia.product_structure_interfaces = MagicMock()
    mock_pycatia.product_structure_interfaces.Product = MagicMock()
    mock_pycatia.hybrid_shape_interfaces = MagicMock()
    mock_pycatia.hybrid_shape_interfaces.HybridShapeFactory = MagicMock()
    mock_pycatia.in_interfaces = MagicMock()
    mock_pycatia.hydro_shape_interfaces = MagicMock()
    sys.modules["pycatia"] = mock_pycatia
    sys.modules["pycatia.part_interfaces"] = mock_pycatia.part_interfaces
    sys.modules["pycatia.product_structure_interfaces"] = mock_pycatia.product_structure_interfaces
    sys.modules["pycatia.hybrid_shape_interfaces"] = mock_pycatia.hybrid_shape_interfaces
    sys.modules["pycatia.in_interfaces"] = mock_pycatia.in_interfaces
    sys.modules["pycatia.hydro_shape_interfaces"] = mock_pycatia.hydro_shape_interfaces

    # Now import connection so HAS_COM is True
    from catia_mcp.connection import HAS_COM
    assert HAS_COM is True, "COM mocks were not installed correctly"

    return mock_pythoncom, mock_win32com


# Install mocks at import time (conftest is loaded by pytest before test modules)
_mock_pythoncom, _mock_win32com = _install_com_mocks()


def pytest_configure(config):
    """Ensure COM mocks are active for all tests."""
    pass


def pytest_runtest_setup(item):
    """Before each test, ensure COM mocks are still in place.

    IMPORTANT: Only reinstall if sys.modules was cleared (e.g., by a test).
    Do NOT reinstall normally — connection tests set their own EnsureDispatch
    behavior that must survive test boundaries.
    The _install_com_mocks() function now preserves existing side_effect
    overrides, so repeated calls are safe.
    """
    if "pythoncom" not in sys.modules:
        # Full reinstall needed — modules were cleared
        _install_com_mocks()
    elif "catia_mcp.connection" in sys.modules:
        # Modules still exist but catia_mcp modules may need refresh
        # Only refresh non-test modules, preserving per-test mock overrides
        for mod in list(sys.modules.keys()):
            if mod.startswith("catia_mcp") and "test_" not in mod:
                del sys.modules[mod]
