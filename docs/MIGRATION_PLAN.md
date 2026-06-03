# CATIA V5 MCP Server — pycatia Migrationsplan

| Feld | Wert |
|------|------|
| **Dokument-ID** | MIG-001 |
| **Version** | 1.1 |
| **Status** | Abgeschlossen |
| **Datum** | 2026-06-03 |
| **Branch** | `feature/pycatia-backend` (off `master`) |
| **Ziel** | Ersetze hand-rolled `win32com`-Workarounds durch **pycatia** als Backend |

**Ergebnis:** Migration abgeschlossen. Dual-Backend (pycatia + win32com fallback) in allen Tool-Modulen implementiert. Dieses Dokument wird nicht weiter gepflegt.

---

## 1. Ziel & Motivation

### 1.1 Problemstellung
Der MCP-Server nutzt aktuell `win32com.client` direkt mit hand-rolled Workarounds für:
- gencache vs. dynamic.Dispatch-Switching (`_hsf()`, `_dpart()`, `_ref()`)
- ByRef-Array-Fallbacks in Measurement (`_get_cog_com()`, `_get_inertia_com()`, `_get_bounding_box_com()`)
- Manuelle COM-Proxy-Typ-Detection (`type(obj).__module__` checks)

Diese Workarounds sind fehleranfällig, schwer wartbar und limitieren die API-Abdeckung.

### 1.2 Lösung: pycatia als Backend
- **pycatia** (https://github.com/evereux/pycatia) ist ein Python-Wrapper um die CATIA V5 COM API
- Auto-generiert 131+ `add_new_*` Methoden für HybridShapeFactory
- Löst ByRef-Array-Probleme durch Property-Access (`measurable.cog`, `measurable.inertia`)
- Bietet saubere `.part`, `.product`, `.origin_elements` Properties (kein gencache/dynamic-Switching nötig)
- **MIT-Lizenz** — kompatibel mit unserem MIT

### 1.3 Strategie: Dual-Backend mit Fallback
- Default: **pycatia** (falls importierbar)
- Fallback: **win32com** (falls pycatia crasht oder nicht installiert)
- Transparent für die Tool-Schicht — Backend-Auswahl in `CATIAConnection`

---

## 2. Branch-Strategie

```
master                    ← produktiver Stand (bleibt unverändert)
  └── feature/pycatia-backend  ← Migrations-Branch
```

- Kleiner, fokussierter Commits pro Phase
- Jeder Commit: `pytest tests/` muss passen
- Am Ende: `git rebase -i` → clean history → PR nach `master`

---

## 3. Phasen

### Phase 0: Branch Setup
- `git checkout -b feature/pycatia-backend`
- Baseline: `pytest tests/` — alle Tests bestanden

### Phase 1: Dependency & Infrastructure (~2h)
| Datei | Änderung |
|-------|----------|
| `pyproject.toml` | `pycatia>=0.9.0; sys_platform == 'win32'` zu `dependencies` hinzufügen |
| `connection.py` | `HAS_PYCATIA` Flag, `_backend` property, `get_pycatia()` lazy-init, `get_active_part_pycatia()` |
| `conftest.py` | `sys.modules["pycatia"]` mocken für Tests |
| `tools/__init__.py` | `GSDTools` zu `__all__` hinzufügen (currently missing) |

### Phase 2: GSD Refactoring (~4h) — **größter Gain**
| Datei | Änderung |
|-------|----------|
| `gsd.py` | `_hsf()` → `pycatia.hybrid_shape_interfaces.HybridShapeFactory()` |
| | `_dpart()` → `pycatia.part_interfaces.Part()` |
| | `_ref_geom()` / `_ref_obj()` → pycatia's `create_reference_from_*()` |
| | `_find_shape()` → pycatia's `hybrid_body.hybrid_shapes` iteration |
| | `_ref()` → pycatia's `part.origin_elements.plane_xy` etc. |
| `test_gsd_tools.py` | Mocks für pycatia-Codepath |
| **Neue Tools** | `catia_create_extract`, `catia_create_intersection`, `catia_create_inverse`, `catia_create_tabulated_cylinder`, `catia_create_project` |

**Ergebnis:** ~150 Zeilen COM-Workarounds → ~30 Zeilen pycatia-Code

### Phase 3: Part Design Refactoring (~3h)
| Datei | Änderung |
|-------|----------|
| `part_design.py` | `ShapeFactory` → pycatia's `part.shape_factory` |
| | `CreateReferenceFromObject()` → pycatia's `part.create_reference_from_object()` |
| | `OriginElements` → pycatia's `part.origin_elements` |
| | `InWorkObject` → pycatia's `part.in_work_object` |
| | `UpdateObject()` → pycatia's `part.update_object()` |
| | `_resolve_geometry()` → pycatia's `body.shapes` iteration |
| `test_part_design_tools.py` | Mocks für pycatia-Codepath |

### Phase 4: Measurement Refactoring (~2h) — **ByRef-Fix**
| Datei | Änderung |
|-------|----------|
| `measurement.py` | `_get_cog_com()` → `measurable.cog` (list property, kein ByRef) |
| | `_get_inertia_com()` → `measurable.inertia` (list property) |
| | `_get_bounding_box_com()` → `measurable.bounding_box` (list property) |
| | `GetMinimumDistance()` → `measurable.get_minimum_distance()` |
| | `GetAngle()` → `measurable.get_angle()` |
| | `Volume`, `Area`, `Length` → pycatia properties |
| `test_measurement_tools.py` | Mocks für pycatia-Codepath |

**Ergebnis:** ~140 Zeilen ByRef-Fallback-Code entfallen komplett

### Phase 5: Sketcher Refactoring (~2h)
| Datei | Änderung |
|-------|----------|
| `sketcher.py` | `OpenEdition()` → `sketch.open_edition()` |
| | `CreateLine()` → `factory.create_line()` |
| | `CreateClosedCircle()` → `factory.create_closed_circle()` |
| | `Constraints` → `sketch.constraints` |
| | `GeometricElements` → `sketch.geometric_elements` |
| `test_sketcher_tools.py` | Mocks für pycatia-Codepath |

### Phase 6: Assembly, Document, Export (~3h)
| Datei | Änderung |
|-------|----------|
| `assembly.py` | `Products` → `product.products`, `Connections` → `product.connections()`, `Position` → `component.position` |
| `document.py` | `Add()` → `documents.add()`, `.Part` → `doc.part`, `.Product` → `doc.product` |
| `export.py` | `ExportData()` → `doc.export_data()`, `CaptureToFile()` → `viewer.capture_to_file()`, `Viewpoint3D` → `viewer.viewpoint_3d` |
| Tests | Mocks für pycatia-Codepath |

### Phase 7: Dual-Backend & Fallback (~2h)
| Datei | Änderung |
|-------|----------|
| `connection.py` | `self._backend = "pycatia"` (default) oder `"win32com"` (fallback) |
| | Pro-Tool-Call: versuche pycatia, fallback to win32com on exception |
| `utils.py` | `format_catia_error()` erkennt Backend und gibt spezifische Hinweise |

### Phase 8: Docs & Final Cleanup (~2h)
| Datei | Änderung |
|-------|----------|
| `README.md` | pycatia als Dependency erwähnen; SSE-Port: `8765` (README) vs `3000` (Code) → synchronisieren |
| `REQUIREMENTS.md` | Tool-Count: 55 → **95** |
| `GAP_ANALYSIS.md` | Tool-Count: 91 → **95** |
| `server.py` | `DEFAULT_SSE_PORT = 3000` → `8765` (um README zu entsprechen) |
| **Final** | `pytest tests/` — alle Tests bestanden |
| **Final** | `git rebase -i` → clean history → PR nach `master`

---

## 4. Risikoanalyse

| Risiko | Wahrscheinlichkeit | Minderung |
|--------|-------------------|-----------|
| pycatia alpha-Bugs | Mittel | Dual-Backend-Fallback |
| pycatia-Version-Breakage | Niedrig | Version pin `>=0.9.0,<1.0.0` |
| Performance-Einbußen | Niedrig | pycatia ist dünner Wrapper um win32com |
| Test-Mocks brechen | Niedrig | conftest.py Erweiterung |
| CATIA-Version-Inkompatibilität | Niedrig | pycatia R28-basiert; Fallback zu win32com |

---

## 5. Aufwandsschätzung

| Phase | Dateien | Aufwand |
|-------|---------|---------|
| 0 (Branch) | — | 5min |
| 1 (Dependency) | 4 | 2h |
| 2 (GSD) | 2 + neue Tools | 4h |
| 3 (Part Design) | 2 | 3h |
| 4 (Measurement) | 2 | 2h |
| 5 (Sketcher) | 2 | 2h |
| 6 (Assembly/Doc/Export) | 6 | 3h |
| 7 (Dual-Backend) | 2 | 2h |
| 8 (Docs/Cleanup) | 4 | 2h |
| **Total** | **~12 files** | **~20h** |

---

## 6. Erfolgskriterien

- [ ] Alle 95 Tools funktionieren mit pycatia-Backend
- [ ] Fallback zu win32com funktioniert bei pycatia-Fehlern
- [ ] `pytest tests/` — alle Tests bestanden (inkl. neue pycatia-Mocks)
- [ ] `pytest tests/` — alle Tests bestanden auf Linux (ohne CATIA, mit Mocks)
- [ ] Dokumentation konsistent (README, REQUIREMENTS, GAP_ANALYSIS)
- [ ] Code-Qualität: keine hand-rolled COM-Workarounds mehr in Tool-Modulen
