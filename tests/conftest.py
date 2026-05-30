"""Shared conftest for catia_mcp tests.

Injects pywin32 mocks BEFORE any catia_mcp module is imported,
so HAS_COM is True and tests run on any OS without CATIA.
"""

import sys
from unittest.mock import MagicMock


def _install_com_mocks():
    """Mock pywin32 and force catia_mcp.connection to reimport."""
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
    # Make Dispatch() return its argument unchanged (pass-through for late binding)
    mock_win32com.client.dynamic.Dispatch.side_effect = lambda obj: obj
    # Only set EnsureDispatch mock on FIRST install (not on pytest_runtest_setup retries)
    # Connection tests override this per-test and we must not clobber their overrides
    if not getattr(mock_win32com.client.gencache.EnsureDispatch, '_conftest_mocked', False):
        def _mock_ensure_dispatch(obj_or_progid):
            if isinstance(obj_or_progid, str):
                raise RuntimeError("ProgID not available in test environment")
            return obj_or_progid
        mock_win32com.client.gencache.EnsureDispatch.side_effect = _mock_ensure_dispatch
        mock_win32com.client.gencache.EnsureDispatch._conftest_mocked = True

    sys.modules["pythoncom"] = mock_pythoncom
    sys.modules["win32com"] = mock_win32com
    sys.modules["win32com.client"] = mock_win32com.client
    sys.modules["win32com.client.dynamic"] = mock_win32com.client.dynamic

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
