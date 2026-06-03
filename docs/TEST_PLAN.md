# ASPICE-Test-Migrationsplan

| Feld | Wert |
|------|------|
| **Dokument-ID** | TST-001 |
| **Version** | 1.0 |
| **Status** | Entwurf |
| **Datum** | 2026-06-03 |
| **Ziel** | Alle 92 FRs (FR-04 bis FR-10) mit Happy-Path- und Error-Path-Tests abdecken |
| **Basis** | GSD-Test-Pattern als Referenz (test_gsd_tools.py) |

---

## 1. Ist-Zustand

| Modul | FRs | ✅ Voll | ⚠️ Teilw. | ❌ Keine | Tests gesamt |
|-------|-----|---------|-----------|----------|-------------|
| FR-04 Document | 7 | 0 | 2 | 5 | 86 |
| FR-05 Sketcher | 14 | 0 | 8 | 6 | 188 |
| FR-06 Part Design | 19 | 0 | 13 | 6 | 178 |
| FR-07 Assembly | 14 | 5 | 3 | 6 | 143 |
| FR-08 Measurement | 10 | 5 | 3 | 2 | 150 |
| FR-09 Export & View | 4 | 0 | 3 | 1 | 77 |
| FR-10 GSD | 24 | 17 | 5 | 2 | 685 |
| **Total** | **92** | **27** | **37** | **28** | **~1507** |

**Ziel:** 0 ❌, ⚠️ reduziert auf Maximal-2 pro FR, ~600+ neue Tests gesamt.

---

## 2. GSD-Pattern (Referenz)

Jeder Test folgt diesem Pattern:

```python
class Test<ToolName>:
    # Happy Path — valid input, assert on result string
    def test_<tool_snake>_valid(self, tools_fixture, conn_mock):
        result = tools_fixture.execute("catia_<tool_name>", { ... })
        assert isinstance(result, str)
        assert "expected_keyword" in result

    # Happy Path — mit optionalen Parametern
    def test_<tool_snake>_with_optional(self, tools_fixture, conn_mock):
        result = tools_fixture.execute("catia_<tool_name>", { ..., "optional_param": ... })
        assert isinstance(result, str)

    # Error Path — validation errors
    def test_<tool_snake>_<param>_negative_raises(self, tools_fixture):
        with pytest.raises(ValueError, match="positive"):
            tools_fixture.execute("catia_<tool_name>", { "param": -1 })

    # Error Path — missing required element
    def test_<tool_snake>_not_found_raises(self, tools_fixture, conn_mock):
        conn_mock.hso.Count = 0  # or other mock config
        with pytest.raises(RuntimeError, match="not found"):
            tools_fixture.execute("catia_<tool_name>", { "element": "Ghost" })
```

### Fixture-Template

```python
@pytest.fixture(autouse=True)
def fresh_com_mocks():
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()
    yield

@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    # ... module-spezifische Mock-Konfiguration ...
    return mock

@pytest.fixture
def <module>_tools(conn_mock):
    from catia_mcp.tools.<module> import <Module>Tools
    return <Module>Tools(conn_mock)
```

---

## 3. Änderungen pro Modul

### 3.1 test_document_tools.py — 5 neue Test-Klassen, ~30 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-04.1 | `catia_new_part` | `test_new_part_default`, `test_new_part_with_name`, `test_new_part_calls_docs_add` | `conn_mock.documents.Add.return_value.Part.Name = "Part.1"` |
| FR-04.2 | `catia_new_product` | `test_new_product_default`, `test_new_product_with_name`, `test_new_product_calls_docs_add` | `conn_mock.documents.Add.return_value.Product.Name = "Product.1"` |
| FR-04.3 | `catia_open_document` | `test_open_document_valid` (Happy Path) | `conn_mock.documents.Open.return_value.Name = "Opened.Part"` |
| FR-04.4 | `catia_save_document` | `test_save_document_with_path` (Happy Path) | `conn_mock.active_document.SaveAs` mock |
| FR-04.5 | `catia_close_document` | `test_close_document_no_save`, `test_close_document_with_save` | `conn_mock.active_document.Name = "ToClose.Part"` |
| FR-04.6 | `catia_list_documents` | `test_list_documents_empty`, `test_list_documents_with_docs`, `test_list_documents_part_type` | `conn_mock.documents.Count = 0` oder `2`, `docs.Item(1).Name = "Part.1"` |
| FR-04.7 | `catia_get_active_document_info` | `test_get_info_part`, `test_get_info_product`, `test_get_info_unknown` | `conn_mock.active_document.Part.Name = ...`, `doc.Bodies.Count = 1` |

**conn_mock-Erweiterung:**
```python
@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    mock.active_document = MagicMock()
    mock.active_document.Name = "Test.Part"
    mock.active_document.FullName = "C:/Test.Part"
    mock.documents = MagicMock()
    mock.documents.Count = 0
    mock.documents.Add.return_value = MagicMock()
    mock.documents.Open.return_value = MagicMock()
    mock.documents.Open.return_value.Name = "Opened.Part"
    mock.refresh_display = MagicMock()
    mock.normalize_path.return_value = "C:/out/part.stp"
    return mock
```

---

### 3.2 test_sketcher_tools.py — 6 neue Test-Klassen, ~25 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-05.4 | `catia_sketch_rectangle` | `test_rectangle_valid`, `test_rectangle_no_active_sketch` | `_active_sketch` + `_active_factory` setzen, `factory.CreateRectangle` mock |
| FR-05.7 | `catia_sketch_arc` | `test_arc_valid`, `test_arc_negative_radius_raises`, `test_arc_no_active_sketch` | `factory.CreateArc` mock |
| FR-05.9 | `catia_sketch_point` | `test_point_valid`, `test_point_no_active_sketch` | `factory.CreatePoint` mock |
| FR-05.10 | `catia_sketch_constraint` | `test_constraint_coincidence`, `test_constraint_distance`, `test_constraint_no_active`, `test_constraint_invalid_type` | `sketch.Constraints.AddConstraint` mock |
| FR-05.11 | `catia_sketch_get_geometry` | `test_get_geometry_list`, `test_get_geometry_empty` | `sketch.GeometricElements.Count = 2` |
| FR-05.1-3 | Happy-Path-Ergänzung | `test_sketch_line_valid`, `test_circle_valid`, `test_rectangle_centered_valid`, `test_close_sketch_valid` | Bestehende Tests erweitern |

**conn_mock-Erweiterung:**
```python
@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    part = MagicMock()
    mock.get_active_part.return_value = part
    part.OriginElements.PlaneXY = MagicMock()
    part.OriginElements.PlaneYZ = MagicMock()
    part.OriginElements.PlaneZX = MagicMock()
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    body.Sketches.Add.return_value = MagicMock()
    part.CreateReferenceFromObject.return_value = MagicMock()
    mock.hso = MagicMock()
    return mock
```

---

### 3.3 test_part_design_tools.py — 6 neue Test-Klassen, ~35 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-06.14 | `catia_list_features` | `test_list_features`, `test_list_features_empty` | `part.MainBody.Shapes.Count = 3`, `Shapes.Item(i).Name` |
| FR-06.15 | `catia_list_edges` | `test_list_edges`, `test_list_edges_empty` | `part.MainBody.Shapes` mit Edge-Namen |
| FR-06.16 | `catia_lifting` | `test_lifting_valid`, `test_lifting_missing_curve_raises`, `test_lifting_missing_sketch_raises` | `sf.AddNewLifting` mock, `_resolve_geometry` mock |
| FR-06.17 | `catia_sweep` | `test_sweep_valid`, `test_sweep_missing_spine_raises` | `sf.AddNewVariableSectionShape` mock |
| FR-06.18 | `catia_loft` | `test_loft_valid`, `test_loft_empty_sketches_raises` | `sf.AddNewLoft` mock |
| FR-06.19 | `catia_boolean` | `test_boolean_union`, `test_boolean_cut`, `test_boolean_intersect`, `test_boolean_missing_body_raises` | `sf.AddOperation` mock |

**conn_mock-Erweiterung:**
```python
@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    part = MagicMock()
    mock.get_active_part.return_value = part
    part.ShapeFactory = MagicMock()
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    body.Sketches.Count = 1
    body.Sketches.Item.return_value.Name = "Sketch.1"
    part.HybridBodies.Count = 1
    mock.get_origin_elements.return_value = {"xy": MagicMock(), "yz": MagicMock(), "zx": MagicMock()}
    mock.hso = MagicMock()
    mock.hso.Count = 1
    mock.hso.Item.return_value.Value = MagicMock()
    mock.refresh_display = MagicMock()
    return mock
```

---

### 3.4 test_assembly_tools.py — 6 neue Test-Klassen, ~25 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-07.2 | `catia_add_new_part` | `test_add_new_part_default`, `test_add_new_part_with_name` | `product.Products.AddComponentWithinProduct` mock |
| FR-07.4 | `catia_coincidence_constraint` | `test_coincidence_valid`, `test_coincidence_nonexistent_raises` | `Connections.AddBiEltCst` mock |
| FR-07.5 | `catia_offset_constraint` | `test_offset_valid`, `test_offset_negative_raises` | `Connections.AddBiEltCst` + Offset mock |
| FR-07.6 | `catia_angle_constraint` | `test_angle_valid`, `test_angle_negative_raises` | `Connections.AddBiEltCst` + Angle mock |
| FR-07.8 | `catia_list_components` | `test_list_components`, `test_list_components_empty` | `product.Products.Count = 3` |
| FR-07.9 | `catia_list_constraints` | `test_list_constraints`, `test_list_constraints_empty` | `product.GetConstraints()[]` mock |

**conn_mock-Erweiterung:**
```python
@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    product = MagicMock()
    mock.get_active_product.return_value = product
    product.Products.Count = 2
    product.Products.Item.side_effect = lambda i: [MagicMock(), MagicMock()][i-1]
    product.Products.Item.return_value.Name = "Part1"
    product.GetConstraints.return_value = []
    conn_mock = MagicMock()
    conn_mock.AddBiEltCst = MagicMock()
    product.Connections.return_value = conn_mock
    return mock
```

---

### 3.5 test_measurement_tools.py — 3 neue Test-Klassen, ~15 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-08.3 | `catia_get_bounding_box` | `test_bounding_box_valid`, `test_bounding_box_not_found` | `measurable.bounding_box` property mock |
| FR-08.4 | `catia_get_parameters` | `test_get_parameters_all`, `test_get_parameters_with_filter`, `test_get_parameters_empty` | `part.Parameters.Count = 3`, `Parameters.Item(i).Name` |
| FR-08.6 | `catia_update_part` | `test_update_part_valid` | `part.Update()` mock |

**conn_mock-Erweiterung:**
```python
@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    part = MagicMock()
    mock.get_active_part.return_value = part
    part.Parameters.Count = 2
    p1 = MagicMock(); p1.Name = "Param1"; p1.Value = 10.0
    p2 = MagicMock(); p2.Name = "Param2"; p2.Value = 20.0
    part.Parameters.Item.side_effect = lambda i: [p1, p2][i-1]
    body = MagicMock()
    mock.get_active_part_body.return_value = body
    mock.app = MagicMock()
    spa = MagicMock()
    mock.app.GetWorkbench.return_value = spa
    measurable = MagicMock()
    spa.GetMeasurable.return_value = measurable
    mock.hso = MagicMock()
    mock.hso.Count = 1
    mock.hso.Item.return_value.Value = MagicMock()
    return mock
```

---

### 3.6 test_export_tools.py — 1 neue Test-Klasse, ~8 neue Tests

| FR | Tool | Neue Tests | Mock-Setup |
|----|------|-----------|------------|
| FR-09.4 | `catia_fit_all` | `test_fit_all_valid` | `viewer.Reframe()` mock |

**conn_mock-Erweiterung:**
```python
# Besteht bereits — nur einen Happy-Path-Test hinzufügen
```

---

### 3.7 test_gsd_tools.py — 2 Lücken schließen, ~5 neue Tests

| FR | Tool | Neue Tests |
|----|------|-----------|
| FR-10.3 | `catia_create_line_2points` | `test_line_2points_missing_point_raises` |
| FR-10.9 | `catia_create_plane_3points` | `test_plane_3points_missing_point_raises` |

---

### 3.8 ⚠️-Tests in ✅ umwandeln (Happy-Path-Ergänzung)

Für alle 37 ⚠️-getesteten FRs jeweils 1-2 Happy-Path-Tests hinzufügen:

| Modul | FR | Fehlende Happy-Path-Tests |
|-------|-----|--------------------------|
| FR-04 | 04.3, 04.4 | `test_open_valid`, `test_save_with_path_valid` |
| FR-05 | 05.1, 05.2, 05.3, 05.5, 05.6, 05.8, 05.12-14 | `test_line_valid`, `test_circle_valid`, `test_close_valid`, `test_rectangle_centered_valid`, `test_spline_valid`, `test_ellipse_valid`, `test_hyperbola_valid`, `test_parabola_valid` |
| FR-06 | 06.1-13 | `test_pad_valid`, `test_pocket_valid`, `test_shaft_valid`, `test_groove_valid`, `test_fillet_valid`, `test_chamfer_valid`, `test_hole_valid`, `test_rect_pattern_valid`, `test_circ_pattern_valid`, `test_mirror_valid`, `test_shell_valid`, `test_draft_valid`, `test_thickness_valid` |
| FR-07 | 07.1, 07.3, 07.7 | `test_add_component_valid`, `test_fix_valid`, `test_move_valid` |
| FR-08 | 08.1, 08.2, 08.5 | `test_distance_valid`, `test_inertia_valid`, `test_set_parameter_valid` |
| FR-09 | 09.2, 09.3 | `test_screenshot_valid`, `test_set_view_valid` |
| FR-10 | 10.3, 10.8, 10.9, 10.11, 10.13 | `test_line_2points_missing_raises`, `test_list_sets_output`, `test_plane_3points_missing_raises`, `test_sweep_missing_raises`, `test_offset_missing_raises` |

---

## 4. Implementierungs-Reihenfolge

Jeder Schritt ist eine eigenständige Iteration mit `pytest tests/` als Gate:

| Schritt | Datei | Neue Tests | Aufwand |
|---------|-------|-----------|---------|
| 1 | `test_document_tools.py` | ~30 | ⭐⭐ |
| 2 | `test_sketcher_tools.py` | ~25 | ⭐⭐ |
| 3 | `test_part_design_tools.py` | ~35 | ⭐⭐⭐ |
| 4 | `test_assembly_tools.py` | ~25 | ⭐⭐ |
| 5 | `test_measurement_tools.py` | ~15 | ⭐ |
| 6 | `test_export_tools.py` | ~8 | ⭐ |
| 7 | `test_gsd_tools.py` | ~5 | ⭐ |
| 8 | Happy-Path-Ergänzung (alle 6 Module) | ~40 | ⭐⭐ |
| **Total** | | **~183** | |

---

## 5. Qualitätskriterien

- [ ] Jeder FR hat mindestens 1 Happy-Path-Test
- [ ] Jeder FR mit Validierung hat mindestens 1 Error-Path-Test
- [ ] Alle Tests verwenden `tools_fixture.execute()` (nicht direkte Method-Calls)
- [ ] Alle Tests verwenden `pytest.raises()` für Error-Path-Tests
- [ ] `conn_mock` fixture ist pro Modul konsistent mit GSD-Pattern
- `pytest tests/` — alle 256+600=856+ Tests bestanden
