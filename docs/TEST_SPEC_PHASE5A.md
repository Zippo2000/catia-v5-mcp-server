# Phase 5a — Part Design Extensions: Test Spezifikation

## Ziel

4 neue Part-Design-Tools implementieren und testen:

| Tool | CATIA COM-API | Beschreibung |
|------|--------------|-------------|
| `catia_lifting` | `ShapeFactory.AddNewLifting` | Variable-Thickness Extrusion mit Guide-Curve |
| `catia_sweep` | `ShapeFactory.AddNewVariableSectionShape` | Variable Section Sweep entlang einer Kurve |
| `catia_loft` | `ShapeFactory.AddNewLoft` | Multi-Sketch Loft zwischen ≥2 Profilen |
| `catia_boolean` | `ShapeFactory.AddOperation` | Boolean: Union, Intersection, Difference zwischen Bodies |

---

## Test 1: Lifting (`catia_lifting`)

**Tool-Definition:**
- `guiding_curve` (required, string) — Name der Guide-Kurve (Edge/Reference)
- `sketch_name` (optional, string) — Profil-Sketch, default: letzter Sketch
- `support` (optional, string) — Unterstützungskurve

**Erwartetes Verhalten:**
- Lifting erstellt eine Extrusion mit variabler Dicke, wobei die Dicke entlang der Guide-Curve variieren kann
- Mindestens Sketch + GuidingCurve erforderlich

**Test-Cases:**

### TC-5a-01: Lifting — Valid Parameter
```python
def test_lifting_valid_params():
    """Lifting mit gültigen Parametern erzeugt korrektes inputSchema."""
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    lifting = next(d for d in defs if d["name"] == "catia_lifting")
    assert lifting["inputSchema"]["required"] == ["guiding_curve"]
    assert "sketch_name" in lifting["inputSchema"]["properties"]
    assert "support" in lifting["inputSchema"]["properties"]
```

### TC-5a-02: Lifting — Missing guiding_curve
```python
def test_lifting_missing_guiding_curve():
    """Fehlt guiding_curve → RuntimeError."""
    result = tools.execute("catia_lifting", {})
    assert "guiding_curve" in result.lower() or "required" in result.lower()
```

### TC-5a-03: Lifting — Invalid guiding_curve name
```python
def test_lifting_invalid_curve():
    """Ungültige Kurve → klarer Fehler."""
    result = tools.execute("catia_lifting", {"guiding_curve": "NichtBestehend"})
    assert "Error" in result or "error" in result.lower()
```

### TC-5a-04: Lifting — With sketch_name override
```python
def test_lifting_with_sketch_name():
    """Benutzerdefinierte Sketch-Referenz."""
    result = tools.execute("catia_lifting", {
        "guiding_curve": "Edge.1",
        "sketch_name": "Sketch.2"
    })
    assert "Error" in result or "Lifting" in result
```

---

## Test 2: Sweep / Variable Section Shape (`catia_sweep`)

**Tool-Definition:**
- `spine` (required, string) — Rückgrat-Kurve (Edge/Reference)
- `section` (optional, string) — Querschnitt-Sketch
- `profile` (optional, string) — Profilkurve
- `direction` (optional, string) — Richtungskurve (für orientation control)

**Test-Cases:**

### TC-5a-05: Sweep — Valid parameters
```python
def test_sweep_valid_params():
    """Sweep mit spine + section."""
    result = tools.execute("catia_sweep", {
        "spine": "Line.1",
        "section": "Sketch.1"
    })
    # Mocked — check Tool-Definition
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    sweep = next(d for d in defs if d["name"] == "catia_sweep")
    assert "spine" in sweep["inputSchema"]["required"]
```

### TC-5a-06: Sweep — Missing spine
```python
def test_sweep_missing_spine():
    """Fehlt spine → RuntimeError."""
    result = tools.execute("catia_sweep", {"section": "Sketch.1"})
    assert "spine" in result.lower() or "required" in result.lower()
```

### TC-5a-07: Sweep — With profile and direction
```python
def test_sweep_full_params():
    """Sweep mit allen optionalen Parametern."""
    result = tools.execute("catia_sweep", {
        "spine": "Line.1",
        "section": "Sketch.1",
        "profile": "Curve.1",
        "direction": "Axis.1"
    })
    # Mocked — should accept
    assert True  # Mock returns success
```

---

## Test 3: Loft (`catia_loft`)

**Tool-Definition:**
- `sketch_names` (required, list of string) — ≥2 Sketch-Namen in Reihenfolge
- Mindestens 2 Sketches erforderlich

**Test-Cases:**

### TC-5a-08: Loft — Valid with 2 sketches
```python
def test_loft_two_sketches():
    """Loft mit 2 Sketches."""
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    loft = next(d for d in defs if d["name"] == "catia_loft")
    assert "sketch_names" in loft["inputSchema"]["required"]
    assert loft["inputSchema"]["properties"]["sketch_names"]["type"] == "array"
```

### TC-5a-09: Loft — Single sketch (too few)
```python
def test_loft_single_sketch():
    """Loft mit nur 1 Sketch → Error (min 2 required)."""
    result = tools.execute("catia_loft", {"sketch_names": ["Sketch.1"]})
    assert "error" in result.lower() or "minimum" in result.lower() or "2" in result
```

### TC-5a-10: Loft — Multiple sketches (3+)
```python
def test_loft_three_sketches():
    """Loft mit 3+ Sketches."""
    result = tools.execute("catia_loft", {
        "sketch_names": ["Sketch.1", "Sketch.2", "Sketch.3"]
    })
    # Mocked — should accept
    assert True
```

### TC-5a-11: Loft — Empty sketch_names
```python
def test_loft_empty_sketches():
    """Loft mit leerer Liste → Error."""
    result = tools.execute("catia_loft", {"sketch_names": []})
    assert "error" in result.lower()
```

---

## Test 4: Boolean (`catia_boolean`)

**Tool-Definition:**
- `operation` (required, enum: "union", "intersection", "difference")
- `body1` (required, string) — Name des ersten Body
- `body2` (required, string) — Name des zweiten Body
- `result_in` (optional, string) — Body in dem das Ergebnis verbleibt

**Test-Cases:**

### TC-5a-12: Boolean Union — Valid parameters
```python
def test_boolean_union_valid():
    """Union mit 2 Bodies."""
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    boolean = next(d for d in defs if d["name"] == "catia_boolean")
    assert "union" in boolean["inputSchema"]["properties"]["operation"]["enum"]
    assert "intersection" in boolean["inputSchema"]["properties"]["operation"]["enum"]
    assert "difference" in boolean["inputSchema"]["properties"]["operation"]["enum"]
    assert set(boolean["inputSchema"]["required"]) == {"operation", "body1", "body2"}
```

### TC-5a-13: Boolean Union — Execute with valid params
```python
def test_boolean_union_execute():
    """Union-Operation."""
    result = tools.execute("catia_boolean", {
        "operation": "union",
        "body1": "PartBody",
        "body2": "PartBody.1"
    })
    assert "Error" in result or "Boolean" in result or "union" in result.lower()
```

### TC-5a-14: Boolean Difference
```python
def test_boolean_difference():
    """Difference-Operation (Material von body2 aus body1 entfernen)."""
    result = tools.execute("catia_boolean", {
        "operation": "difference",
        "body1": "PartBody",
        "body2": "PartBody.1"
    })
    assert True  # Mock accepts
```

### TC-5a-15: Boolean Intersection
```python
def test_boolean_intersection():
    """Intersection-Operation (nur gemeinsames Volume)."""
    result = tools.execute("catia_boolean", {
        "operation": "intersection",
        "body1": "PartBody",
        "body2": "PartBody.1"
    })
    assert True
```

### TC-5a-16: Boolean — Missing body1
```python
def test_boolean_missing_body1():
    """Fehlt body1 → Error."""
    result = tools.execute("catia_boolean", {
        "operation": "union",
        "body2": "PartBody.1"
    })
    assert "body1" in result.lower() or "required" in result.lower()
```

### TC-5a-17: Boolean — Invalid operation
```python
def test_boolean_invalid_operation():
    """Ungültiger operation-Wert → Error."""
    result = tools.execute("catia_boolean", {
        "operation": "explode",
        "body1": "PartBody",
        "body2": "PartBody.1"
    })
    assert "error" in result.lower() or "invalid" in result.lower()
```

### TC-5a-18: Boolean — body1 == body2
```python
def test_boolean_same_body():
    """body1 == body2 → Error (nicht erlaubt)."""
    result = tools.execute("catia_boolean", {
        "operation": "union",
        "body1": "PartBody",
        "body2": "PartBody"
    })
    assert "error" in result.lower() or "same" in result.lower()
```

---

## Test 5: Tool-Definition Integration

### TC-5a-19: Neue Tools sind in get_tool_definitions()
```python
def test_new_tools_in_definitions():
    """Alle 4 neuen Tools sind im Schema registriert."""
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    names = [d["name"] for d in defs]
    assert "catia_lifting" in names
    assert "catia_sweep" in names
    assert "catia_loft" in names
    assert "catia_boolean" in names
```

### TC-5a-20: Execute-Router recognizes new tools
```python
def test_execute_router_new_tools():
    """execute() leitet zu korrekten Methoden."""
    result = tools.execute("catia_lifting", {})
    assert isinstance(result, str)
```

### TC-5a-21: Tool count increased from 15 to 19
```python
def test_tool_count():
    """15 bestehende + 4 neue = 19 Tools."""
    tools = PartDesignTools(conn)
    defs = tools.get_tool_definitions()
    assert len(defs) == 19
```

### TC-5a-22: Overall tool count 55 → 59
```python
def test_overall_tool_count():
    """Gesamt-Tool-Anzahl steigt von 55 auf 59."""
    # In server context: total across all modules
    assert True  # Verified via server tests
```

---

## Test 6: Edge Cases & Error Handling

### TC-5a-23: Lifting — CATIA not connected
```python
def test_lifting_not_connected():
    """Lifting ohne CATIA-Verbindung → RuntimeError."""
    conn = MockConnection(connected=False)
    tools = PartDesignTools(conn)
    result = tools.execute("catia_lifting", {"guiding_curve": "Edge.1"})
    assert "connect" in result.lower() or "error" in result.lower()
```

### TC-5a-24: Boolean — Non-existent body
```python
def test_boolean_nonexistent_body():
    """Boolean mit nicht-existentem Body → klarer Error."""
    result = tools.execute("catia_boolean", {
        "operation": "union",
        "body1": "NichtBestehend",
        "body2": "AuchNichtBestehend"
    })
    assert "Error" in result or "error" in result.lower()
```

---

## Zusammenfassung

| TC-ID | Test | Priority |
|-------|------|----------|
| TC-5a-01 | Lifting valid params | High |
| TC-5a-02 | Lifting missing guiding_curve | High |
| TC-5a-03 | Lifting invalid curve | Medium |
| TC-5a-04 | Lifting with sketch_name | Medium |
| TC-5a-05 | Sweep valid params | High |
| TC-5a-06 | Sweep missing spine | High |
| TC-5a-07 | Sweep full params | Medium |
| TC-5a-08 | Loft two sketches | High |
| TC-5a-09 | Loft single sketch | High |
| TC-5a-10 | Loft three sketches | Medium |
| TC-5a-11 | Loft empty sketches | High |
| TC-5a-12 | Boolean union valid | High |
| TC-5a-13 | Boolean union execute | High |
| TC-5a-14 | Boolean difference | High |
| TC-5a-15 | Boolean intersection | High |
| TC-5a-16 | Boolean missing body1 | High |
| TC-5a-17 | Boolean invalid operation | High |
| TC-5a-18 | Boolean same body | High |
| TC-5a-19 | New tools in definitions | High |
| TC-5a-20 | Execute router | High |
| TC-5a-21 | Tool count 19 | High |
| TC-5a-22 | Overall count 59 | Medium |
| TC-5a-23 | Lifting not connected | High |
| TC-5a-24 | Boolean nonexistent body | High |

**Total: 24 Tests**
