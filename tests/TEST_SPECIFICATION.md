# CATIA V5 MCP Server — Test Specification

> Created: 2026-05-30  
> Target: `phase1-bugfixes` branch (Phases 1-3 applied)  
> CATIA API Reference: [PartInterfaces.ShapeFactory](https://catiadesign.org/_doc/V5Automation/generated/interfaces/PartInterfaces/interface_ShapeFactory_20269.htm), [Measurable](https://catiadesign.org/_doc/V5Automation/generated/interfaces/_index/CAAMasterIdx.htm)

---

## 1. Test Strategy

| Category | Approach | Runs on real CATIA? |
|---|---|---|
| **Unit Tests** (utils, connection mocking) | `pytest` + `unittest.mock` | ❌ No |
| **Integration Tests** (tool execute flow) | `pytest` + real CATIA COM | ⚠️ Optional (skipped if CATIA unavailable) |
| **Smoke Tests** (import, server init) | `pytest` — no CATIA needed | ❌ No |

Since CATIA V5 requires Windows + licensed software, we design tests that:
1. **Always pass** on non-Windows / no-CATIA (unit tests with mocks)
2. **Run integration tests** only when `CATIA_TEST_LIVE=1` is set
3. **Mock all COM interactions** for reliable CI

---

## 2. Test Cases — `catia_mcp/utils.py` (Unit Tests)

### UT-01: `validate_positive_float`
| ID | Input | Expected |
|---|---|---|
| UT-01a | `5.0, "radius"` | Returns `5.0` |
| UT-01b | `0, "height"` | Raises `ValueError` |
| UT-01c | `-1.0, "depth"` | Raises `ValueError` |
| UT-01d | `"abc", "width"` | Raises `ValueError` |
| UT-01e | `None, "length"` | Raises `ValueError` |
| UT-01f | `int(10), "count"` | Returns `10.0` (int is valid) |

### UT-02: `validate_non_negative_float`
| ID | Input | Expected |
|---|---|---|
| UT-02a | `0.0, "angle"` | Returns `0.0` |
| UT-02b | `5.5, "offset"` | Returns `5.5` |
| UT-02c | `-1.0, "x"` | Raises `ValueError` |
| UT-02d | `"bad", "y"` | Raises `ValueError` |

### UT-03: `validate_positive_int`
| ID | Input | Expected |
|---|---|---|
| UT-03a | `1, "count"` | Returns `1` |
| UT-03b | `0, "count"` | Raises `ValueError` |
| UT-03c | `-5, "count"` | Raises `ValueError` |
| UT-03d | `3.5, "count"` | Raises `ValueError` |

### UT-04: `validate_file_path`
| ID | Input | Expected |
|---|---|---|
| UT-04a | `"C:/test/part.CATPart"` | Returns as-is |
| UT-04b | `"C:\\test\\part.CATPart"` | Returns as-is |
| UT-04c | `"", "path"` | Raises `ValueError` |
| UT-04d | `"relative_file.txt", "path"` | Raises `ValueError` |
| UT-04e | `123, "path"` | Raises `ValueError` |

### UT-05: `validate_plane`
| ID | Input | Expected |
|---|---|---|
| UT-05a | `"xy"` | Returns `"xy"` |
| UT-05b | `"XY"` | Returns `"xy"` |
| UT-05c | `"yz"` | Returns `"yz"` |
| UT-05c | `"zx"` | Returns `"zx"` |
| UT-05d | `"xz"` | Raises `ValueError` |
| UT-05e | `"front"` | Raises `ValueError` |

### UT-06: `validate_sketch_name`
| ID | Input | Expected |
|---|---|---|
| UT-06a | `None` | Returns `None` |
| UT-06b | `"Sketch.1"` | Returns `"Sketch.1"` |
| UT-06c | `""` | Raises `ValueError` |
| UT-06d | `123` | Raises `ValueError` |

### UT-07: `format_catia_error`
| ID | Input | Expected |
|---|---|---|
| UT-07a | `("AddNewPad", Exception("bad sketch"))` | Returns string containing "AddNewPad", "bad sketch" |
| UT-07b | `("GetCOG", Exception(None))` | Returns string (no crash on None) |

---

## 3. Test Cases — `catia_mcp/connection.py` (Mocked Unit Tests)

### UC-01: `CATIAConnection` initialization
| ID | Test | Expected |
|---|---|---|
| UC-01a | `conn = CATIAConnection()` | `is_connected` is `False`, `_launched_instance` is `False` |
| UC-01b | `_locked` flag | Default `False` |

### UC-02: `_normalize_path`
| ID | Input | Expected |
|---|---|---|
| UC-02a | `"/home/test/file.txt"` | `"\\home\\test\\file.txt"` |
| UC-02b | `"C:/Users/test/file.CATPart"` | `"C:\Users\test\file.CATPart"` |
| UC-02c | `"C:\\Users\\test\\"` | `"C:\Users\test"` (trailing slash removed) |
| UC-02d | `123` | Returns `123` (non-string passthrough) |

### UC-03: `is_connected` property
| ID | Setup | Expected |
|---|---|---|
| UC-03a | `app = None` | `False` |
| UC-03b | `app` mock, `Caption` raises | `False` + `app` set to `None` |
| UC-03c | `app` mock, `Caption` returns `"CATIA V5"` | `True` |

### UC-04: `connect()` with mock
| ID | Setup | Expected |
|---|---|---|
| UC-04a | Already connected | Returns "Already connected..." |
| UC-04b | `_locked = True` | Raises `RuntimeError` |
| UC-04c | `GetActiveObject` succeeds | Returns "Connected to running..." |
| UC-04d | `GetActiveObject` fails, `Dispatch` succeeds | Returns "Launched new...", `_launched_instance = True` |
| UC-04e | Both fail | Raises `RuntimeError` |
| UC-04f | After failure | `_locked` is `False` (always released) |

### UC-05: `disconnect()`
| ID | Test | Expected |
|---|---|---|
| UC-05a | Normal disconnect | `app = None`, `_initialized_com = False`, `_launched_instance = False` |

### UC-06: `close()`
| ID | Setup | Expected |
|---|---|---|
| UC-06a | Not connected | Returns "Not connected..." |
| UC-06b | Connected, 2 docs open | Closes both docs, calls `app.Quit()`, disconnects |

### UC-07: `reconnect()`
| ID | Setup | Expected |
|---|---|---|
| UC-07a | `GetActiveObject` succeeds | Returns "Reconnected..." |
| UC-07b | `GetActiveObject` fails, `Dispatch` succeeds | Returns "Launched new..." |

### UC-08: `ensure_connected()`
| ID | Setup | Expected |
|---|---|---|
| UC-08a | Already connected | No-op |
| UC-08b | Not connected, `reconnect()` works | Reconnects |
| UC-08c | Not connected, `reconnect()` fails, `connect()` works | Connects |

---

## 4. Test Cases — Tool Module Input Validation (Mocked)

### UPT-01: `DocumentTools._open_document()`
| ID | Input | Expected |
|---|---|---|
| UPT-01a | Valid path `"C:/test.part"` | Calls `docs.Open()` with normalized path |
| UPT-01b | Empty path `""` | Raises `ValueError` |
| UPT-01c | Relative path `"test.part"` | Raises `ValueError` |

### UPT-02: `DocumentTools._save_document()`
| ID | Input | Expected |
|---|---|---|
| UPT-02a | No path | Calls `doc.Save()` |
| UPT-02b | Valid path | Calls `doc.SaveAs()` with normalized path |
| UPT-02c | Relative path | Raises `ValueError` |

### UPT-03: `PartDesignTools._pad()`
| ID | Input | Expected |
|---|---|---|
| UPT-03a | `height=-5` | Raises `ValueError` ("height must be positive") |
| UPT-03b | `height=0` | Raises `ValueError` |
| UPT-03c | `sketch_name=""` | Raises `ValueError` |
| UPT-03d | `direction="invalid"` | Uses input as-is (enum enforced by MCP schema) |

### UPT-04: `PartDesignTools._pocket()`
| ID | Input | Expected |
|---|---|---|
| UPT-04a | `depth=-10` | Raises `ValueError` |

### UPT-05: `PartDesignTools._fillet()`
| ID | Input | Expected |
|---|---|---|
| UPT-05a | `radius=0` | Raises `ValueError` |
| UPT-05b | `radius=-5` | Raises `ValueError` |

### UPT-06: `PartDesignTools._chamfer()`
| ID | Input | Expected |
|---|---|---|
| UPT-06a | `length=-1` | Raises `ValueError` |
| UPT-06b | `angle=-45` | Raises `ValueError` |

### UPT-07: `PartDesignTools._hole()`
| ID | Input | Expected |
|---|---|---|
| UPT-07a | `diameter=0` | Raises `ValueError` |
| UPT-07b | `depth=-1` | Raises `ValueError` |

### UPT-08: `PartDesignTools._mirror()`
| ID | Input | Expected |
|---|---|---|
| UPT-08a | `plane="xy"` | Valid |
| UPT-08b | `plane="front"` | Raises `ValueError` |

### UPT-09: `PartDesignTools._rect_pattern()`
| ID | Input | Expected |
|---|---|---|
| UPT-09a | `dir1_count=0` | Raises `ValueError` |
| UPT-09b | `dir1_count=-1` | Raises `ValueError` |
| UPT-09c | `dir1_spacing=0` | Raises `ValueError` |

### UPT-10: `PartDesignTools._circ_pattern()`
| ID | Input | Expected |
|---|---|---|
| UPT-10a | `count=0` | Raises `ValueError` |

### UPT-11: `SketcherTools._create_sketch()`
| ID | Input | Expected |
|---|---|---|
| UPT-11a | `plane="xy"` | Valid |
| UPT-11b | `plane="front"` | Raises `ValueError` |

### UPT-12: `SketcherTools._draw_circle()`
| ID | Input | Expected |
|---|---|---|
| UPT-12a | `radius=0` | Raises `ValueError` |
| UPT-12b | `radius=-5` | Raises `ValueError` |

### UPT-13: `SketcherTools._draw_centered_rectangle()`
| ID | Input | Expected |
|---|---|---|
| UPT-13a | `width=0` | Raises `ValueError` |
| UPT-13b | `height=-10` | Raises `ValueError` |

### UPT-14: `SketcherTools._draw_spline()`
| ID | Input | Expected |
|---|---|---|
| UPT-14a | `points=[]` | Raises `ValueError` (< 2 points) |
| UPT-14b | `points=[[0,0]]` | Raises `ValueError` (< 2 points) |
| UPT-14c | `points=[[0,0],[1,1]]` | Valid |

### UPT-15: `AssemblyTools._add_component()`
| ID | Input | Expected |
|---|---|---|
| UPT-15a | Valid path | Calls with normalized path |
| UPT-15b | Relative path | Raises `ValueError` |

### UPT-16: `AssemblyTools._fix_constraint()`
| ID | Input | Expected |
|---|---|---|
| UPT-16a | Non-existent component | Raises `ValueError` ("not found") |

### UPT-17: `AssemblyTools._move_component()`
| ID | Input | Expected |
|---|---|---|
| UPT-17a | Non-existent component | Raises `ValueError` ("not found") |

### UPT-18: `ExportTools._export()`
| ID | Input | Expected |
|---|---|---|
| UPT-18a | Valid path + format | Normalizes path, calls `ExportData()` |
| UPT-18b | Invalid format | Raises `ValueError` |
| UPT-18c | Relative path | Raises `ValueError` |

### UPT-19: `ExportTools._screenshot()`
| ID | Input | Expected |
|---|---|---|
| UPT-19a | `width=0` | Raises `ValueError` |
| UPT-19b | `height=-1` | Raises `ValueError` |

### UPT-20: `MeasurementTools._measure_distance()`
| ID | Input | Expected |
|---|---|---|
| UPT-20a | Both elements exist | Returns distance string |
| UPT-20b | Element 1 not found | Raises `RuntimeError` |
| UPT-20c | SPAWorkbench fails | Raises `RuntimeError` with formatted error |

### UPT-21: `MeasurementTools._get_inertia()`
| ID | Input | Expected |
|---|---|---|
| UPT-21a | `density=-1` | Raises `ValueError` |
| UPT-21b | `density=7800` | Valid |

### UPT-22: `MeasurementTools._set_parameter()`
| ID | Input | Expected |
|---|---|---|
| UPT-22a | Non-existent parameter | Raises `ValueError` ("not found") |

---

## 5. Test Cases — Server / Integration

### US-01: Tool routing
| ID | Test | Expected |
|---|---|---|
| US-01a | All tools registered | 50+ tools in `_tool_router` |
| US-01b | Unknown tool | Returns error message |
| US-01c | `catia_close` not auto-connected | Does NOT call `connect()` before executing |

### US-02: `catia_close` in tool definitions
| ID | Test | Expected |
|---|---|---|
| US-02a | `catia_close` present | Found in `document_tools.get_tool_definitions()` |
| US-02b | `catia_close` routed correctly | Routes to `conn.close()` |

### US-03: COM error handling
| ID | Setup | Expected |
|---|---|---|
| US-03a | `AddNewPad` raises COMException | Returns formatted error with troubleshooting hints |
| US-03b | `GetActiveObject` raises | Returns error without crashing |

---

## 6. Test Cases — Error Messages

### UEM-01: Error message content
| ID | Error | Must Contain |
|---|---|---|
| UEM-01a | `format_catia_error("Pad", ...)` | "AddNewPad", "modal dialog", "reconnect" |
| UEM-01b | Negative dimension | "must be positive" |
| UEM-01c | Invalid plane | "must be one of: 'xy', 'yz', 'zx'" |
| UEM-01d | Missing component | "'<name>' not found" |

---

## 7. Test Cases — `__main__.py` / Entry Point

### UEM-01: Entry point
| ID | Test | Expected |
|---|---|---|
| EM-01a | `if __name__ == "__main__"` guard | Present in `__main__.py` |
| EM-01b | `python -m catia_mcp` import path | `server:main` in `console_scripts` |

---

## 8. Test Cases — `pyproject.toml`

### EP-01: Build config
| ID | Test | Expected |
|---|---|---|
| EP-01a | `build-backend` | `"setuptools.build_meta"` (not legacy) |
| EP-01b | `requires-python` | `>=3.10` |
| EP-01c | Dependencies | `mcp`, `pywin32` present |

---

## 9. Test Execution Matrix

| Test File | Tests | CATIA Required? | Est. Time |
|---|---|---|---|
| `test_utils.py` | 25 | ❌ | 1s |
| `test_connection.py` | 20 | ❌ (mocked) | 1s |
| `test_document_tools.py` | 8 | ❌ (mocked) | 1s |
| `test_part_design_tools.py` | 20 | ❌ (mocked) | 1s |
| `test_sketcher_tools.py` | 12 | ❌ (mocked) | 1s |
| `test_assembly_tools.py` | 8 | ❌ (mocked) | 1s |
| `test_measurement_tools.py` | 10 | ❌ (mocked) | 1s |
| `test_export_tools.py` | 8 | ❌ (mocked) | 1s |
| `test_server.py` | 5 | ❌ (mocked) | 1s |
| `test_entry_points.py` | 5 | ❌ | 1s |
| **Total** | **~122** | **All mockable** | **~10s** |
