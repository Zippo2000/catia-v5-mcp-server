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
    """Before each test, ensure COM mocks are still in place."""
    if "pythoncom" not in sys.modules:
        _install_com_mocks()


def pytest_runtest_teardown(item):
    """After each test, re-inject mocks (some tests may delete sys.modules entries)."""
    _install_com_mocks()
