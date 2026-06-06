# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.11.0] - 2026-06-06

### Added
- **Part Design Phase 2 Tools** — 5 new tools:
  - `catia_variable_fillet` — Variable-radius fillet transitioning between two radii along an edge
  - `catia_drafted_filleted_pad` — Pad with integrated draft angle and bottom fillet in a single operation
  - `catia_drafted_filleted_pocket` — Pocket with integrated draft angle and bottom fillet in a single operation
  - `catia_multi_pad` — Create multiple pads from multiple sketches in one operation
  - `catia_multi_pocket` — Create multiple pockets from multiple sketches in one operation
- **Tool Count** — 111 → 116 tools (Part Design: 23 → 28)

### Changed
- **Version** — 1.10.0 → 1.11.0
- **Part Design Module** — Added 5 advanced composite features for mold-design and multi-feature workflows

---

## [Unreleased]

### Added
- **GSD Surface Manipulation** — 4 new tools: `catia_create_blend`, `catia_split_surface`, `catia_extend_surface`, `catia_trim_surface`
- **GSD Advanced Primitives** — 4 new tools: `catia_create_sphere`, `catia_create_cone`, `catia_create_torus`, `catia_create_ruled`
- **GSD Module** — 24 tools total covering wireframe (point, line, circle, plane, cylinder) and surface design (fill, sweep, join, offset, thicken, multi-section)
- **Part Design Extensions** — 4 new tools: `catia_lifting`, `catia_sweep`, `catia_loft`, `catia_boolean`
- **Sketcher Conics** — 3 new tools: `catia_sketch_ellipse`, `catia_sketch_hyperbola`, `catia_sketch_parabola`
- **Assembly Advanced Constraints** — 3 new tools: `catia_contact_constraint`, `catia_distance_constraint`, `catia_tangent_constraint`
- **Assembly Management** — 2 new tools: `catia_remove_component`, `catia_remove_constraint`
- **Measurement Extensions** — 4 new tools: `catia_measure_angle`, `catia_measure_area`, `catia_measure_length`, `catia_measure_interference`
- **Streamable HTTP Transport** — Third transport mode alongside stdio and SSE, using `StreamableHTTPSessionManager` with lifespan session management
- **pycatia Dependency** — Added `pycatia>=0.9.0` as optional dual-backend alongside win32com

### Changed
- **Tool Count** — 55 → 95 tools across 7 modules
- **Test Count** — 154 → 256 pytest tests
- **GSD Coverage** — 0 → 24 tools (67% of tracked GSD API areas)
- **SSE Default Port** — 3000 → 8765
- **Requirements Doc** — Updated to v1.8, added FR-10 (GSD), updated all module counts
- **Gap Analysis** — Updated to v1.2, reflected completed GSD, Part Design, Sketcher and Assembly features

### Fixed
- **COM Proxy Crashes** — Resolved gencache vs dynamic.Dispatch inconsistency causing intermittent crashes on `.Part`/`.Product` access
- **CreateReference Ambiguity** — Split into `CreateReferenceFromGeometry` (HybridShapes) and `CreateReferenceFromObject` (OriginElements)
- **GSD API Method Names** — Corrected all method names against official CATIA V5 documentation
- **Cylinder Creation** — Fixed direction parameter to use `HybridShapeDirection` via `AddNewDirection`
- **Torus Creation** — Fixed angle conversion to radians, uses infinite axis line for `AddNewRevol`
- **Cone/Sphere Angle Conversion** — Fixed degree-to-radian conversion for `AddNewRevol` and `AddNewSphere`
- **Windows stdio** — Fixed signal handler compatibility and SSE `ClosedResourceError`
- **Sketcher pycatia Support** — Added `_is_pycatia()` helper for `OpenEdition`/`CloseEdition`
- **Part Design Dual-Backend** — All 19 part design methods now support pycatia with win32com fallback
- **HSO Pollution** — Added `finally: hso.Clear()` in `_resolve_geometry()` and `_shell()`
- **Fillet/Chamfer edge_name** — Fixed to actually use the `edge_name` argument when provided
- **Server Debug Logging** — Removed `inspect.getsource()` debug checks from all transport runners
- **Test Mock Isolation** — Rewrote `_install_com_mocks()` to preserve per-test `EnsureDispatch`/`GetActiveObject` overrides
- **Geometrical Set Iteration** — Added try/except fallback for win32com `HybridBodies` iteration

---

## [0.1.0] - 2026-05-29

### Added
- Initial release of CATIA V5 MCP Server
- **Document Management** — 10 tools: create, open, save, close, list parts and products
- **2D Sketching** — 14 tools: lines, rectangles, circles, arcs, splines, points, constraints
- **Part Design** — 28 tools: pad, pocket, shaft, groove, fillet, chamfer, hole, patterns, mirror, shell, draft, thickness, lifting, sweep, loft, boolean, rib, slot, stiffener, split body, variable fillet, drafted filleted pad/pocket, multi pad/pocket
- **Assembly** — 14 tools: add/remove components, fix/coincidence/offset/angle/contact/distance/tangent constraints, move, list
- **Measurement** — 10 tools: distance, inertia, bounding box, parameters, angle, area, length, interference, update
- **Export & View** — 4 tools: STEP/IGES/STL export, screenshots, view orientations
- **GSD (Wireframe & Surface)** — 24 tools: point, line, circle, plane, cylinder, fill, sweep, join, thicken, offset, multi-section, sphere, cone, torus, ruled, blend, split, extend, trim
- **Three Transport Modes** — stdio, SSE, Streamable HTTP
- **LM Studio Integration** — SSE transport guide for vLLM.rs, LM Studio, Open WebUI
- **Test Suite** — 256 pytest tests with mocked COM dependencies, runnable on Linux without CATIA
- **Documentation** — README, GAP_ANALYSIS (v1.2), REQUIREMENTS (v1.8)

---

## Known Issues

### BUG-001: Connection test mock side_effect / return_value conflict
- **Affected tests:** `test_dispatch_new_instance`, `test_get_active_object_success`, `test_reconnect_fallback` (3/256)
- **Ursache:** `conftest._install_com_mocks()` setzt `EnsureDispatch.side_effect` und `GetActiveObject.side_effect` auf Default-Funktionen. Individualle Tests überschreiben `return_value` (z.B. `EnsureDispatch.return_value = mock_app`), aber `side_effect` hat Vorrang vor `return_value` in `unittest.mock`. Die Default-`side_effect`-Funktion wirft `RuntimeError("ProgID not available...")` für string-Argumente, wodurch die `return_value`-Overrides der Tests ignoriert werden.
- **Status:** Offen. Lösung: Entweder Tests müssen `side_effect` statt `return_value` setzen, oder `_install_com_mocks()` muss `side_effect = None` verwenden und die Default-Logik in `return_value` + einen Wrapper-`side_effect` verlegen, der `return_value` respektiert.
- **Dateien:** `tests/conftest.py:46-53`, `tests/test_connection.py:105-131`

### BUG-002: pycatia mock aktiviert HAS_PYCATIA, führt zu pycatia-Code-Pfaden in Tests
- **Betroffen:** Potenziell alle Tools-Tests, falls `HAS_PYCATIA` nach pycatia-Mock-Installation `True` wird
- **Ursache:** `conftest._install_com_mocks()` injiziert `mock_pycatia` in `sys.modules["pycatia"]`. Wenn `catia_mcp.connection` neu importiert wird *nach* der Injektion, wird `HAS_PYCATIA` `True`. Da `HAS_PYCATIA` module-global ist und die Tools-Module es beim Import feststellen, hängt das Verhalten davon ab, *wann* die Tools-Module relativ zum pycatia-Mock importiert werden. In der aktuellen Test-Ausführung scheint `HAS_PYCATIA` `False` zu bleiben, da der connection-Import vor dem pycatia-Mock erfolgt.
- **Status:** Beobachten. Falls Tests beginnen, pycatia-Pfade zu nehmen, muss entweder `mock_pycatia` als `ImportError` konfiguriert werden oder `HAS_PYCATIA` explizit auf `False` gesetzt werden.
- **Dateien:** `tests/conftest.py:63-79`, `catia_mcp/connection.py:24-31`
