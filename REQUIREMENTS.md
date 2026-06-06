# CATIA V5 MCP Server — Requirements Specification

| Field | Value |
|-------|-------|
| **Document ID** | REQ-001 |
| **Version** | 1.9 |
| **Status** | Active |
| **Date** | 2026-06-06 |
| **Basis** | catia-v5-mcp-server v1.11.0, 116 Tools, 7 Modules, 256 Tests |

---

## 1. Scope

This document specifies the functional and non-functional requirements for the CATIA V5 MCP Server.
It follows ASPICE-compliant structure with traceability to implementation.

---

## 2. Functional Requirements

### 2.1 Document Management (FR-001)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-001.1 | Connect to running CATIA V5 instance or launch new | `catia_connect` | ✅ Implemented |
| FR-001.2 | Disconnect from CATIA without closing | `catia_disconnect` | ✅ Implemented |
| FR-001.3 | Close CATIA entirely (all documents) | `catia_close` | ✅ Implemented |
| FR-001.4 | Create new Part document | `catia_new_part` | ✅ Implemented |
| FR-001.5 | Create new Product (assembly) document | `catia_new_product` | ✅ Implemented |
| FR-001.6 | Open existing CATIA document | `catia_open_document` | ✅ Implemented |
| FR-001.7 | Save active document | `catia_save_document` | ✅ Implemented |
| FR-001.8 | Close active document | `catia_close_document` | ✅ Implemented |
| FR-001.9 | List all open documents | `catia_list_documents` | ✅ Implemented |
| FR-001.10 | Get active document info | `catia_get_active_document_info` | ✅ Implemented |

### 2.2 2D Sketching (FR-002)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-002.1 | Create sketch on reference plane | `catia_create_sketch` | ✅ Implemented |
| FR-002.2 | Close sketch and return to Part Design | `catia_close_sketch` | ✅ Implemented |
| FR-002.3 | Draw line | `catia_sketch_line` | ✅ Implemented |
| FR-002.4 | Draw rectangle | `catia_sketch_rectangle` | ✅ Implemented |
| FR-002.5 | Draw centered rectangle | `catia_sketch_centered_rectangle` | ✅ Implemented |
| FR-002.6 | Draw circle | `catia_sketch_circle` | ✅ Implemented |
| FR-002.7 | Draw arc | `catia_sketch_arc` | ✅ Implemented |
| FR-002.8 | Draw ellipse | `catia_sketch_ellipse` | ✅ Implemented |
| FR-002.9 | Draw hyperbola | `catia_sketch_hyperbola` | ✅ Implemented |
| FR-002.10 | Draw parabola | `catia_sketch_parabola` | ✅ Implemented |
| FR-002.11 | Draw spline | `catia_sketch_spline` | ✅ Implemented |
| FR-002.12 | Create sketch point | `catia_sketch_point` | ✅ Implemented |
| FR-002.13 | Add constraints | `catia_sketch_constraint` | ✅ Implemented |
| FR-002.14 | List sketch geometry | `catia_sketch_get_geometry` | ✅ Implemented |
| FR-002.15 | Trim sketch curve | `catia_sketch_trim` | ✅ Implemented |
| FR-002.16 | Mirror sketch element | `catia_sketch_mirror` | ✅ Implemented |
| FR-002.17 | Convert to construction element | `catia_sketch_construction_element` | ✅ Implemented |
| FR-002.18 | List sketch geometry with indices | `catia_sketch_get_geometry` | ✅ Implemented |

### 2.3 Part Design (FR-003)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-003.1 | Create pad (extrusion) | `catia_pad` | ✅ Implemented |
| FR-003.2 | Create pocket (cut extrusion) | `catia_pocket` | ✅ Implemented |
| FR-003.3 | Create shaft (revolution) | `catia_shaft` | ✅ Implemented |
| FR-003.4 | Create groove (revolution cut) | `catia_groove` | ✅ Implemented |
| FR-003.5 | Create fillet (rounded edge) | `catia_fillet` | ✅ Implemented |
| FR-003.6 | Create chamfer (beveled edge) | `catia_chamfer` | ✅ Implemented |
| FR-003.7 | Create hole | `catia_hole` | ✅ Implemented |
| FR-003.8 | Create rectangular pattern | `catia_rect_pattern` | ✅ Implemented |
| FR-003.9 | Create circular pattern | `catia_circ_pattern` | ✅ Implemented |
| FR-003.10 | Mirror feature | `catia_mirror` | ✅ Implemented |
| FR-003.11 | Create shell | `catia_shell` | ✅ Implemented |
| FR-003.12 | Apply draft | `catia_draft` | ✅ Implemented |
| FR-003.13 | Apply thickness | `catia_thickness` | ✅ Implemented |
| FR-003.14 | Create lifting | `catia_lifting` | ✅ Implemented |
| FR-003.15 | Create sweep (VSS) | `catia_sweep` | ✅ Implemented |
| FR-003.16 | Create loft | `catia_loft` | ✅ Implemented |
| FR-003.17 | Boolean operation | `catia_boolean` | ✅ Implemented |
| FR-003.18 | Create rib | `catia_rib` | ✅ Implemented |
| FR-003.19 | Create slot | `catia_slot` | ✅ Implemented |
| FR-003.20 | Create stiffener | `catia_stiffener` | ✅ Implemented |
| FR-003.21 | Split body | `catia_split_body` | ✅ Implemented |
| FR-003.22 | List features | `catia_list_features` | ✅ Implemented |
| FR-003.23 | List edges | `catia_list_edges` | ✅ Implemented |
| FR-003.24 | Create variable-radius fillet | `catia_variable_fillet` | ✅ Implemented (v1.11.0) |
| FR-003.25 | Create drafted filleted pad | `catia_drafted_filleted_pad` | ✅ Implemented (v1.11.0) |
| FR-003.26 | Create drafted filleted pocket | `catia_drafted_filleted_pocket` | ✅ Implemented (v1.11.0) |
| FR-003.27 | Create multi-pad | `catia_multi_pad` | ✅ Implemented (v1.11.0) |
| FR-003.28 | Create multi-pocket | `catia_multi_pocket` | ✅ Implemented (v1.11.0) |

### 2.4 GSD — Wireframe & Surface (FR-004)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-004.1 | Create geometrical set | `catia_create_geometrical_set` | ✅ Implemented |
| FR-004.2 | Create point by coordinates | `catia_create_point_coord` | ✅ Implemented |
| FR-004.3 | Create point on curve | `catia_create_point_on_curve` | ✅ Implemented |
| FR-004.4 | Create point at intersection | `catia_create_point_intersection` | ✅ Implemented |
| FR-004.5 | Create line by 2 points | `catia_create_line_2points` | ✅ Implemented |
| FR-004.6 | Create line by point + direction | `catia_create_line_point_direction` | ✅ Implemented |
| FR-004.7 | Create tangent line | `catia_create_line_tangent` | ✅ Implemented |
| FR-004.8 | Create normal line to surface | `catia_create_line_normal_to_surface` | ✅ Implemented |
| FR-004.9 | Create circle | `catia_create_circle_center_radius` | ✅ Implemented |
| FR-004.10 | Create offset plane | `catia_create_plane_offset` | ✅ Implemented |
| FR-004.11 | Create parallel plane | `catia_create_plane_parallel` | ✅ Implemented |
| FR-004.12 | Create tangent plane | `catia_create_plane_tangent_to_surface` | ✅ Implemented |
| FR-004.13 | Create cylinder | `catia_create_cylinder` | ✅ Implemented |
| FR-004.14 | List geometrical sets | `catia_list_geometrical_sets` | ✅ Implemented |
| FR-004.15 | Create plane by 3 points | `catia_create_plane_3points` | ✅ Implemented |
| FR-004.16 | Create fill surface | `catia_create_fill` | ✅ Implemented |
| FR-004.17 | Create sweep surface | `catia_create_sweep` | ✅ Implemented |
| FR-004.18 | Create rotational surface | `catia_create_rotational_surface` | ✅ Implemented |
| FR-004.19 | Create offset surface | `catia_create_offset_surface` | ✅ Implemented |
| FR-004.20 | Join surfaces | `catia_create_join` | ✅ Implemented |
| FR-004.21 | Thicken surface | `catia_create_thicken` | ✅ Implemented |
| FR-004.22 | Create multi-section surface | `catia_create_surface_from_contours` | ✅ Implemented |
| FR-004.23 | Create sphere | `catia_create_sphere` | ✅ Implemented |
| FR-004.24 | Create cone | `catia_create_cone` | ✅ Implemented |
| FR-004.25 | Create torus | `catia_create_torus` | ✅ Implemented |
| FR-004.26 | Create ruled surface | `catia_create_ruled` | ✅ Implemented |
| FR-004.27 | Create blend | `catia_create_blend` | ✅ Implemented |
| FR-004.28 | Split surface | `catia_split_surface` | ✅ Implemented |
| FR-004.29 | Extend surface | `catia_extend_surface` | ✅ Implemented |
| FR-004.30 | Trim surface | `catia_trim_surface` | ✅ Implemented |
| FR-004.31 | Mirror wireframe element | `catia_create_mirror` | ✅ Implemented |
| FR-004.32 | Create tabulated cylinder | `catia_create_tabulated_cylinder` | ✅ Implemented |

### 2.5 Assembly (FR-005)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-005.1 | Add component | `catia_add_component` | ✅ Implemented |
| FR-005.2 | Create new part in assembly | `catia_add_new_part` | ✅ Implemented |
| FR-005.3 | Fix constraint | `catia_fix_constraint` | ✅ Implemented |
| FR-005.4 | Ground constraint | `catia_ground_constraint` | ✅ Implemented |
| FR-005.5 | Coincidence constraint | `catia_coincidence_constraint` | ✅ Implemented |
| FR-005.6 | Offset constraint | `catia_offset_constraint` | ✅ Implemented |
| FR-005.7 | Angle constraint | `catia_angle_constraint` | ✅ Implemented |
| FR-005.8 | Contact constraint | `catia_contact_constraint` | ✅ Implemented |
| FR-005.9 | Distance constraint | `catia_distance_constraint` | ✅ Implemented |
| FR-005.10 | Tangent constraint | `catia_tangent_constraint` | ✅ Implemented |
| FR-005.11 | Move component | `catia_move_component` | ✅ Implemented |
| FR-005.12 | Remove component | `catia_remove_component` | ✅ Implemented |
| FR-005.13 | Remove constraint | `catia_remove_constraint` | ✅ Implemented |
| FR-005.14 | List components | `catia_list_components` | ✅ Implemented |
| FR-005.15 | List constraints | `catia_list_constraints` | ✅ Implemented |

### 2.6 Measurement (FR-006)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-006.1 | Measure distance | `catia_measure_distance` | ✅ Implemented |
| FR-006.2 | Get inertia properties | `catia_get_inertia` | ✅ Implemented |
| FR-006.3 | Get bounding box | `catia_get_bounding_box` | ✅ Implemented |
| FR-006.4 | Get parameters | `catia_get_parameters` | ✅ Implemented |
| FR-006.5 | Set parameter | `catia_set_parameter` | ✅ Implemented |
| FR-006.6 | Measure angle | `catia_measure_angle` | ✅ Implemented |
| FR-006.7 | Measure area | `catia_measure_area` | ✅ Implemented |
| FR-006.8 | Measure length | `catia_measure_length` | ✅ Implemented |
| FR-006.9 | Measure interference | `catia_measure_interference` | ✅ Implemented |
| FR-006.10 | Update part | `catia_update_part` | ✅ Implemented |

### 2.7 Export & View (FR-007)

| ID | Requirement | Tool(s) | Status |
|----|-------------|---------|--------|
| FR-007.1 | Export to file | `catia_export` | ✅ Implemented |
| FR-007.2 | Take screenshot | `catia_screenshot` | ✅ Implemented |
| FR-007.3 | Set view orientation | `catia_set_view` | ✅ Implemented |
| FR-007.4 | Fit all | `catia_fit_all` | ✅ Implemented |

---

## 3. Non-Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| NR-001 | Platform: Windows only (COM Automation) | ✅ Met |
| NR-002 | Python 3.10+ | ✅ Met |
| NR-003 | CATIA V5 R2016+ | ✅ Met |
| NR-004 | Three transport modes (stdio, SSE, Streamable HTTP) | ✅ Met |
| NR-005 | Auto-connect on first tool use | ✅ Met |
| NR-006 | Auto-reconnect on COM drop | ✅ Met |
| NR-007 | Thread safety via asyncio.Lock | ✅ Met |
| NR-008 | Input validation before COM calls | ✅ Met |
| NR-009 | Dual-backend (pycatia + win32com fallback) | ✅ Met |
| NR-010 | Test suite runs on Linux without CATIA (mocked COM) | ✅ Met |
| NR-011 | Line length: 100 characters (ruff) | ✅ Met |
| NR-012 | Logging to %TEMP%/catia-mcp/ | ✅ Met |

---

## 4. Traceability Matrix

| Module | FR Range | Tools | Tests |
|--------|----------|-------|-------|
| Document | FR-001 | 10 | 24 |
| Sketcher | FR-002 | 18 | 38 |
| Part Design | FR-003 | 28 | 48 |
| GSD | FR-004 | 32 | 62 |
| Assembly | FR-005 | 15 | 32 |
| Measurement | FR-006 | 10 | 28 |
| Export | FR-007 | 4 | 12 |
| Connection | — | 3 | 12 |
| **Total** | **97 FRs** | **116** | **256** |

---

## 5. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.8 | 2026-05-29 | Agent | Initial v1.8 — 95 tools, 92 FRs |
| 1.9 | 2026-06-06 | Agent | Added FR-003.24–FR-003.28 (5 new Phase 2 Part Design tools), updated tool counts to 116 |
