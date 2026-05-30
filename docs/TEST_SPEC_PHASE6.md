# Phase 6 — GSD (Wireframe & Surface Design): Test Spezifikation

## Ziel

GSD-Module (`catia_mcp/tools/gsd.py`) implementieren mit 16 Tools:

**Wireframe (8 Tools):**
| Tool | CATIA API | Beschreibung |
|------|-----------|-------------|
| `catia_create_geometrical_set` | `HybridBodies.Add()` | Geometrical Set erstellen |
| `catia_create_point_coord` | `HybridShapeFactory.AddNewPointCoord` | Punkt durch Koordinaten (x,y,z) |
| `catia_create_line_2points` | `HybridShapeFactory.AddNewLine2Points` | Linie durch 2 Punkte |
| `catia_create_line_point_direction` | `HybridShapeFactory.AddNewLinePtDir` | Linie durch Punkt und Richtung |
| `catia_create_circle_center_radius` | `HybridShapeFactory.AddNewCircle` | Kreis (Mitte + Radius) |
| `catia_create_plane_offset` | `HybridShapeFactory.AddNewPlaneOffset` | Ebene mit Offset |
| `catia_create_cylinder` | `HybridShapeFactory.AddNewCylinder` | Zylinder |
| `catia_list_geometrical_sets` | `HybridBodies.Item()` | Alle Geometrical Sets auflisten |

**Surface (8 Tools):**
| Tool | CATIA API | Beschreibung |
|------|-----------|-------------|
| `catia_create_plane_3points` | `HybridShapeFactory.AddNewPlane3Points` | Ebene durch 3 Punkte |
| `catia_create_fill` | `HybridShapeFactory.AddNewFill` | Fill-Surface |
| `catia_create_sweep` | `HybridShapeFactory.AddNewSweptSurface` | Swept Surface |
| `catia_create_surface_from_contours` | `HybridShapeFactory.AddNewSurfFromContours` | Surface von Konturen |
| `catia_create_rotational_surface` | `HybridShapeFactory.AddNewRotationalSurface` | Rotations-Surface |
| `catia_create_offset_surface` | `HybridShapeFactory.AddNewOffset` | Offset-Surface |
| `catia_create_join` | `HybridShapeFactory.AddNewJoin` | Mehrere Surfaces verbinden |
| `catia_create_thicken` | `HybridShapeFactory.AddNewThicken` | Surface → Solid |

---

## Test 1: Geometrical Set

### TC-6-01: create_geometrical_set valid
```python
def test_create_geometrical_set_valid():
    """Geometrical Set mit Namen erstellen."""
    result = gsd_tools.execute("catia_create_geometrical_set", {"name": "Construction"})
    assert "Geometrical Set" in result or "hybrid" in result.lower()
```

### TC-6-02: create_geometrical_set empty name
```python
def test_create_geometrical_set_empty():
    """Geometrical Set mit leerem Namen → Error."""
    result = gsd_tools.execute("catia_create_geometrical_set", {"name": ""})
    assert "error" in result.lower() or "name" in result.lower()
```

---

## Test 2: Wireframe

### TC-6-03: point_coord valid
```python
def test_point_coord_valid():
    result = gsd_tools.execute("catia_create_point_coord", {
        "x": 0, "y": 10, "z": 20
    })
    assert isinstance(result, str)
```

### TC-6-04: point_coord non-numeric
```python
def test_point_coord_non_numeric():
    with pytest.raises((ValueError, RuntimeError)):
        gsd_tools.execute("catia_create_point_coord", {"x": "abc", "y": 10, "z": 20})
```

### TC-6-05: line_2points valid
```python
def test_line_2points_valid():
    result = gsd_tools.execute("catia_create_line_2points", {
        "point1_name": "Point.1", "point2_name": "Point.2"
    })
    assert isinstance(result, str)
```

### TC-6-06: line_2points missing point
```python
def test_line_2points_missing():
    result = gsd_tools.execute("catia_create_line_2points", {
        "point1_name": "Point.1"
    })
    assert "error" in result.lower() or "point" in result.lower()
```

### TC-6-07: circle valid
```python
def test_circle_valid():
    result = gsd_tools.execute("catia_create_circle_center_radius", {
        "center_name": "Point.1", "radius": 50
    })
    assert isinstance(result, str)
```

### TC-6-08: circle negative radius
```python
def test_circle_negative_radius():
    with pytest.raises((ValueError, RuntimeError)):
        gsd_tools.execute("catia_create_circle_center_radius", {
            "center_name": "Point.1", "radius": -10
        })
```

### TC-6-09: plane_offset valid
```python
def test_plane_offset_valid():
    result = gsd_tools.execute("catia_create_plane_offset", {
        "reference_plane": "xy", "offset": 25
    })
    assert isinstance(result, str)
```

### TC-6-10: cylinder valid
```python
def test_cylinder_valid():
    result = gsd_tools.execute("catia_create_cylinder", {
        "center_name": "Point.1", "axis": "xy", "radius": 20, "height": 100
    })
    assert isinstance(result, str)
```

### TC-6-11: list_geometrical_sets
```python
def test_list_geometrical_sets():
    result = gsd_tools.execute("catia_list_geometrical_sets", {})
    assert isinstance(result, str)
```

---

## Test 3: Surface

### TC-6-12: plane_3points valid
```python
def test_plane_3points_valid():
    result = gsd_tools.execute("catia_create_plane_3points", {
        "point1_name": "Point.1", "point2_name": "Point.2", "point3_name": "Point.3"
    })
    assert isinstance(result, str)
```

### TC-6-13: fill valid
```python
def test_fill_valid():
    result = gsd_tools.execute("catia_create_fill", {
        "contour_names": ["Circle.1", "Circle.2"]
    })
    assert isinstance(result, str)
```

### TC-6-14: fill empty contours
```python
def test_fill_empty():
    result = gsd_tools.execute("catia_create_fill", {"contour_names": []})
    assert "error" in result.lower()
```

### TC-6-15: sweep valid
```python
def test_sweep_valid():
    result = gsd_tools.execute("catia_create_sweep", {
        "spine_name": "Line.1", "section_name": "Circle.1"
    })
    assert isinstance(result, str)
```

### TC-6-16: offset_surface valid
```python
def test_offset_surface_valid():
    result = gsd_tools.execute("catia_create_offset_surface", {
        "surface_name": "Sheet.1", "distance": 5
    })
    assert isinstance(result, str)
```

### TC-6-17: join valid
```python
def test_join_valid():
    result = gsd_tools.execute("catia_create_join", {
        "surface_names": ["Sheet.1", "Sheet.2"]
    })
    assert isinstance(result, str)
```

### TC-6-18: thicken valid
```python
def test_thicken_valid():
    result = gsd_tools.execute("catia_create_thicken", {
        "surface_name": "Sheet.1", "thickness": 2
    })
    assert isinstance(result, str)
```

### TC-6-19: rotational_surface valid
```python
def test_rotational_surface_valid():
    result = gsd_tools.execute("catia_create_rotational_surface", {
        "axis_name": "Axis.1", "profile_name": "Circle.1", "angle": 180
    })
    assert isinstance(result, str)
```

### TC-6-20: surface_from_contours valid
```python
def test_surface_from_contours_valid():
    result = gsd_tools.execute("catia_create_surface_from_contours", {
        "contour_names": ["Circle.1", "Circle.2"]
    })
    assert isinstance(result, str)
```

---

## Test 4: Tool Integration

### TC-6-21: all 16 GSD tools in definitions
```python
def test_gsd_tool_definitions():
    defs = gsd_tools.get_tool_definitions()
    names = [d["name"] for d in defs]
    assert len(defs) == 16
    assert "catia_create_geometrical_set" in names
    assert "catia_create_point_coord" in names
    assert "catia_create_line_2points" in names
    assert "catia_create_circle_center_radius" in names
    assert "catia_create_plane_offset" in names
    assert "catia_create_cylinder" in names
    assert "catia_list_geometrical_sets" in names
    assert "catia_create_fill" in names
    assert "catia_create_sweep" in names
    assert "catia_create_join" in names
    assert "catia_create_thicken" in names
```

### TC-6-22: GSD tools registered in server
```python
def test_gsd_tools_in_server():
    """Server hat GSD-Module registriert."""
    assert "catia_mcp.tools.gsd" in [m.__name__ for m in server._tool_modules]
```

---

## Zusammenfassung

| TC-ID | Tool | Priority |
|-------|------|----------|
| TC-6-01 | Geometrical Set valid | High |
| TC-6-02 | Geometrical Set empty | High |
| TC-6-03 | Point coord valid | High |
| TC-6-04 | Point coord non-numeric | High |
| TC-6-05 | Line 2points valid | High |
| TC-6-06 | Line 2points missing | High |
| TC-6-07 | Circle valid | High |
| TC-6-08 | Circle negative radius | High |
| TC-6-09 | Plane offset valid | High |
| TC-6-10 | Cylinder valid | High |
| TC-6-11 | List geometric sets | High |
| TC-6-12 | Plane 3points valid | High |
| TC-6-13 | Fill valid | High |
| TC-6-14 | Fill empty | High |
| TC-6-15 | Sweep valid | High |
| TC-6-16 | Offset surface valid | High |
| TC-6-17 | Join valid | High |
| TC-6-18 | Thicken valid | High |
| TC-6-19 | Rotational surface valid | Medium |
| TC-6-20 | Surface from contours valid | Medium |
| TC-6-21 | All 16 tool definitions | High |
| TC-6-22 | GSD in server | High |

**Total: 22 Tests**
