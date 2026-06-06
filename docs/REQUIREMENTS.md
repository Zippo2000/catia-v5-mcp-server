# CATIA V5 MCP Server — ASPICE Requirements Specification

| Feld | Wert |
|------|------|
| **Dokument-ID** | REQ-001 |
| **Version** | 1.9 |
| **Status** | Freigegeben |
| **Letzte Änderung** | 2026-06-06 |
| **Projekt** | catia-v5-mcp-server |
| **Software-Version** | 0.1.0 |

---

## 1. Einleitung

### 1.1 Zweck

Diese Spezifikation definiert die funktionalen und nicht-funktionalen Anforderungen an den
**CATIA V5 MCP Server** (nachfolgend „System"). Das System stellt einen MCP-Server (Model Context
Protocol) bereit, der es LLM-Clients ermöglicht, CATIA V5 CAD-Operationen über eine standardisierte
Tool-Interface zu steuern.

### 1.2 Geltungsbereich

Das System ist ein Python-Package (`catia-v5-mcp-server`), das als MCP-Server agiert und über
zwei Transport-Modi (stdio, SSE) mit LLM-Clients kommuniziert. Die CAD-Operationen werden
über **pycatia** (primär) mit **win32com** als Fallback an CATIA V5 delegiert.

### 1.3 Begriffe und Abkürzungen

| Begriff | Definition |
|---------|-----------|
| **MCP** | Model Context Protocol — Standard-Protokoll für LLM-Tool-Integration |
| **LLM-Client** | Client-Anwendung, die einen MCP-Server konsumiert (z.B. Claude Desktop, LM Studio) |
| **COM** | Component Object Model — Windows-Automation-Standard |
| **Part** | Einzelnes 3D-Körperteil in CATIA V5 |
| **Product** | Assembly (Baugruppe) in CATIA V5 |
| **Sketch** | 2D-Geometrie, die als Profil für 3D-Features dient |
| **Feature** | 3D-Operation (Pad, Pocket, Fillet, etc.) |
| **Constraint** | Geometrische/physikalische Bedingung im Sketch oder Assembly |
| **SSE** | Server-Sent Events — HTTP-basierter单向-Messaging-Transport |
| **stdio** | Standard Input/Output — lokale Pipe-basierte Kommunikation |
| **SMART** | Specific, Measurable, Achievable, Relevant, Time-bound |

### 1.4 Normen und Referenzen

| Ref | Norm | Relevanz |
|-----|------|----------|
| R1 | ASPICE SYS.2 | Software Requirements Engineering |
| R2 | ISO/IEC/IEEE 29148 | Requirements & Specification |
| R3 | MCP Specification (v2024.11) | Model Context Protocol Standard |
| R4 | Dassault Systèmes CATIA V5 Automation API | COM-Interface-Spezifikation |
| R5 | Python PEP 8 | Python Code Style |

---

## 2. Gesamte Anforderungen

### 2.1 Allgemeine Beschreibung

#### 2.1.1 Produkt-Perspektive

```
┌──────────────┐  MCP-Protokoll  ┌──────────────┐  pycatia / win32com  ┌──────────┐
│  LLM-Client  │  ──────────────►│  MCP-Server  │  ───────────────────►│ CATIA V5 │
│              │  (stdio / SSE)  │ (Python)     │  (Dual-Backend)      │ (Windows)│
└──────────────┘                  └──────────────┘                      └──────────┘
```

Das System ist ein **Middleware-Server** zwischen LLM-Clients und CATIA V5. Es übersetzt
MCP-Tool-Calls in COM-Aufrufe und formatiert COM-Ergebnisse als MCP-Tool-Responses.

#### 2.1.2 Produkt-Funktionen (Übersicht)

| Kategorie | Tool-Anzahl | Beschreibung |
|-----------|------------|-------------|
| Dokument-Verwaltung | 10 | Erstellen, Öffnen, Speichern, Schließen von Part/Product/Drawing |
| Sketcher | 18 | 2D-Geometrie-Erstellung (inkl. Conics, Trim, Mirror, Construction Element) und -Bearbeitung |
| Part Design | 23 | 3D-Feature-Erstellung (Pad, Pocket, Fillet, Lifting, Sweep, Loft, Boolean, Rib, Slot, Stiffener, Split Body, etc.) |
| Assembly | 15 | Baugruppen-Verwaltung und Constraints (inkl. Contact, Distance, Tangent, Ground, Remove) |
| Measurement | 10 | Abstand, Trägheit, Bounding Box, Parameter, Winkel, Fläche, Länge, Interferenz |
| Export & View | 4 | Export (STEP/IGES/STL), Screenshots, View |
| GSD (Wireframe & Surface) | 32 | Point, Line, Circle, Plane, Cylinder, Fill, Sweep, Join, Sphere, Cone, Torus, Ruled, Blend, Split, Extend, Trim, Mirror, Tabulated Cylinder, Point on Curve, Point Intersection, Line Tangent, Line Normal, Plane Parallel, Plane Tangent |
| **Total** | **111** | — |

#### 2.1.3 Nutzerklassen und Charakteristiken

| Nutzerklasse | Beschreibung | Anforderungen |
|-------------|-------------|--------------|
| CAD-Ingenieur | Nutzt CATIA V5 professionell | Vollständige Feature-Abdeckung, Korrektheit |
| Entwickler | Integriert MCP-Server | Stabile API, klare Dokumentation |
| LLM-User | Chat-basierte CAD-Interaktion | Fehler-resilient, klare Error-Messages |

#### 2.1.4 Betriebsumgebung

| Komponente | Anforderung |
|-----------|-----------|
| **Betriebssystem** | Windows 10/11 (64-bit) — COM-Automation erfordert Windows |
| **Python** | Version ≥ 3.10 |
| **CATIA V5** | Version R2016+ mit gültiger Lizenz |
| **MCP-Client** | Beliebiger MCP-kompatibler Client (Claude Desktop, LM Studio, vLLM.rs, etc.) |
| **Netzwerk** | Für SSE-Modus: TCP-Port 8765 (default) muss erreichbar sein |

#### 2.1.5 Einschränkungen

| Einschränkung | Begründung |
|--------------|-----------|
| COM-Automation nur unter Windows | Plattform-Beschränkung von win32com/pycatia |
| Single-Threaded COM-Zugriff | CATIA COM-API ist nicht thread-safe |
| Keine CATIA-Zeichnungsautomatisierung | Aktuell kein Drawing-Tool-Set implementiert |

#### 2.1.6 Verwendungsannahmen

1. CATIA V5 ist installiert und lizenziert auf dem Windows-System.
2. Der Nutzer hat administrative Rechte zum Starten von COM-Automation.
3. Der LLM-Client unterstützt das MCP-Protokoll.
4. Für SSE-Modus: TCP-Port ist von Client aus erreichbar (Firewall).

---

## 3. Detaillierte Anforderungen

### 3.1 Funktionale Anforderungen

#### FR-01: MCP-Server-Grundfunktionalität

**FR-01.1** Das System SOLL sich als MCP-Server mit dem Namen `catia-v5-mcp` registrieren.

> *Verifizierbarkeit:* Der Server antwortet auf `initialize`-Request mit `serverInfo.name == "catia-v5-mcp"`.

**FR-01.2** Das System SOLL mindestens 111 Tools implementieren und über `tools/list` verfügbar machen.

> *Verifizierbarkeit:* `tools/list`-Response enthält ≥55 Einträge mit korrekten `name`, `description`, `inputSchema`.

**FR-01.3** Das System SOLL auf `tools/call`-Requests das angegebene Tool ausführen und ein strukturiertes Text-Ergebnis zurückgeben.

> *Verifizierbarkeit:* Jeder `tools/call`-Request mit gültigen Parametern resultiert in einer `text`-Content-Response.

**FR-01.4** Das System SOLL unbekannte Tool-Namen mit einer klaren Fehlermeldung ablehnen.

> *Verifizierbarkeit:* `tools/call` mit nicht-existentem Tool-Name resultiert in Error-Text, der den Tool-Namen enthält.

---

#### FR-02: Transport-Modi

**FR-02.1** Das System SOLL einen stdio-Transport-Modus unterstützen, bei dem MCP-JSON-RPC über stdin/stdout erfolgt.

> *Verifizierbarkeit:* Start mit `python -m catia_mcp` (default) ermöglicht Kommunikation via stdin/stdout.

**FR-02.2** Das System SOLL einen SSE-Transport-Modus unterstützen, der zwei HTTP-Endpoints bereitstellt:
- `GET /sse` — SSE-Stream (Server → Client)
- `POST /messages/` — Client-Nachrichten (Client → Server)

> *Verifizierbarkeit:* Start mit `python -m catia_mcp --sse` öffnet HTTP-Endpoints auf konfigurierbarem Host/Port.

**FR-02.3** Das System SOLL den SSE-Bind-Host per `--host` CLI-Argument konfigurierbar machen (Standard: `0.0.0.0`).

> *Verifizierbarkeit:* `--host 127.0.0.1` bindet SSE-Server auf localhost.

**FR-02.4** Das System SOLL den SSE-Port per `--port` CLI-Argument konfigurierbar machen (Standard: `8765`).

> *Verifizierbarkeit:* `--port 9000` bindet SSE-Server auf Port 9000.

**FR-02.5** Die Transport-Modus-Argumente `--stdio` und `--sse` SIND mutually exclusive.

> *Verifizierbarkeit:* Kombination `--stdio --sse` resultiert in Argument-Parser-Fehler.

---

#### FR-03: CATIA-Verbindung

**FR-03.1** Das System SOLL bei `catia_connect` zuerst versuchen, eine existierende CATIA-Instanz zu erreichen.

> *Verifizierbarkeit:* Bei laufender CATIA-Instanz verwendet `GetActiveObject` statt `CreateObject`.

**FR-03.2** Das System SOLL bei fehlender CATIA-Instanz eine neue Instanz starten.

> *Verifizierbarkeit:* Bei nicht-laufender CATIA führt `catia_connect` zum Start von `CATIA.Application`.

**FR-03.3** Das System SOLL nach COM-Verbindungsabbruch eine erneute Verbindung durch `ensure_connected()` ermöglichen.

> *Verifizierbarkeit:* Nach `disconnect`+neuem `connect` ist `is_connected` == True.

**FR-03.4** Das System SOLL bei `catia_disconnect` die COM-Referenz freigeben, aber CATIA nicht beenden.

> *Verifizierbarkeit:* Nach `catia_disconnect` ist `is_connected` == False, CATIA-Prozess läuft weiter.

**FR-03.5** Das System SOLL bei `catia_close` CATIA vollständig beenden (einschließlich aller offenen Dokumente).

> *Verifizierbarkeit:* Nach `catia_close` ist der CATIA-Prozess nicht mehr lauffähig.

**FR-03.6** Das System SOLL doppelte Verbindungsversuche durch einen Lock-Mechanismus verhindern.

> *Verifizierbarkeit:* Während eines laufenden `connect()`-Aufrufs resultiert ein neuer `connect()` in `RuntimeError`.

**FR-03.7** Das System SOLL automatisch bei jedem Tool-Call (außer `catia_connect`, `catia_disconnect`, `catia_close`) eine aktive CATIA-Verbindung sicherstellen.

> *Verifizierbarkeit:* Aufruf eines Tools ohne vorherigen `catia_connect` löst impliziten Connect aus.

---

#### FR-04: Dokument-Verwaltung (10 Tools)

**FR-04.1** `catia_new_part` SOLL ein neues Part-Dokument erstellen und optional benennen.

> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Nach Aufruf ist ein neues Part-Dokument aktiv.

**FR-04.2** `catia_new_product` SOLL ein neues Product-Dokument (Assembly) erstellen und optional benennen.

> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Nach Aufruf ist ein neues Product-Dokument aktiv.

**FR-04.3** `catia_open_document` SOLL ein bestehendes CATIA-Dokument (.CATPart, .CATProduct, .CATDrawing) öffnen.

> *Parameter:* `file_path` (required, string). *Verifizierbarkeit:* Dokument wird als ActiveDocument geladen.

**FR-04.4** `catia_save_document` SOLL das aktive Dokument speichern (optional als neuen Pfad).

> *Parameter:* `file_path` (optional, string). *Verifizierbarkeit:* Datei existiert nach Aufruf.

**FR-04.5** `catia_close_document` SOLL das aktive Dokument schließen (optional mit Speichern).

> *Parameter:* `save` (optional, bool). *Verifizierbarkeit:* Dokument ist nicht mehr in der Document-Liste.

**FR-04.6** `catia_list_documents` SOLL alle offenen Dokumente mit Typ und Pfad auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen, Typen und Pfade aller offenen Dokumente.

**FR-04.7** `catia_get_active_document_info` SOLL detaillierte Informationen über das aktive Dokument zurückgeben.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Name, Typ, Pfad, Part Bodies, Features, etc.

---

#### FR-05: Sketcher (18 Tools)

**FR-05.1** `catia_create_sketch` SOLL einen 2D-Sketch auf einer Referenzebene (xy, yz, zx) erstellen.

> *Parameter:* `plane` (optional, enum: xy/yz/zx, default: xy). *Verifizierbarkeit:* Sketch ist aktiv und editierbar.

**FR-05.2** `catia_close_sketch` SOLL den aktiven Sketch schließen und zur Part Design-Umgebung zurückkehren.

> *Parameter:* keine. *Verifizierbarkeit:* Kein aktiver Sketch, 3D-Features können erstellt werden.

**FR-05.3** `catia_sketch_line` SOLL eine Linie von (x1,y1) nach (x2,y2) zeichnen.

> *Parameter:* `x1,y1,x2,y2` (required, number, mm). *Verifizierbarkeit:* Line-Element existiert im Sketch.

**FR-05.4** `catia_sketch_rectangle` SOLL ein Rechteck durch zwei Eckpunkte zeichnen.

> *Parameter:* `x1,y1,x2,y2` (required, number, mm). *Verifizierbarkeit:* 4 Line-Elemente existieren.

**FR-05.5** `catia_sketch_centered_rectangle` SOLL ein zentriertes Rechteck erstellen.

> *Parameter:* `cx,cy` (optional, number), `width,height` (required, number, mm). *Verifizierbarkeit:* Rechteck ist am Zentrum zentriert.

**FR-05.6** `catia_sketch_circle` SOLL einen Kreis mit gegebenem Radius zeichnen.

> *Parameter:* `cx,cy` (optional, number), `radius` (required, number > 0, mm). *Verifizierbarkeit:* Circle-Element existiert.

**FR-05.7** `catia_sketch_arc` SOLL einen Kreisbogen erstellen.

> *Parameter:* `cx,cy,radius,start_angle,end_angle` (required, number). *Verifizierbarkeit:* Arc-Element existiert mit korrekten Winkeln.

**FR-05.8** `catia_sketch_spline` SOLL eine Spline durch Kontrollpunkte erstellen.

> *Parameter:* `points` (required, list of [x,y]), `closed` (optional, bool). *Verifizierbarkeit:* Spline-Element durch alle Punkte.

**FR-05.9** `catia_sketch_point` SOLL einen Punkt im Sketch erstellen.

> *Parameter:* `x,y` (required, number, mm). *Verifizierbarkeit:* Point-Element existiert.

**FR-05.10** `catia_sketch_constraint` SOLL eine geometrische oder dimensionale Constraint hinzufügen.

> *Parameter:* `type` (required, enum), `value`, `geometry_index_1`, `geometry_index_2` (optional). *Verifizierbarkeit:* Constraint ist in Sketch aktiv.

**FR-05.11** `catia_sketch_get_geometry` SOLL alle Geometrie-Elemente im aktiven Sketch auflisten.
**FR-05.12** `catia_sketch_ellipse` SOLL eine Ellipse im Sketch zeichnen.

> *Parameter:* `cx`, `cy` (optional), `major_axis`, `minor_axis` (required, > 0), `angle` (optional). *Verifizierbarkeit:* Ellipse-Element existiert im Sketch.

**FR-05.13** `catia_sketch_hyperbola` SOLL eine Hyperbel im Sketch zeichnen.

> *Parameter:* `cx`, `cy` (optional), `transverse_axis`, `conjugate_axis` (required, > 0), `angle` (optional). *Verifizierbarkeit:* Hyperbola-Element existiert im Sketch.

**FR-05.14** `catia_sketch_parabola` SOLL eine Parabel im Sketch zeichnen.

> *Parameter:* `cx`, `cy` (optional), `focal_length` (required, > 0), `angle` (optional). *Verifizierbarkeit:* Parabola-Element existiert im Sketch.

**FR-05.15** `catia_sketch_trim` SOLL eine Sketch-Kurve mit einer anderen Kurve als Schneidelement trimmen.

> *Parameter:* `curve_name`, `trim_tool` (required). *Verifizierbarkeit:* Kurve ist am Schneidelement getrimmt.

**FR-05.16** `catia_sketch_mirror` SOLL ein Sketch-Element an einer Achse spiegeln.

> *Parameter:* `element_name`, `mirror_axis` (required). *Verifizierbarkeit:* Gespiegeltes Element existiert im Sketch.

**FR-05.17** `catia_sketch_construction_element` SOLL ein Sketch-Element in ein Konstruktionselement (Hilfslinie) umwandeln.

> *Parameter:* `element_name` (required). *Verifizierbarkeit:* Element ist als Konstruktionselement markiert.

**FR-05.18** `catia_sketch_get_geometry` SOLL alle Geometrie-Elemente im aktiven Sketch auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Indizes, Typen und Eigenschaften aller Elemente.

---

#### FR-06: Part Design (23 Tools)

**FR-06.1** `catia_pad` SOLL einen Pad (Extrusion) aus dem letzten oder benannten Sketch erstellen.

> *Parameter:* `height` (required, number > 0, mm), `direction` (optional, enum: normal/reverse/both), `symmetric` (optional, bool), `sketch_name` (optional, string). *Verifizierbarkeit:* Solid-Feature existiert mit korrekter Höhe.

**FR-06.2** `catia_pocket` SOLL eine Aussparung (Cut Extrusion) aus dem Sketch erstellen.

> *Parameter:* `depth` (required, number > 0, mm), `direction` (optional, enum), `sketch_name` (optional, string). *Verifizierbarkeit:* Material wird entfernt.

**FR-06.3** `catia_shaft` SOLL eine Drehung (Revolution) um eine Achse erstellen.

> *Parameter:* `angle` (optional, number, default 360, degrees), `sketch_name` (optional, string). *Verifizierbarkeit:* Rotations-Feature existiert.

**FR-06.4** `catia_groove` SOLL eine Dreh-Aussparung erstellen.

> *Parameter:* `angle` (optional, number), `sketch_name` (optional, string). *Verifizierbarkeit:* Rotations-Feature mit Materialentfernung.

**FR-06.5** `catia_fillet` SOLL Rundungen auf Kanten erstellen.

> *Parameter:* `radius` (required, number > 0, mm), `edge_name` (optional, string). *Verifizierbarkeit:* Fillet-Feature auf Kante(n) existiert.

**FR-06.6** `catia_chamfer` SOLL Fasen auf Kanten erstellen.

> *Parameter:* `length` (required, number > 0, mm), `angle` (optional, number, default 45, degrees), `edge_name` (optional, string). *Verifizierbarkeit:* Chamfer-Feature existiert.

**FR-06.7** `catia_hole` SOLL ein Loch erstellen (einfach, Senkkopf, Zentrierbohrung).

> *Parameter:* `diameter` (required, number > 0), `depth` (required, number > 0), `type` (optional, enum), `threaded` (optional, bool), `sketch_name` (optional, string). *Verifizierbarkeit:* Hole-Feature existiert.

**FR-06.8** `catia_rect_pattern` SOLL ein Feature in einem rechteckigen Muster duplizieren.

> *Parameter:* `dir1_count`, `dir1_spacing` (required), `dir2_count`, `dir2_spacing` (optional), `feature_name` (required, string). *Verifizierbarkeit:* Pattern-Feature existiert mit korrekter Instanzanzahl.

**FR-06.9** `catia_circ_pattern` SOLL ein Feature um eine Achse dreh-symmetrisch duplizieren.

> *Parameter:* `count` (required, int > 0), `angular_spacing` (optional, number), `feature_name` (required, string). *Verifizierbarkeit:* Pattern-Feature mit korrekter Anzahl.

**FR-06.10** `catia_mirror` SOLL ein Feature oder Body an einer Ebene spiegeln.

> *Parameter:* `plane` (required, enum: xy/yz/zx), `feature_name` (optional, string; default: letztes Feature). *Verifizierbarkeit:* Gespiegeltes Feature existiert.

**FR-06.11** `catia_shell` SOLL ein Part aushöhlen.

> *Parameter:* `thickness` (required, number > 0, mm), `faces_to_remove` (optional, list of strings). *Verifizierbarkeit:* Hollow-Feature existiert mit gegebener Wandstärke.

**FR-06.12** `catia_draft` SOLL Ziehkanten anwenden.

> *Parameter:* `angle` (required, number), `face_name` (optional, string), `pulling_direction` (optional, string). *Verifizierbarkeit:* Draft-Feature existiert.

**FR-06.13** `catia_thickness` SOLL Fläche verschieben.

> *Parameter:* `offset` (required, number, mm), `face_name` (optional, string). *Verifizierbarkeit:* Thickness-Feature existiert.

**FR-06.14** `catia_list_features` SOLL alle Features im aktiven Part Body auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen und Typen aller Features.

**FR-06.15** `catia_list_edges` SOLL alle Kanten des aktiven Solid auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Kanten-Namen für Fillet/Chamfer-Selektion.

**FR-06.16** `catia_lifting` SOLL eine variable Extrusion entlang einer Kurve erstellen.

> *Parameter:* `guiding_curve` (required), `sketch_name` (optional), `support` (optional). *Verifizierbarkeit:* Lifting-Feature existiert.

**FR-06.17** `catia_sweep` SOLL eine Variable Section Sweep (VSS) erstellen.

> *Parameter:* `spine`, `section` (required), `profile`, `direction` (optional). *Verifizierbarkeit:* Sweep-Feature existiert.

**FR-06.18** `catia_loft` SOLL eine Loft-Interpolation zwischen 2+ Sketchen erstellen.

> *Parameter:* `sketch_names` (required, list). *Verifizierbarkeit:* Loft-Feature existiert.

**FR-06.19** `catia_boolean` SOLL eine Boolean-Operation (Union, Difference, Intersection) zwischen zwei Bodies durchführen.

> *Parameter:* `operation` (required, enum: union/difference/intersection), `body1`, `body2` (required). *Verifizierbarkeit:* Boolean-Feature existiert.

**FR-06.20** `catia_rib` SOLL ein Rib-Feature aus einem Sketch-Profil in einer Richtung erstellen.

> *Parameter:* `direction` (required), `sketch_name` (optional). *Verifizierbarkeit:* Rib-Feature existiert.

**FR-06.21** `catia_slot` SOLL ein Slot-Feature (Nut) aus einem Sketch-Profil erstellen.

> *Parameter:* `sketch_name` (optional). *Verifizierbarkeit:* Slot-Feature existiert.

**FR-06.22** `catia_stiffener` SOLL ein Stiffener-Feature entlang eines Sketch-Profils auf einer Supportfläche erstellen.

> *Parameter:* `direction` (required), `sketch_name` (optional), `support` (optional). *Verifizierbarkeit:* Stiffener-Feature existiert.

**FR-06.23** `catia_split_body` SOLL einen Body mit einer Ebene, Oberfläche oder einem Part aufteilen.

> *Parameter:* `tool_name` (required), `keep_part` (optional). *Verifizierbarkeit:* Split-Feature existiert.

---

#### FR-07: Assembly (15 Tools)

**FR-07.1** `catia_add_component` SOLL eine existierende .CATPart oder .CATProduct als Komponente hinzufügen.

> *Parameter:* `file_path` (required, string). *Verifizierbarkeit:* Komponente ist in Product-Tree.

**FR-07.2** `catia_add_new_part` SOLL ein neues Part direkt in der Assembly erstellen.

> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Neues Part-Komponente existiert.

**FR-07.3** `catia_fix_constraint` SOLL eine Komponente fixieren (alle Freiheitsgrade entfernen).

> *Parameter:* `component_name` (required, string). *Verifizierbarkeit:* Fix-Constraint existiert.

**FR-07.4** `catia_coincidence_constraint` SOLL eine Coincidence-Constraint zwischen zwei Komponenten erstellen.

> *Parameter:* `component1`, `component2` (required, string), `element1`, `element2` (optional, string). *Verifizierbarkeit:* Constraint existiert in Assembly.

**FR-07.5** `catia_offset_constraint` SOLL eine Offset-Constraint erstellen.

> *Parameter:* `component1`, `component2` (required, string), `offset` (required, number, mm). *Verifizierbarkeit:* Abstand-Constraint existiert.

**FR-07.6** `catia_angle_constraint` SOLL eine Winkel-Constraint erstellen.

> *Parameter:* `component1`, `component2` (required, string), `angle` (required, number, degrees). *Verifizierbarkeit:* Winkel-Constraint existiert.

**FR-07.7** `catia_move_component` SOLL eine Komponente translatieren und/oder rotieren.

> *Parameter:* `component_name` (required, string), `tx,ty,tz` (optional, number, mm), `rx,ry,rz` (optional, number, degrees). *Verifizierbarkeit:* Komponente hat neue Position/Orientierung.

**FR-07.8** `catia_list_components` SOLL alle Assembly-Komponenten auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen und Positionen aller Komponenten.

**FR-07.9** `catia_list_constraints` SOLL alle Assembly-Constraints auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Typen und Ziel-Elemente aller Constraints.


**FR-07.10** `catia_contact_constraint` SOLL einen Contact-Constraint zwischen zwei Komponenten erstellen.

> *Parameter:* `component1`, `component2` (required, string), `element1`, `element2` (optional). *Verifizierbarkeit:* Contact-Constraint existiert.

**FR-07.11** `catia_distance_constraint` SOLL einen Distance-Constraint erstellen.

> *Parameter:* `component1`, `component2`, `distance` (required, > 0), `element1`, `element2` (optional). *Verifizierbarkeit:* Distance-Constraint mit korrekter Distanz existiert.

**FR-07.12** `catia_tangent_constraint` SOLL einen Tangency-Constraint erstellen.

> *Parameter:* `component1`, `component2` (required), `element1`, `element2` (optional). *Verifizierbarkeit:* Tangency-Constraint existiert.

**FR-07.13** `catia_remove_component` SOLL eine Komponente aus der Assembly entfernen.

> *Parameter:* `component_name` (required). *Verifizierbarkeit:* Komponente ist nicht mehr im Product-Tree.

**FR-07.14** `catia_remove_constraint` SOLL einen Constraint entfernen.

> *Parameter:* `constraint_name` (required). *Verifizierbarkeit:* Constraint ist entfernt.

**FR-07.15** `catia_ground_constraint` SOLL eine Komponente in der Assembly grounden (Bewegung verhindern, ohne vollständig zu fixieren).

> *Parameter:* `component_name` (required). *Verifizierbarkeit:* Ground-Constraint existiert.

---

#### FR-08: Measurement (10 Tools)

**FR-08.1** `catia_measure_distance` SOLL den Mindestabstand zwischen zwei Geometrie-Elementen messen.

> *Parameter:* `element1`, `element2` (required, string). *Verifizierbarkeit:* Response enthält Distanz in mm.

**FR-08.2** `catia_get_inertia` SOLL Trägheitseigenschaften zurückgeben (Volumen, Oberfläche, Schwerpunkt, Masse, Trägheitstensor).

> *Parameter:* `density` (optional, number, kg/m³). *Verifizierbarkeit:* Response enthält Volumen (mm³), Oberfläche (mm²), COG (mm³), optional Masse.

**FR-08.3** `catia_get_bounding_box` SOLL die Bounding Box des aktiven Parts zurückgeben.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält min/max-Koordinaten in mm.

**FR-08.4** `catia_get_parameters` SOLL alle user-defined und computed Parameter auflisten.

> *Parameter:* `filter` (optional, string). *Verifizierbarkeit:* Response enthält Parameter-Namen und -Werte.

**FR-08.5** `catia_set_parameter` SOLL den Wert eines Parameters setzen.

> *Parameter:* `name` (required, string), `value` (required, number). *Verifizierbarkeit:* Parameter hat neuen Wert.

**FR-08.6** `catia_update_part` SOLL das aktive Part aktualisieren/neu berechnen.

> *Parameter:* keine. *Verifizierbarkeit:* Alle Features sind recalc'd und up-to-date.

**FR-08.7** `catia_measure_angle` SOLL den Winkel zwischen zwei planaren Flächen messen.

> *Parameter:* `element1`, `element2` (required). *Verifizierbarkeit:* Response enthält Winkel in Grad.

**FR-08.8** `catia_measure_area` SOLL die Oberfläche einer Fläche/Surface messen.

> *Parameter:* `element` (required). *Verifizierbarkeit:* Response enthält Fläche in mm²/cm².

**FR-08.9** `catia_measure_length` SOLL die Länge einer Kante/Kurve messen.

> *Parameter:* `element` (required). *Verifizierbarkeit:* Response enthält Länge in mm.

**FR-08.10** `catia_measure_interference` SOLL Interferenz/Überlappung zwischen zwei Bodies prüfen.

> *Parameter:* `element1`, `element2` (required). *Verifizierbarkeit:* Response enthält Interferenz-Tiefe oder Freiraum.

---

#### FR-09: Export & View (4 Tools)

**FR-09.1** `catia_export` SOLL das aktive Dokument in ein externes Format exportieren (STEP, IGES, STL, 3DXML, VRML, PDF, CGR).

> *Parameter:* `file_path` (required, string), `format` (optional, enum: step/iges/stl/3dxml/vrml). *Verifizierbarkeit:* Output-Datei existiert im korrekten Format.

**FR-09.2** `catia_screenshot` SOLL einen Screenshot der aktuellen 3D-Ansicht speichern (PNG, JPG, BMP).

> *Parameter:* `file_path` (required, string), `width` (optional, int, default 1920), `height` (optional, int, default 1080). *Verifizierbarkeit:* Bilddatei existiert mit korrekten Abmessungen.

**FR-09.3** `catia_set_view` SOLL die 3D-Ansicht-Orientierung setzen (front, back, top, bottom, left, right, isometric).

> *Parameter:* `view` (required, enum). *Verifizierbarkeit:* View-Orientierung ist geändert.

**FR-09.4** `catia_fit_all` SOLL die Ansicht auf alle Geometrie zoomen (Zoom to Fit).

> *Parameter:* keine. *Verifizierbarkeit:* Alle Geometrie ist sichtbar.

---

#### FR-10: GSD — Wireframe & Surface (32 Tools)

**FR-10.1** `catia_create_geometrical_set` SOLL einen neuen Geometrical Set (HybridBody) erstellen.

> *Parameter:* `name` (required). *Verifizierbarkeit:* Neuer HybridBody existiert.

**FR-10.2** `catia_create_point_coord` SOLL einen Punkt durch 3D-Koordinaten erstellen.

> *Parameter:* `x`, `y`, `z` (required), `set_name` (optional). *Verifizierbarkeit:* Point-Element existiert.

**FR-10.3** `catia_create_line_2points` SOLL eine Linie durch zwei Punkte erstellen.

> *Parameter:* `point1_name`, `point2_name` (required), `set_name` (optional). *Verifizierbarkeit:* Line-Element existiert.

**FR-10.4** `catia_create_line_point_direction` SOLL eine Linie durch Punkt und Richtung erstellen.

> *Parameter:* `point_name`, `direction` (required), `set_name` (optional). *Verifizierbarkeit:* Line-Element existiert.

**FR-10.5** `catia_create_circle_center_radius` SOLL einen Kreis durch Mittelpunkt und Radius erstellen.

> *Parameter:* `center_name`, `radius` (required), `support_plane`, `set_name` (optional). *Verifizierbarkeit:* Circle-Element existiert.

**FR-10.6** `catia_create_plane_offset` SOLL eine versetzte Ebene erstellen.

> *Parameter:* `reference_plane`, `offset` (required), `set_name` (optional). *Verifizierbarkeit:* Plane-Element existiert.

**FR-10.7** `catia_create_cylinder` SOLL einen Zylinder erstellen.

> *Parameter:* `center_name`, `axis`, `radius`, `height` (required), `set_name` (optional). *Verifizierbarkeit:* Cylinder-Element existiert.

**FR-10.8** `catia_list_geometrical_sets` SOLL alle Geometrical Sets auflisten.

> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen und Shape-Counts.

**FR-10.9** `catia_create_plane_3points` SOLL eine Ebene durch drei Punkte erstellen.

> *Parameter:* `point1_name`, `point2_name`, `point3_name` (required). *Verifizierbarkeit:* Plane-Element existiert.

**FR-10.10** `catia_create_fill` SOLL eine Fill-Oberfläche aus Konturen erstellen.

> *Parameter:* `contour_names` (required). *Verifizierbarkeit:* Fill-Element existiert.

**FR-10.11** `catia_create_sweep` SOLL eine Swept-Surface erstellen.

> *Parameter:* `spine_name`, `section_name` (required). *Verifizierbarkeit:* Sweep-Element existiert.

**FR-10.12** `catia_create_rotational_surface` SOLL eine Rotationsfläche erstellen.

> *Parameter:* `axis_name`, `profile_name` (required), `angle` (optional). *Verifizierbarkeit:* Rotational-Surface existiert.

**FR-10.13** `catia_create_offset_surface` SOLL eine Offset-Oberfläche erstellen.

> *Parameter:* `surface_name`, `distance` (required). *Verifizierbarkeit:* Offset-Surface existiert.

**FR-10.14** `catia_create_join` SOLL mehrere Oberflächen verbinden.

> *Parameter:* `surface_names` (required). *Verifizierbarkeit:* Join-Element existiert.

**FR-10.15** `catia_create_thicken` SOLL eine Oberfläche verdicken.

> *Parameter:* `surface_name`, `thickness` (required). *Verifizierbarkeit:* Thicken-Element existiert.

**FR-10.16** `catia_create_surface_from_contours` SOLL eine Multi-Section-Surface erstellen.

> *Parameter:* `contour_names` (required). *Verifizierbarkeit:* Multi-section-surface existiert.

**FR-10.17** `catia_create_sphere` SOLL eine Kugeloberfläche erstellen.

> *Parameter:* `radius` (required), `cx`, `cy`, `cz`, `angle_start`, `angle_end`, `lat_start`, `lat_end`, `set_name` (optional). *Verifizierbarkeit:* Sphere-Element existiert.

**FR-10.18** `catia_create_cone` SOLL eine Kegelfläche erstellen.

> *Parameter:* `base_radius`, `height` (required), `cx`, `cy`, `cz`, `top_radius`, `angle`, `set_name` (optional). *Verifizierbarkeit:* Cone-Element existiert.

**FR-10.19** `catia_create_torus` SOLL eine Torusfläche erstellen.

> *Parameter:* `major_radius`, `minor_radius` (required), `cx`, `cy`, `cz`, `angle_start`, `angle_end`, `set_name` (optional). *Verifizierbarkeit:* Torus-Element existiert.

**FR-10.20** `catia_create_ruled` SOLL eine Regelfläche zwischen zwei Kurven erstellen.

> *Parameter:* `profile1`, `profile2` (required). *Verifizierbarkeit:* Ruled-surface existiert.

**FR-10.21** `catia_create_blend` SOLL einen Blend (Fillett) auf einer Kante/Kurve erstellen.

> *Parameter:* `edge_or_curve_name`, `radius` (required). *Verifizierbarkeit:* Blend-Element existiert.

**FR-10.22** `catia_split_surface` SOLL eine Oberfläche mit einem Schneidelement aufteilen.

> *Parameter:* `surface_name`, `tool_name` (required). *Verifizierbarkeit:* Split-Element existiert.

**FR-10.23** `catia_extend_surface` SOLL eine Oberfläche über ihre aktuelle Begrenzung hinaus erweitern.

> *Parameter:* `surface_name` (required), `distance` (optional, default 10). *Verifizierbarkeit:* Extend-Element existiert.

**FR-10.24** `catia_trim_surface` SOLL eine Oberfläche mit einem Schneidelement beschneiden.

> *Parameter:* `surface_name`, `tool_name` (required), `keep_part` (optional). *Verifizierbarkeit:* Trim-Element existiert.

**FR-10.25** `catia_create_point_on_curve` SOLL einen Punkt auf einer Kurve an einem gegebenen Parameter erstellen.

> *Parameter:* `curve_name` (required), `parameter` (required, 0-1), `set_name` (optional). *Verifizierbarkeit:* Point-Element existiert auf der Kurve.

**FR-10.26** `catia_create_point_intersection` SOLL einen Punkt am Schnittpunkt zweier Elemente erstellen.

> *Parameter:* `element1_name`, `element2_name` (required), `set_name` (optional). *Verifizierbarkeit:* Point-Element existiert am Schnittpunkt.

**FR-10.27** `catia_create_line_tangent` SOLL eine Tangente an einer Kurve an einem Punkt erstellen.

> *Parameter:* `curve_name`, `point_name` (required), `set_name` (optional). *Verifizierbarkeit:* Line-Element existiert als Tangente.

**FR-10.28** `catia_create_line_normal_to_surface` SOLL eine Normale auf einer Oberfläche an einem Punkt erstellen.

> *Parameter:* `surface_name`, `point_name` (required), `set_name` (optional). *Verifizierbarkeit:* Line-Element existiert als Normalenvektor.

**FR-10.29** `catia_create_plane_parallel` SOLL eine parallele Ebene durch einen Punkt erstellen.

> *Parameter:* `reference_plane`, `point_name` (required), `set_name` (optional). *Verifizierbarkeit:* Plane-Element existiert parallel zur Referenzebene.

**FR-10.30** `catia_create_plane_tangent_to_surface` SOLL eine Tangentialebene auf einer Oberfläche an einem Punkt erstellen.

> *Parameter:* `surface_name`, `point_name` (required), `set_name` (optional). *Verifizierbarkeit:* Plane-Element existiert als Tangentialebene.

**FR-10.31** `catia_create_mirror` SOLL ein Wireframe-Element an einer Ebene spiegeln.

> *Parameter:* `element_name`, `mirror_plane_name` (required), `set_name` (optional). *Verifizierbarkeit:* Gespiegeltes Element existiert.

**FR-10.32** `catia_create_tabulated_cylinder` SOLL eine Tabulated-Cylinder-Oberfläche durch Extrusion eines Profils erstellen.

> *Parameter:* `profile_name`, `direction`, `length` (required), `set_name` (optional). *Verifizierbarkeit:* Tabulated-Cylinder-Element existiert.

---

### 3.2 Nicht-Funktionale Anforderungen

#### NR-01: Funktional

**NR-01.1** Das System SOLL auf dem Zielsystem (Windows) ausführbar sein.

> *Kriterium:* `python -m catia_mcp` startet ohne ImportError (bei installierten Dependencies).

**NR-01.2** Die Mindest-Python-Version SOLL Python 3.10 sein.

> *Kriterium:* `requires-python = ">=3.10"` in `pyproject.toml`.

**NR-01.3** Der Server SOLL als pip-installierbares Package verfügbar sein.

> *Kriterium:* `pip install -e .` installiert Package mit entry point `catia-mcp`.

#### NR-02: Zuverlässigkeit

**NR-02.1** Das System SOLL nach einem COM-Verbindungsabbruch eine transparente Neuverbindung durch `ensure_connected()` ermöglichen.

> *Kriterium:* Nach Abbruch ist `reconnect()` erfolgreich innerhalb von 30 Sekunden.

**NR-02.2** Das System SOLL doppelte COM-Zugriffe durch einen asyncio-Lock serialisieren.

> *Kriterium:* Parallele Tool-Calls führen nie zu COM-Thread-Violations.

**NR-02.3** Das System SOLL nach einem CATIA-Neustart wieder verbinden können.

> *Kriterium:* Nach CATIA-Neustart + `catia_connect` ist Server funktionsfähig.

#### NR-03: Fehlerbehandlung

**NR-03.1** Das System SOLL bei ungültigen Eingaben eine klare Fehlermeldung zurückgeben, die den betroffenen Parameter und den erwarteten Wertebereich nennt.

> *Kriterium:* Fehlermeldung enthält Parametername, tatsächlichen Wert, und erwartetes Format.

**NR-03.2** Das System SOLL CATIA COM-Fehler in nutzerfreundliche Messages übersetzen.

> *Kriterium:* Fehlermeldung enthält Operation-Name, CATIA-Fehlermeldung, und gängige Lösungsansätze.

**NR-03.3** Das System SOLL nicht abstürzen, wenn CATIA nicht installiert oder nicht lizenziert ist.

> *Kriterium:* `catia_connect` wirft `RuntimeError` mit klarer Message statt uncaught Exception.

#### NR-04: Eingabe-Validierung

**NR-04.1** Numerische Eingaben SOLLEN auf Typ und Wertebereich validiert werden, bevor sie an CATIA gesendet werden.

> *Kriterium:* Negative Abmessungen bei `pad`/`pocket` resultieren in ValidationError, nicht in COM-Fehler.

**NR-04.2** Dateipfade SOLLEN auf Gültigkeit (Nicht-Leer, absoluter Pfad) validiert werden.

> *Kriterium:* Relativer Pfad bei `catia_open_document` resultiert in ValidationError.

**NR-04.3** Ebenen-Namen SOLLEN auf `xy`, `yz`, `zx` beschränkt sein.

> *Kriterium:* Ungültiger Ebenen-Name resultiert in ValidationError.

#### NR-05: Performance

**NR-05.1** Die Latenz zwischen `tools/call`-Eingang und -Antwort SOLL unter 5 Sekunden liegen (bei einfacher Geometrie).

> *Kriterium:* `catia_list_documents` antwortet innerhalb von 5 Sekunden.

**NR-05.2** Der SSE-Server SOLL mindestens 10 gleichzeitige Client-Verbindungen unterstützen.

> *Kriterium:* 10 parallele SSE-Verbindungen ohne Timeout oder Absturz.

#### NR-06: Logging

**NR-06.1** Das System SOLL alle Tool-Calls und -Ergebnisse (first 200 chars) loggen.

> *Kriterium:* Log-Datei enthält Timestamp, Tool-Name, Arguments, und Ergebnis.

**NR-06.2** Das System SOLL Log-Dateien außerhalb des Projektverzeichnisses speichern (im Temp-Verzeichnis).

> *Kriterium:* Logs nach `%TEMP%\catia-mcp\catia_mcp.log` (Windows) geschrieben.

**NR-06.3** Das System SOLL Logs sowohl in Datei als auch auf stderr ausgeben.

> *Kriterium:* stderr-Output enthält gleiche Log-Messages wie Datei.

#### NR-07: Sicherheit

**NR-07.1** Das System SOLL keine API-Keys, Tokens oder Passwörter im Code speichern.

> *Kriterium:* Keine Zeichenketten mit `ghp_`, `github_pat_`, `xoxp-`, `sk-` im Repository.

**NR-07.2** Das System SOLL keine persönlichen Daten (E-Mails, Namen) in gepushten Dateien enthalten.

> *Kriterium:* Kein `*.com`-E-Mail-Pattern in Quelldateien.

**NR-07.3** Das System SOLL den SSE-Transport-Modus mit konfigurierbarem Bind-Host betreiben (Standard: `0.0.0.0` für LAN).

> *Kriterium:* `--host 127.0.0.1` für localhost-only Zugriff verfügbar.

#### NR-08: Wartbarkeit

**NR-08.1** Das System SOLL eine umfassende Test-Suite mit mockten COM-Abhängigkeiten bereitstellen.

> *Kriterium:* 256 pytest-Tests, alle bestanden, lauffähig unter Linux ohne CATIA.

**NR-08.2** Das System SOLL eine `.gitignore`-Datei enthalten, die Python-Artefakte, venvs, Logs und `.env`-Dateien ausschließt.

> *Kriterium:* Git-Index enthält keine `*.pyc`, `__pycache__/`, `.venv/`, `*.log`, `.env`.

**NR-08.3** Das System SOLL eine MIT-Lizenz enthalten.

> *Kriterium:* `LICENSE`-Datei im Repo-Root existiert.

#### NR-09: Portabilität

**NR-09.1** Das System SOLL unter Windows 10/11 (64-bit) lauffähig sein.

> *Kriterium:* COM-Automation funktioniert auf Windows mit CATIA V5.

**NR-09.2** Die Test-Suite SOLL unter Linux ausführbar sein.

> *Kriterium:* `pytest tests/` unter Linux ohne CATIA oder COM erfolgreich.

---

## 4. Traceability Matrix

| Req-ID | Kategorie | Implementiert in | Testet in |
|--------|-----------|-----------------|-----------|
| FR-01.1–01.4 | MCP-Grundfunktion | `server.py` | `test_server.py` |
| FR-02.1–02.5 | Transport | `server.py` | `test_sse.py` |
| FR-03.1–03.7 | CATIA-Verbindung | `connection.py` | `test_connection.py` |
| FR-04.1–04.7 | Dokument | `tools/document.py` | `test_document_tools.py` |
| FR-05.1–05.14 | Sketcher | `tools/sketcher.py` | `test_sketcher_tools.py` |
| FR-06.1–06.19 | Part Design | `tools/part_design.py` | `test_part_design_tools.py` |
| FR-07.1–07.14 | Assembly | `tools/assembly.py` | `test_assembly_tools.py` |
| FR-08.1–08.10 | Measurement | `tools/measurement.py` | `test_measurement_tools.py` |
| FR-09.1–09.4 | Export & View | `tools/export.py` | `test_export_tools.py` |
| FR-10.1–10.24 | GSD | `tools/gsd.py` | `test_gsd_tools.py` |
| NR-01.1–01.3 | Funktional | `pyproject.toml`, `__main__.py` | `test_entry_points.py` |
| NR-02.1–02.3 | Zuverlässigkeit | `connection.py` | `test_connection.py` |
| NR-03.1–03.3 | Fehlerbehandlung | `utils.py` | `test_utils.py` |
| NR-04.1–04.3 | Validierung | `utils.py` | `test_utils.py` |
| NR-05.1–05.2 | Performance | `server.py` | — (manual) |
| NR-06.1–06.3 | Logging | `server.py` | — (verifikation per Log-File) |
| NR-07.1–07.3 | Sicherheit | `.gitignore`, `.gitattributes`, `server.py` | — (manual audit) |
| NR-08.1–08.3 | Wartbarkeit | `tests/`, `.gitignore`, `LICENSE` | — |
| NR-09.1–09.2 | Portabilität | `pyproject.toml` | `pytest tests/` |

---

## 5. Änderungsprotokoll

| Version | Datum | Autor | Änderung |
|---------|-------|-------|---------|
| 1.0 | 2026-05-30 | Hermes Agent | Erstfassung |
| 1.8 | 2026-06-03 | Agent | pycatia-Dual-Backend, Tool-Count 55→95, GSD-FR-10, Part Design 15→19, Measurement 6→10, Assembly 9→14, Tests 154→256 |
