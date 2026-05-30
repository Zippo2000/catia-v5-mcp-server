"""Tests for catia_mcp.utils — input validation and error formatting.

NOTE: utils.py does NOT import pywin32, so no COM mocking needed.
"""

from catia_mcp.utils import (
    format_catia_error,
    validate_file_path,
    validate_non_negative_float,
    validate_plane,
    validate_positive_float,
    validate_positive_int,
    validate_sketch_name,
)


class TestValidatePositiveFloat:
    def test_valid_float(self):
        assert validate_positive_float(5.0, "x") == 5.0

    def test_valid_int(self):
        assert validate_positive_float(10, "x") == 10.0

    def test_zero_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(0, "height")

    def test_negative_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(-1.0, "height")

    def test_string_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a number"):
            validate_positive_float("abc", "height")

    def test_none_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a number"):
            validate_positive_float(None, "height")


class TestValidateNonNegativeFloat:
    def test_zero(self):
        assert validate_non_negative_float(0.0, "a") == 0.0

    def test_positive(self):
        assert validate_non_negative_float(5.5, "a") == 5.5

    def test_negative_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be non-negative"):
            validate_non_negative_float(-1.0, "a")

    def test_string_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a number"):
            validate_non_negative_float("bad", "a")


class TestValidatePositiveInt:
    def test_valid(self):
        assert validate_positive_int(1, "c") == 1

    def test_zero_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(0, "c")

    def test_negative_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(-5, "c")

    def test_float_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be an integer"):
            validate_positive_int(3.5, "c")


class TestValidateFilePath:
    def test_absolute_forward(self):
        assert validate_file_path("C:/test/part.CATPart", "path") == "C:/test/part.CATPart"

    def test_absolute_backslash(self):
        assert validate_file_path("C:\\test\\part.CATPart", "path") == "C:\\test\\part.CATPart"

    def test_unix_absolute(self):
        result = validate_file_path("/home/test/part.CATPart", "path")
        assert result == "/home/test/part.CATPart"

    def test_empty_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must not be empty"):
            validate_file_path("", "path")

    def test_whitespace_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must not be empty"):
            validate_file_path("   ", "path")

    def test_non_string_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a string"):
            validate_file_path(123, "path")

    def test_relative_raises(self):
        import pytest
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            validate_file_path("relative_file.txt", "path")


class TestValidatePlane:
    def test_xy(self):
        assert validate_plane("xy") == "xy"

    def test_xy_upper(self):
        assert validate_plane("XY") == "xy"

    def test_yz(self):
        assert validate_plane("yz") == "yz"

    def test_zx(self):
        assert validate_plane("zx") == "zx"

    def test_xz_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Must be one of"):
            validate_plane("xz")

    def test_front_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Must be one of"):
            validate_plane("front")

    def test_non_string_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a string"):
            validate_plane(123)


class TestValidateSketchName:
    def test_none(self):
        assert validate_sketch_name(None) is None

    def test_valid(self):
        assert validate_sketch_name("Sketch.1") == "Sketch.1"

    def test_empty_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must not be empty"):
            validate_sketch_name("")

    def test_non_string_raises(self):
        import pytest
        with pytest.raises(ValueError, match="must be a string"):
            validate_sketch_name(123)


class TestFormatCatiaError:
    def test_normal(self):
        result = format_catia_error("AddNewPad", Exception("bad sketch"))
        assert "AddNewPad" in result
        assert "bad sketch" in result
        assert "modal dialog" in result

    def test_none_error(self):
        result = format_catia_error("GetCOG", Exception(None))
        assert "Unknown CATIA COM error" in result

    def test_empty_error(self):
        result = format_catia_error("Op", Exception(""))
        assert "Unknown CATIA COM error" in result
