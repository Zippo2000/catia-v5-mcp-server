# CATIA V5 MCP Server — Gap Analysis

| Field | Value |
|-------|-------|
| **Document ID** | GAP-001 |
| **Version** | 1.3 |
| **Status** | Active |
| **Date** | 2026-06-06 |
| **Basis** | catia-v5-mcp-server v1.11.0, 116 Tools, 7 Modules |

---

## 1. Overview

This document analyzes the gap between CATIA V5's full COM Automation API and the tools
currently exposed by the MCP server. It identifies covered areas, gaps, and prioritization
for future development.

**Current Coverage:** 116 tools across 7 modules covering ~62% of tracked API areas.

---

## 2. Module Coverage Summary

| Module | CATIA API Areas | Covered | Gap | Coverage |
|--------|----------------|---------|-----|----------|
| Document Management | 12 | 10 | 2 | 83% |
| Sketcher | 22 | 18 | 4 | 82% |
| Part Design | 42 | 28 | 14 | 67% |
| GSD (Wireframe & Surface) | 52 | 32 | 20 | 62% |
| Assembly | 25 | 15 | 10 | 60% |
| Measurement | 18 | 10 | 8 | 56% |
| Export & View | 8 | 4 | 4 | 50% |
| **Total** | **179** | **116** | **63** | **65%** |

---

## 3. Part Design — Gap Analysis (FR-003)

### 3.1 Covered (28 tools)

| Feature | Tool | Status |
|---------|------|--------|
| Pad | `catia_pad` | ✅ |
| Pocket | `catia_pocket` | ✅ |
| Shaft | `catia_shaft` | ✅ |
| Groove | `catia_groove` | ✅ |
| Fillet (constant radius) | `catia_fillet` | ✅ |
| Chamfer | `catia_chamfer` | ✅ |
| Hole | `catia_hole` | ✅ |
| Rectangular pattern | `catia_rect_pattern` | ✅ |
| Circular pattern | `catia_circ_pattern` | ✅ |
| Mirror | `catia_mirror` | ✅ |
| Shell | `catia_shell` | ✅ |
| Draft | `catia_draft` | ✅ |
| Thickness | `catia_thickness` | ✅ |
| Lifting | `catia_lifting` | ✅ |
| Sweep (VSS) | `catia_sweep` | ✅ |
| Loft | `catia_loft` | ✅ |
| Boolean | `catia_boolean` | ✅ |
| Rib | `catia_rib` | ✅ |
| Slot | `catia_slot` | ✅ |
| Stiffener | `catia_stiffener` | ✅ |
| Split body | `catia_split_body` | ✅ |
| List features | `catia_list_features` | ✅ |
| List edges | `catia_list_edges` | ✅ |
| **Variable fillet** | `catia_variable_fillet` | ✅ (v1.11.0) |
| **Drafted filleted pad** | `catia_drafted_filleted_pad` | ✅ (v1.11.0) |
| **Drafted filleted pocket** | `catia_drafted_filleted_pocket` | ✅ (v1.11.0) |
| **Multi pad** | `catia_multi_pad` | ✅ (v1.11.0) |
| **Multi pocket** | `catia_multi_pocket` | ✅ (v1.11.0) |

### 3.2 Gaps (14 areas)

| # | Feature | Priority | Rationale |
|---|---------|----------|-----------|
| 1 | **Variable chamfer** | High | Complements variable fillet; common in mold design |
| 2 | **Multi-fillet** | High | Apply fillets to multiple edges with different radii in one operation |
| 3 | **Multi-chamfer** | Medium | Apply chamfers to multiple edges with different parameters |
| 4 | **Drafted pad** | Medium | Pad with draft but no fillet (simpler variant of drafted_filleted_pad) |
| 5 | **Drafted pocket** | Medium | Pocket with draft but no fillet |
| 6 | **Multi-fillet** (different radii) | Medium | Batch fillet with per-edge radius specification |
| 7 | **Remove feature** | High | Delete a feature from the part body |
| 8 | **Rename feature** | Medium | Rename existing features for clarity |
| 9 | **Visibility toggle** | Medium | Show/hide features in the 3D view |
| 10 | **Update object** | Low | Force update of a specific feature |
| 11 | **Multi-loft** | Low | Loft from multiple sketch sets |
| 12 | **Multi-sweep** | Low | Sweep from multiple profiles |
| 13 | **Power copy** | Low | Parametric copy of features between parts |
| 14 | **Multi-body management** | Medium | Create, rename, delete part bodies |

---

## 4. Sketcher — Gap Analysis (FR-002)

### 4.1 Gaps (4 areas)

| # | Feature | Priority |
|---|---------|----------|
| 1 | **Polyline** | Medium |
| 2 | **Polygon** | Medium |
| 3 | **Point on geometry** | Low |
| 4 | **Delete sketch element** | High |

---

## 5. GSD — Gap Analysis (FR-004)

### 5.1 Gaps (20 areas)

| # | Feature | Priority |
|---|---------|----------|
| 1 | **Extract** | High |
| 2 | **Intersection** | High |
| 3 | **Inverse** | Medium |
| 4 | **Project** | High |
| 5 | **Multi-project** | Medium |
| 6 | **Swept area** | Low |
| 7 | **Surface area** | Medium |
| 8 | **Distance to surface** | Medium |
| 9 | **Angle between surfaces** | Medium |
| 10 | **Create curve on surface** | High |
| 11 | **Isoparametric curve** | Medium |
| 12 | **Offset curve** | Medium |
| 13 | **Parallel curve** | Low |
| 14 | **Intersection curve** | High |
| 15 | **Sweep with multiple sections** | Medium |
| 16 | **Surface from 3 curves** | Low |
| 17 | **Surface from 4 curves** | Medium |
| 18 | **Healing** | Low |
| 19 | **Analysis (curvature, deviation)** | Medium |
| 20 | **Multi-directional offset** | Low |

---

## 6. Assembly — Gap Analysis (FR-005)

### 6.1 Gaps (10 areas)

| # | Feature | Priority |
|---|---------|----------|
| 1 | **In-context design** | High |
| 2 | **Configurations** | Medium |
| 3 | **Instance visibility** | Medium |
| 4 | **Link management** | Medium |
| 5 | **Update assembly** | High |
| 6 | **Product tree navigation** | Medium |
| 7 | **Create sub-assembly** | High |
| 8 | **Save assembly** | Low |
| 9 | **Insert component from library** | Medium |
| 10 | **Replace component** | Low |

---

## 7. Measurement — Gap Analysis (FR-006)

### 7.1 Gaps (8 areas)

| # | Feature | Priority |
|---|---------|----------|
| 1 | **Volume measurement** | High |
| 2 | **Surface area** | Medium |
| 3 | **Mass properties** | High |
| 4 | **Moment of inertia** | Medium |
| 5 | **Center of gravity** | Medium |
| 6 | **Section properties** | Low |
| 7 | **Curvature measurement** | Low |
| 8 | **Deviation analysis** | Low |

---

## 8. Export & View — Gap Analysis (FR-007)

### 8.1 Gaps (4 areas)

| # | Feature | Priority |
|---|---------|----------|
| 1 | **Export to PDF** | Medium |
| 2 | **Export to 3DXML** | Medium |
| 3 | **Export to VRML** | Low |
| 4 | **Custom view save/recall** | Medium |

---

## 9. Priority Roadmap

### Phase 2 (Completed — v1.11.0)

- ✅ Variable fillet
- ✅ Drafted filleted pad
- ✅ Drafted filleted pocket
- ✅ Multi pad
- ✅ Multi pocket

### Phase 3 (Proposed)

| Priority | Feature | Module |
|----------|---------|--------|
| P1 | Remove feature | Part Design |
| P1 | Extract | GSD |
| P1 | Project | GSD |
| P1 | Intersection | GSD |
| P1 | Volume measurement | Measurement |
| P1 | Mass properties | Measurement |
| P2 | Variable chamfer | Part Design |
| P2 | Multi-fillet | Part Design |
| P2 | In-context design | Assembly |
| P2 | Create sub-assembly | Assembly |

### Phase 4 (Future)

| Priority | Feature | Module |
|----------|---------|--------|
| P3 | Drawing tools (2D drafting) | Drawing |
| P3 | Knowledgeware (formulas, rules) | Knowledgeware |
| P3 | Configurations | Assembly |
| P4 | 3DEXPERIENCE CATIA support | All |

---

## 10. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.2 | 2026-05-29 | Agent | Initial v1.2 — 95 tools, 187 API areas tracked |
| 1.3 | 2026-06-06 | Agent | Updated for v1.11.0: added 5 new Part Design tools (variable_fillet, drafted_filleted_pad/pocket, multi_pad/pocket), updated coverage to 116 tools / 65% |
