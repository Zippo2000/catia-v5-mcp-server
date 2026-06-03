"""Test entry point configuration and build metadata."""

import pathlib
import tomllib


class TestEntryPoints:
    def test_pyproject_build_backend(self):
        pyproject = pathlib.Path(__file__).parent.parent / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text())
        assert data["build-system"]["build-backend"] == "setuptools.build_meta"

    def test_console_scripts_defined(self):
        pyproject = pathlib.Path(__file__).parent.parent / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text())
        scripts = data.get("project", {}).get("scripts", {})
        assert "catia-mcp" in scripts
        assert "catia_mcp.server:main" in scripts["catia-mcp"]

    def test_main_guard_exists(self):
        main_file = pathlib.Path(__file__).parent.parent / "catia_mcp" / "__main__.py"
        content = main_file.read_text()
        assert "__name__" in content
        assert "__main__" in content

    def test_all_tool_modules_import(self):
        """All tool modules should import without error."""
        from catia_mcp.tools.part_design import PartDesignTools
        from catia_mcp.tools.sketcher import SketcherTools
        from catia_mcp.tools.document import DocumentTools
        from catia_mcp.tools.assembly import AssemblyTools
        from catia_mcp.tools.measurement import MeasurementTools
        from catia_mcp.tools.export import ExportTools
        from catia_mcp.tools.gsd import GSDTools
        assert PartDesignTools is not None
        assert SketcherTools is not None
        assert DocumentTools is not None
        assert AssemblyTools is not None
        assert MeasurementTools is not None
        assert ExportTools is not None
        assert GSDTools is not None
