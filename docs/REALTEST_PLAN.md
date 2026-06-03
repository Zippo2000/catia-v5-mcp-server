# CATIA V5 MCP Server — Realtest Plan

> **Created:** 2026-06-03  
> **Purpose:** Live integration tests against real CATIA V5 via Hermes Agent  
> **Transport:** SSE (`python -m catia_mcp --sse --host 0.0.0.0 --port 8765`)  
> **Tester:** Hermes Agent (MCP client connected to SSE endpoint)  
> **Scope:** Alle 95 Tools über 7 Module, inkl. Error-Handling und Edge Cases

---

## 1. Setup-Voraussetzungen

### 1.1 MCP-Server starten (vor ALLEN Tests)

```bash
cd catia-v5-mcp-server
.venv\Scripts\activate
python -m catia_mcp --sse --host 0.0.0.0 --port 8765
```

- Server läuft im Vordergrund; Terminal offen lassen
- Log-Datei: `%TEMP%\catia-mcp\catia_mcp.log`
- Hermes Agent muss SSE-Endpoint `http://localhost:8765/sse` verbinden

### 1.2 CATIA V5 starten

- CATIA V5 manuell starten (oder der MCP-Server startet es automatisch via `catia_connect`)
- Keine modalen Dialoge offen lassen
- Workspace-Verzeichnis erstellen: `C:\catia_tests\` (für exportierte Dateien)

### 1.3 Hermes Agent konfigurieren

- MCP Tool Source: SSE, URL `http://localhost:8765/sse`
- Agent kann dann alle `catia_*` Tools aufrufen

---

## 2. Test-Suite-Übersicht

| Phase | Modul | Tools | Tests | Beschreibung |
|-------|-------|-------|-------|-------------|
| **P0** | Document | 10 | 12 | Verbindung, Part/Product erstellen, speichern, schließen |
| **P1** | Sketcher | 14 | 18 | 2D-Geometrie: Linien, Rechtecke, Kreise, Arcs, Splines, Constraints |
| **P2** | Part Design | 19 | 25 | Pad, Pocket, Shaft, Fillet, Hole, Patterns, Boolean, etc. |
| **P3** | GSD | 24 | 20 | Wireframe/Surface: Points, Lines, Planes, Fill, Sweep, etc. |
| **P4** | Assembly | 14 | 12 | Komponenten, Constraints, Move |
| **P5** | Measurement | 10 | 12 | Distance, Inertia, Bounding Box, Parameters |
| **P6** | Export | 4 | 8 | STEP/IGES/STL Export, Screenshots, Views |
| **P7** | Fehlerbehandlung | — | 10 | Negative Werte, ungültige Pfade, fehlende Elemente |
| **P8** | Transport/Server | — | 5 | Auto-connect, Reconnect, Tool-Routing, SSE-Stabilität |
| | | **95** | **122** | |

---

## 3. Detaillierte Testfälle

---

### Phase P0: Document Management (12 Tests)

**Ziel:** Verbindung aufbauen, Dokumente erstellen/openen/schließen, Grundfunktionalität verifizieren.

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P0-01 | `catia_connect` | `{}` | "Connected to running CATIA V5 instance" ODER "Launched new CATIA V5 instance" |
| P0-02 | `catia_new_part` | `{}` | "Created new Part document: 'Part.*'" |
| P0-03 | `catia_new_part` | `{"name": "TestPart"}` | "Created new Part document: 'TestPart'" |
| P0-04 | `catia_new_product` | `{}` | "Created new Product (assembly) document: 'Product.*'" |
| P0-05 | `catia_new_product` | `{"name": "TestAssembly"}` | "Created new Product (assembly) document: 'TestAssembly'" |
| P0-06 | `catia_list_documents` | `{}` | JSON mit mindestens 1 Dokument |
| P0-07 | `catia_get_active_document_info` | `{}` | JSON mit name, type="CATPart", bodies |
| P0-08 | `catia_save_document` | `{"file_path": "C:/catia_tests/test_part.CATPart"}` | "Document saved as: C:\catia_tests\test_part.CATPart" |
| P0-09 | `catia_close_document` | `{"save": false}` | "Document '...' closed" |
| P0-10 | `catia_open_document` | `{"file_path": "C:/catia_tests/test_part.CATPart"}` | "Opened document: '...' from C:\catia_tests\test_part.CATPart" |
| P0-11 | `catia_disconnect` | `{}` | "Disconnected from CATIA V5" |
| P0-12 | `catia_connect` (nach disconnect) | `{}` | Reconnect erfolgreich |

**Abhängigkeiten:** P0-01 zuerst. P0-08 setzt voraus, dass `C:\catia_tests\` existiert.

---

### Phase P1: Sketcher (18 Tests)

**Ziel:** 2D-Sketching: Geometrie erstellen, close, Constraints.

**Voraussetzung:** P0-01 (connect) + P0-03 (new part "TestSketch")

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P1-01 | `catia_create_sketch` | `{"plane": "xy"}` | "Sketch created on XY plane" |
| P1-02 | `catia_sketch_line` | `{"x1": 0, "y1": 0, "x2": 100, "y2": 0}` | "Line created: (0,0) to (100,0)" |
| P1-03 | `catia_sketch_line` | `{"x1": 100, "y1": 0, "x2": 100, "y2": 60}` | "Line created: (100,0) to (100,60)" |
| P1-04 | `catia_sketch_line` | `{"x1": 100, "y1": 60, "x2": 0, "y2": 60}` | "Line created: (100,60) to (0,60)" |
| P1-05 | `catia_sketch_line` | `{"x1": 0, "y1": 60, "x2": 0, "y2": 0}` | "Line created: (0,60) to (0,0)" |
| P1-06 | `catia_sketch_rectangle` | `{"x1": 120, "y1": 0, "x2": 220, "y2": 60}` | "Rectangle created: 4 lines" |
| P1-07 | `catia_sketch_centered_rectangle` | `{"cx": 0, "cy": 100, "width": 80, "height": 40}` | "Rectangle created: centered at (0,100), 80x40" |
| P1-08 | `catia_sketch_circle` | `{"cx": 150, "cy": 100, "radius": 25}` | "Circle created: center (150,100), R25" |
| P1-09 | `catia_sketch_circle` | `{"radius": 15}` | "Circle created: center (0,0), R15" (Default-Position) |
| P1-10 | `catia_sketch_arc` | `{"cx": 0, "cy": 180, "radius": 30, "start_angle": 0, "end_angle": 180}` | "Arc created: 0° to 180°, R30" |
| P1-11 | `catia_sketch_spline` | `{"points": [[0, 200], [20, 220], [40, 200], [60, 220]]}` | "Spline created: 4 control points" |
| P1-12 | `catia_sketch_point` | `{"x": 100, "y": 200}` | "Point created: (100, 200)" |
| P1-13 | `catia_sketch_get_geometry` | `{}` | JSON-Liste aller Geometrien mit Indices |
| P1-14 | `catia_sketch_constraint` | `{"type": "horizontal", "geometry_index_1": 1}` | "Constraint 'horizontal' applied" |
| P1-15 | `catia_sketch_constraint` | `{"type": "distance", "geometry_index_1": 1, "geometry_index_2": 2, "value": 100}` | "Constraint 'distance' = 100mm applied" |
| P1-16 | `catia_close_sketch` | `{}` | "Sketch closed, returned to Part Design" |
| P1-17 | `catia_create_sketch` (2. Sketch) | `{"plane": "yz"}` | "Sketch created on YZ plane" |
| P1-18 | `catia_close_sketch` | `{}` | Zweiter Sketch geschlossen |

**Validierung nach P1:** `catia_list_features` aufrufen — alle Sketches sollten gelistet sein.

---

### Phase P2: Part Design (25 Tests)

**Ziel:** 3D-Features erstellen, modifizieren, patterns, boolean.

**Voraussetzung:** P0-01 (connect) + neuer Part + geschlossener Sketch mit Rechteckprofil (oder neuer Sketch erstellen)

#### P2.A: Basis-Features

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-01 | `catia_create_sketch` | `{"plane": "xy"}` | Sketch auf XY |
| P2-02 | `catia_sketch_centered_rectangle` | `{"cx": 0, "cy": 0, "width": 100, "height": 60}` | Rechteck 100x60 |
| P2-03 | `catia_close_sketch` | `{}` | Sketch geschlossen |
| P2-04 | `catia_pad` | `{"height": 40}` | "Pad created: 40 mm (normal). Feature: 'Pad.*'" |
| P2-05 | `catia_list_features` | `{}` | Pad in Features-Liste sichtbar |
| P2-06 | `catia_list_edges` | `{}` | Alle Kanten des Blocks gelistet |

#### P2.B: Cut-Features

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-07 | `catia_create_sketch` | `{"plane": "xy"}` (auf Oberseite — ggf. Offset-Plane) | Sketch |
| P2-08 | `catia_sketch_circle` | `{"cx": 0, "cy": 0, "radius": 15}` | Kreis R15 |
| P2-09 | `catia_close_sketch` | `{}` | Sketch geschlossen |
| P2-10 | `catia_pocket` | `{"depth": 20}` | "Pocket created: 20 mm deep" |

#### P2.C: Edge-Features

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-11 | `catia_fillet` | `{"radius": 3}` | "Fillet created: R3 mm" (alle Kanten) |
| P2-12 | `catia_fillet` | `{"radius": 2, "edge_name": "<EdgeName>"}` (Name aus P2-06) | "Fillet created: R2 mm" (spezifische Kante) |
| P2-13 | `catia_chamfer` | `{"length": 5, "angle": 45}` | "Chamfer created: 5 mm at 45°" |

#### P2.D: Revolution-Features

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-14 | `catia_create_sketch` | `{"plane": "yz"}` | Sketch auf YZ |
| P2-15 | `catia_sketch_line` | `{"x1": 0, "y1": 0, "x2": 0, "y2": 30}` | Vertikale Linie (Rotationsachse) |
| P2-16 | `catia_sketch_rectangle` | `{"x1": 10, "y1": 5, "x2": 25, "y2": 25}` | Profil neben Achse |
| P2-17 | `catia_close_sketch` | `{}` | Geschlossen |
| P2-18 | `catia_shaft` | `{"angle": 360}` | "Shaft (revolution) created: 360°" |
| P2-19 | `catia_shaft` | `{"angle": 180}` | "Shaft (revolution) created: 180°" (halbe Rotation) |

#### P2.E: Hole

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-20 | `catia_create_sketch` | `{"plane": "xy"}` | Sketch |
| P2-21 | `catia_sketch_point` | `{"x": 30, "y": 20}` | Point (Lochmittelpunkt) |
| P2-22 | `catia_close_sketch` | `{}` | Geschlossen |
| P2-23 | `catia_hole` | `{"diameter": 8, "depth": 30}` | "Hole created: D8 mm, depth 30 mm" |

#### P2.F: Patterns & Mirror

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P2-24 | `catia_rect_pattern` | `{"dir1_count": 3, "dir1_spacing": 20}` | "Rectangular pattern: 3x1, spacing 20mm" |
| P2-25 | `catia_mirror` | `{"plane": "yz"}` | "Mirror created about YZ plane" |

---

### Phase P3: GSD — Wireframe & Surface (20 Tests)

**Ziel:** Geometrical Sets, Points, Lines, Planes, Surfaces.

**Voraussetzung:** P0-01 (connect) + neuer Part "TestGSD"

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P3-01 | `catia_create_geometrical_set` | `{"name": "TestGeoSet"}` | "Geometrical Set 'TestGeoSet' created" |
| P3-02 | `catia_create_point_coord` | `{"x": 0, "y": 0, "z": 0, "set_name": "TestGeoSet"}` | "Point created: (0,0,0)" |
| P3-03 | `catia_create_point_coord` | `{"x": 100, "y": 50, "z": 25, "set_name": "TestGeoSet"}` | "Point created: (100,50,25)" |
| P3-04 | `catia_create_line_2points` | `{"point1_name": "Point.1", "point2_name": "Point.2", "set_name": "TestGeoSet"}` | "Line created between Point.1 and Point.2" |
| P3-05 | `catia_create_line_point_direction` | `{"point_name": "Point.1", "direction": "x", "set_name": "TestGeoSet"}` | "Line created through Point.1 along X" |
| P3-06 | `catia_create_circle_center_radius` | `{"center_name": "Point.1", "radius": 30, "support_plane": "xy", "set_name": "TestGeoSet"}` | "Circle created: center Point.1, R30 on XY" |
| P3-07 | `catia_create_plane_offset` | `{"reference_plane": "xy", "offset": 50, "set_name": "TestGeoSet"}` | "Plane created: offset 50mm from XY" |
| P3-08 | `catia_create_plane_3points` | `{"point1_name": "Point.1", "point2_name": "Point.2", "point3_name": "<Point3>", "set_name": "TestGeoSet"}` | "Plane created through 3 points" |
| P3-09 | `catia_create_cylinder` | `{"center_name": "Point.1", "axis": "z", "radius": 20, "height": 60, "set_name": "TestGeoSet"}` | "Cylinder created: R20, H60" |
| P3-10 | `catia_create_sphere` | `{"cx": 0, "cy": 0, "cz": 100, "radius": 25, "set_name": "TestGeoSet"}` | "Sphere created: center (0,0,100), R25" |
| P3-11 | `catia_create_cone` | `{"cx": 0, "cy": 0, "cz": 150, "base_radius": 20, "height": 40, "set_name": "TestGeoSet"}` | "Cone created: base R20, H40" |
| P3-12 | `catia_create_torus` | `{"cx": 0, "cy": 0, "cz": 200, "major_radius": 30, "minor_radius": 8, "set_name": "TestGeoSet"}` | "Torus created: major R30, minor R8" |
| P3-13 | `catia_create_fill` | `{"contour_names": ["Circle.1"], "set_name": "TestGeoSet"}` | "Fill surface created" |
| P3-14 | `catia_create_sweep` | `{"spine_name": "Line.1", "section_name": "Circle.1", "set_name": "TestGeoSet"}` | "Sweep surface created" |
| P3-15 | `catia_create_offset_surface` | `{"surface_name": "Fill.1", "distance": 5, "set_name": "TestGeoSet"}` | "Offset surface created: +5mm" |
| P3-16 | `catia_create_join` | `{"surface_names": ["Fill.1", "Offset.1"], "set_name": "TestGeoSet"}` | "Join created" |
| P3-17 | `catia_create_thicken` | `{"surface_name": "Fill.1", "thickness": 2, "set_name": "TestGeoSet"}` | "Thicken created: 2mm" |
| P3-18 | `catia_create_ruled` | `{"profile1": "Line.1", "profile2": "Line.2", "set_name": "TestGeoSet"}` | "Ruled surface created" |
| P3-19 | `catia_list_geometrical_sets` | `{}` | JSON mit "TestGeoSet" und Shape-Counts |
| P3-20 | `catia_create_blend` | `{"edge_or_curve_name": "Line.1", "radius": 5, "set_name": "TestGeoSet"}` | "Blend created: R5" |

**Hinweis:** P3-08 bis P3-20 hängen von den Namen der vorher erstellten Elemente ab. Hermes Agent muss die Tool-Antworten parsen, um Element-Namen zu extrahieren.

---

### Phase P4: Assembly (12 Tests)

**Ziel:** Assembly erstellen, Komponenten hinzufügen, Constraints, Move.

**Voraussetzung:** P0-01 (connect) + mindestens 2 existierende .CATPart-Dateien aus P0/P2

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P4-01 | `catia_new_product` | `{"name": "TestAssembly"}` | "Created new Product: 'TestAssembly'" |
| P4-02 | `catia_add_new_part` | `{"name": "BasePart"}` | "Component 'BasePart' added" |
| P4-03 | `catia_add_component` | `{"file_path": "C:/catia_tests/test_part.CATPart"}` | "Component added from file" (falls P0-08 erfolgreich) |
| P4-04 | `catia_fix_constraint` | `{"component_name": "BasePart"}` | "Fix constraint applied to 'BasePart'" |
| P4-05 | `catia_list_components` | `{}` | JSON mit allen Komponenten |
| P4-06 | `catia_move_component` | `{"component_name": "BasePart", "tx": 50, "ty": 0, "tz": 0}` | "Component 'BasePart' moved by (50, 0, 0) mm" |
| P4-07 | `catia_move_component` | `{"component_name": "BasePart", "rx": 0, "ry": 90, "rz": 0}` | "Component 'BasePart' rotated 90° about Y" |
| P4-08 | `catia_coincidence_constraint` | `{"component1": "BasePart", "component2": "<Comp2>", "element1": "<elem1>", "element2": "<elem2>"}` | "Coincidence constraint created" |
| P4-09 | `catia_offset_constraint` | `{"component1": "BasePart", "component2": "<Comp2>", "offset": 10}` | "Offset constraint: 10mm" |
| P4-10 | `catia_contact_constraint` | `{"component1": "BasePart", "component2": "<Comp2>"}` | "Contact constraint created" |
| P4-11 | `catia_list_constraints` | `{}` | JSON mit allen Constraints |
| P4-12 | `catia_get_active_document_info` | `{}` | JSON mit type="CATProduct", components |

**Hinweis:** P4-03 erfordert, dass `C:/catia_tests/test_part.CATPart` existiert (aus P0-08). P4-08 bis P4-10 benötigen Element-Namen, die der Agent aus P4-05 extrahieren muss.

---

### Phase P5: Measurement (12 Tests)

**Ziel:** Distanz, Inertia, Bounding Box, Parameter messen.

**Voraussetzung:** Part mit mindestens einem Pad (aus P2)

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P5-01 | `catia_measure_distance` | `{"element1": "<Edge1>", "element2": "<Edge2>"}` | Distance in mm zurück |
| P5-02 | `catia_get_inertia` | `{}` | JSON mit volume, area, cog (ohne Dichte) |
| P5-03 | `catia_get_inertia` | `{"density": 7800}` | JSON mit volume, area, cog, mass, inertia matrix |
| P5-04 | `catia_get_bounding_box` | `{}` | JSON mit min/max coordinates |
| P5-05 | `catia_measure_angle` | `{"element1": "<Face1>", "element2": "<Face2>"}` | Angle in degrees |
| P5-06 | `catia_measure_area` | `{"element": "<Face1>"}` | Area in mm² |
| P5-07 | `catia_measure_length` | `{"element": "<Edge1>"}` | Length in mm |
| P5-08 | `catia_measure_interference` | `{"element1": "<Body1>", "element2": "<Body2>"}` | Distance (negative = interference) |
| P5-09 | `catia_get_parameters` | `{}` | JSON-Liste aller Parameter |
| P5-10 | `catia_get_parameters` | `{"filter": "Length"}` | Gefilterte Parameter-Liste |
| P5-11 | `catia_set_parameter` | `{"name": "<ParamName>", "value": 50}` | "Parameter '<ParamName>' set to 50" |
| P5-12 | `catia_update_part` | `{}` | "Part updated successfully" |

**Hinweis:** Element-Namen müssen aus `catia_list_edges` (P2-06) oder `catia_list_features` extrahiert werden.

---

### Phase P6: Export & View (8 Tests)

**Ziel:** Datei-Export, Screenshots, View-Steuerung.

**Voraussetzung:** Part mit Geometrie (aus P2)

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P6-01 | `catia_set_view` | `{"view": "isometric"}` | "View set to isometric" |
| P6-02 | `catia_set_view` | `{"view": "front"}` | "View set to front" |
| P6-03 | `catia_set_view` | `{"view": "top"}` | "View set to top" |
| P6-04 | `catia_fit_all` | `{}` | "View fitted to all geometry" |
| P6-05 | `catia_screenshot` | `{"file_path": "C:/catia_tests/screenshot.png"}` | "Screenshot saved to C:\catia_tests\screenshot.png" |
| P6-06 | `catia_screenshot` | `{"file_path": "C:/catia_tests/screenshot.jpg", "width": 1280, "height": 720}` | "Screenshot saved (1280x720)" |
| P6-07 | `catia_export` | `{"file_path": "C:/catia_tests/test_part.stp"}` | "Exported to STEP: C:\catia_tests\test_part.stp" |
| P6-08 | `catia_export` | `{"file_path": "C:/catia_tests/test_part.igs"}` | "Exported to IGES: C:\catia_tests\test_part.igs" |

**Validierung:** Nach P6-07/P6-08 prüfen, ob die Dateien auf der Festplatte existieren.

---

### Phase P7: Fehlerbehandlung (10 Tests)

**Ziel:** Validierung und Error-Handling testen.

| ID | Tool | Eingabe | Erwartetes Ergebnis |
|----|------|---------|-------------------|
| P7-01 | `catia_pad` | `{"height": -10}` | `ValueError`: "height must be positive" |
| P7-02 | `catia_pad` | `{"height": 0}` | `ValueError`: "height must be positive" |
| P7-03 | `catia_pocket` | `{"depth": -5}` | `ValueError`: "depth must be positive" |
| P7-04 | `catia_fillet` | `{"radius": -2}` | `ValueError`: "radius must be positive" |
| P7-05 | `catia_chamfer` | `{"length": -1}` | `ValueError`: "length must be positive" |
| P7-06 | `catia_sketch_circle` | `{"radius": 0}` | `ValueError`: "radius must be positive" |
| P7-07 | `catia_create_sketch` | `{"plane": "front"}` | `ValueError`: "must be one of: 'xy', 'yz', 'zx'" |
| P7-08 | `catia_mirror` | `{"plane": "invalid"}` | `ValueError`: "must be one of: 'xy', 'yz', 'zx'" |
| P7-09 | `catia_open_document` | `{"file_path": "nonexistent_file.txt"}` | `RuntimeError`: "not found" oder File-Error |
| P7-10 | `catia_export` | `{"file_path": "relative_path.stp"}` | `ValueError`: "must be an absolute path" |

---

### Phase P8: Transport & Server-Stabilität (5 Tests)

**Ziel:** MCP-Server-Verhalten, Auto-connect, SSE-Stabilität.

| ID | Aktion | Erwartetes Ergebnis |
|----|--------|-------------------|
| P8-01 | Tool aufrufen OHNE vorheriges `catia_connect` (z.B. `catia_new_part`) | Auto-connect: Server verbindet sich automatisch zu CATIA |
| P8-02 | `catia_disconnect` → dann `catia_new_part` | Auto-reconnect: Server verbindet sich wieder |
| P8-03 | `list_tools` MCP-Request | Alle 95 Tools zurück, mit korrekten `inputSchema` |
| P8-04 | Unbekanntes Tool aufrufen: `catia_nonexistent` | Error: "Unknown tool: 'catia_nonexistent'" |
| P8-05 | Schnelleffolge von 10 Tool-Calls innerhalb 10s | Alle 10 erfolgreich (Serialisierung via asyncio.Lock) |

---

## 4. Test-Ausführung für Hermes Agent

### 4.1 Empfohlene Reihenfolge

```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8
```

- **P0–P6:** Happy-Path (jeweils nacheinander, da Zustandsabhängig)
- **P7:** Fehler-Tests (können isoliert laufen; eigener Part empfohlen)
- **P8:** Transport-Tests (P8-01/02 am besten zu Beginn; P8-03/04/05 jederzeit)

### 4.2 Prometheus für jeden Test

Für jeden Test soll der Hermes Agent:
1. **Tool-Call** ausführen mit exakter Eingabe
2. **Antwort** prüfen:
   - Ist das Ergebnis ein String?
   - Enthält es das erwartete Keyword (z.B. "created", "saved", "connected")?
   - Bei JSON: Sind die erwarteten Felder vorhanden?
3. **Bei Error-Tests:** Wurde die erwartete Exception geworfen?
4. **Ergebnis** als ✅ (pass) oder ❌ (fail) protokollieren

### 4.3 Element-Namen-Extraktion

Viele Tests (P3, P4, P5) benötigen Element-Namen aus vorherigen Tool-Antworten.
Der Hermes Agent muss:
- Die Tool-Antwort parsen (z.B. `"Feature: 'Pad.1'"` → Name ist `Pad.1`)
- `catia_list_features` / `catia_list_edges` / `catia_list_geometrical_sets` nutzen, um aktuelle Namen zu ermitteln
- Die ermittelten Namen in nachfolgenden Tool-Calls verwenden

### 4.4 Cleanup nach Tests

```
catia_close_document  {"save": false}   # für alle geöffneten Dokumente
catia_close           {}                 # CATIA beenden
```

---

## 5. Erfolgskriterien

| Metrik | Ziel |
|--------|------|
| **Pass-Rate** | >= 90% aller Tests |
| **Happy-Path (P0–P6)** | >= 95% (>= 95/100 Tests) |
| **Error-Handling (P7)** | 100% (alle 10 Tests) |
| **Transport (P8)** | 100% (alle 5 Tests) |
| **SSE-Stabilität** | Kein Server-Crash während der gesamten Test-Suite |

---

## 6. Bekannte Risiken & Workarounds

| Risiko | Impact | Workaround |
|--------|--------|-----------|
| CATIA-Modal-Dialog blockiert COM | Tool-Call hängt/fehltschlägt | Manuell Dialog schließen; `catia_connect` neu aufrufen |
| Element-Namen variieren je nach CATIA-Version | P3/P4/P5-Tests scheitern | `catia_list_features`/`catia_list_edges` vor jedem Test aufrufen |
| COM-Timeout bei langsamen CATIA-Operationen | Tool-Call timeout | Wartezeit zwischen Calls; `catia_update_part` nach schweren Operationen |
| pycatia vs. win32com Backend-Unterschiede | Leichte Verhaltensvariationen | Kein Problem — beide Backend sollen funktionieren |
| `C:\catia_tests\` existiert nicht | P0-08, P4-03, P6-05/07/08 scheitern | Verzeichnis manuell erstellen oder Pfad anpassen |

---

## 7. Test-Ergebnis-Protokoll (Vorlage)

Nach Abschluss füllt der Hermes Agent diese Tabelle aus:

| Phase | Test ID | Status | Bemerkung |
|-------|---------|--------|-----------|
| P0 | P0-01 | ⬜ | |
| P0 | P0-02 | ⬜ | |
| ... | ... | ⬜ | |
| P8 | P8-05 | ⬜ | |

**Legende:** ✅ Pass, ❌ Fail, ⏭️ Skipped, ⏳ Timeout

---

## 8. Quick-Start-Checkliste für Hermes Agent

- [ ] MCP-Server gestartet: `python -m catia_mcp --sse --host 0.0.0.0 --port 8765`
- [ ] Hermes Agent mit SSE `http://localhost:8765/sse` verbunden
- [ ] Verzeichnis `C:\catia_tests\` erstellt
- [ ] Phase P0 beginnen (P0-01: `catia_connect`)
- [ ] Jede Phase nacheinander; Element-Namen aus Antworten extrahieren
- [ ] Ergebnisse protokollieren
- [ ] Am Ende: `catia_close` aufrufen
