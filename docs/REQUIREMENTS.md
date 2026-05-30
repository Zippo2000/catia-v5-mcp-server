     1|# CATIA V5 MCP Server — ASPICE Requirements Specification
     2|
     3|| Feld | Wert |
     4||------|------|
     5|| **Dokument-ID** | REQ-001 |
     6|| **Version** | 1.4 |
     7|| **Status** | Entwurf |
     8|| **Letzte Änderung** | 2026-05-30 |
     9|| **Projekt** | catia-v5-mcp-server |
    10|| **Software-Version** | 0.1.0 |
    11|
    12|---
    13|
    14|## 1. Einleitung
    15|
    16|### 1.1 Zweck
    17|
    18|Diese Spezifikation definiert die funktionalen und nicht-funktionalen Anforderungen an den
    19|**CATIA V5 MCP Server** (nachfolgend „System"). Das System stellt einen MCP-Server (Model Context
    20|Protocol) bereit, der es LLM-Clients ermöglicht, CATIA V5 CAD-Operationen über eine standardisierte
    21|Tool-Interface zu steuern.
    22|
    23|### 1.2 Geltungsbereich
    24|
    25|Das System ist ein Python-Package (`catia-v5-mcp-server`), das als MCP-Server agiert und über
    26|zwei Transport-Modi (stdio, SSE) mit LLM-Clients kommuniziert. Die CAD-Operationen werden
    27|über Windows COM Automation (win32com) an CATIA V5 delegiert.
    28|
    29|### 1.3 Begriffe und Abkürzungen
    30|
    31|| Begriff | Definition |
    32||---------|-----------|
    33|| **MCP** | Model Context Protocol — Standard-Protokoll für LLM-Tool-Integration |
    34|| **LLM-Client** | Client-Anwendung, die einen MCP-Server konsumiert (z.B. Claude Desktop, LM Studio) |
    35|| **COM** | Component Object Model — Windows-Automation-Standard |
    36|| **Part** | Einzelnes 3D-Körperteil in CATIA V5 |
    37|| **Product** | Assembly (Baugruppe) in CATIA V5 |
    38|| **Sketch** | 2D-Geometrie, die als Profil für 3D-Features dient |
    39|| **Feature** | 3D-Operation (Pad, Pocket, Fillet, etc.) |
    40|| **Constraint** | Geometrische/physikalische Bedingung im Sketch oder Assembly |
| **GSD** | Generative Shape Design — CATIA V5 Workbench für Surface/Wireframe |
| **HybridBody** | Geometrical Set / Konstruktionselemente-Container in CATIA Part |
| **HybridShapeFactory** | COM-Factory zur Erzeugung von Wireframe- und Surface-Geometrie |
    41|| **SSE** | Server-Sent Events — HTTP-basierter单向-Messaging-Transport |
    42|| **stdio** | Standard Input/Output — lokale Pipe-basierte Kommunikation |
    43|| **SMART** | Specific, Measurable, Achievable, Relevant, Time-bound |
    44|
    45|### 1.4 Normen und Referenzen
    46|
    47|| Ref | Norm | Relevanz |
    48||-----|------|----------|
    49|| R1 | ASPICE SYS.2 | Software Requirements Engineering |
    50|| R2 | ISO/IEC/IEEE 29148 | Requirements & Specification |
    51|| R3 | MCP Specification (v2024.11) | Model Context Protocol Standard |
    52|| R4 | Dassault Systèmes CATIA V5 Automation API | COM-Interface-Spezifikation |
    53|| R5 | Python PEP 8 | Python Code Style |
    54|
    55|---
    56|
    57|## 2. Gesamte Anforderungen
    58|
    59|### 2.1 Allgemeine Beschreibung
    60|
    61|#### 2.1.1 Produkt-Perspektive
    62|
    63|```
    64|┌──────────────┐  MCP-Protokoll  ┌──────────────┐  COM-Automation  ┌──────────┐
    65|│  LLM-Client  │  ──────────────►│  MCP-Server  │  ───────────────►│ CATIA V5 │
    66|│              │  (stdio / SSE)  │ (Python)     │  (win32com)      │ (Windows)│
    67|└──────────────┘                  └──────────────┘                   └──────────┘
    68|```
    69|
    70|Das System ist ein **Middleware-Server** zwischen LLM-Clients und CATIA V5. Es übersetzt
    71|MCP-Tool-Calls in COM-Aufrufe und formatiert COM-Ergebnisse als MCP-Tool-Responses.
    72|
    73|#### 2.1.2 Produkt-Funktionen (Übersicht)
    74|
    75|| Kategorie | Tool-Anzahl | Beschreibung |
    76||-----------|------------|-------------|
    77|| Dokument-Verwaltung | 10 | Erstellen, Öffnen, Speichern, Schließen von Part/Product/Drawing |
    78|| Sketcher | 11 | 2D-Geometrie-Erstellung und -Bearbeitung |
    79|| Part Design | 19 | 3D-Feature-Erstellung (Pad, Pocket, Fillet, etc.) |
    80|| Assembly | 14 | Baugruppen-Verwaltung und Constraints (inkl. Contact, Distance, Tangent, Remove) |
    81|| GSD (Wireframe & Surface) | 16 | Point, Line, Circle, Plane, Cylinder, Fill, Sweep, Join, Thicken |
    82|| Export & View | 4 | Export (STEP/IGES/STL), Screenshots, View |
    83|| **Total** | **87** | — |
    84|
    85|#### 2.1.3 Nutzerklassen und Charakteristiken
    86|
    87|| Nutzerklasse | Beschreibung | Anforderungen |
    88||-------------|-------------|--------------|
    89|| CAD-Ingenieur | Nutzt CATIA V5 professionell | Vollständige Feature-Abdeckung, Korrektheit |
    90|| Entwickler | Integriert MCP-Server | Stabile API, klare Dokumentation |
    91|| LLM-User | Chat-basierte CAD-Interaktion | Fehler-resilient, klare Error-Messages |
    92|
    93|#### 2.1.4 Betriebsumgebung
    94|
    95|| Komponente | Anforderung |
    96||-----------|-----------|
    97|| **Betriebssystem** | Windows 10/11 (64-bit) — COM-Automation erfordert Windows |
    98|| **Python** | Version ≥ 3.10 |
    99|| **CATIA V5** | Version R2016+ mit gültiger Lizenz |
   100|| **MCP-Client** | Beliebiger MCP-kompatibler Client (Claude Desktop, LM Studio, vLLM.rs, etc.) |
   101|| **Netzwerk** | Für SSE-Modus: TCP-Port 8765 (default) muss erreichbar sein |
   102|
   103|#### 2.1.5 Einschränkungen
   104|
   105|| Einschränkung | Begründung |
   106||--------------|-----------|
   107|| COM-Automation nur unter Windows | Plattform-Beschränkung von win32com |
   108|| Single-Threaded COM-Zugriff | CATIA COM-API ist nicht thread-safe |
   109|| Keine CATIA-Zeichnungsautomatisierung | Aktuell kein Drawing-Tool-Set implementiert |
   110|| Keine Drawing-Automatisierung | Aktuell kein Drawing-Tool-Set implementiert |
   111|
   112|#### 2.1.6 Verwendungsannahmen
   113|
   114|1. CATIA V5 ist installiert und lizenziert auf dem Windows-System.
   115|2. Der Nutzer hat administrative Rechte zum Starten von COM-Automation.
   116|3. Der LLM-Client unterstützt das MCP-Protokoll.
   117|4. Für SSE-Modus: TCP-Port ist von Client aus erreichbar (Firewall).
   118|
   119|---
   120|
   121|## 3. Detaillierte Anforderungen
   122|
   123|### 3.1 Funktionale Anforderungen
   124|
   125|#### FR-01: MCP-Server-Grundfunktionalität
   126|
   127|**FR-01.1** Das System SOLL sich als MCP-Server mit dem Namen `catia-v5-mcp` registrieren.
   128|
   129|> *Verifizierbarkeit:* Der Server antwortet auf `initialize`-Request mit `serverInfo.name == "catia-v5-mcp"`.
   130|
   131|**FR-01.2** Das System SOLL mindestens 87 Tools implementieren und über `tools/list` verfügbar machen.
   132|
   133|> *Verifizierbarkeit:* `tools/list`-Response enthält ≥87 Einträge mit korrekten `name`, `description`, `inputSchema`.
   134|
   135|**FR-01.3** Das System SOLL auf `tools/call`-Requests das angegebene Tool ausführen und ein strukturiertes Text-Ergebnis zurückgeben.
   136|
   137|> *Verifizierbarkeit:* Jeder `tools/call`-Request mit gültigen Parametern resultiert in einer `text`-Content-Response.
   138|
   139|**FR-01.4** Das System SOLL unbekannte Tool-Namen mit einer klaren Fehlermeldung ablehnen.
   140|
   141|> *Verifizierbarkeit:* `tools/call` mit nicht-existentem Tool-Name resultiert in Error-Text, der den Tool-Namen enthält.
   142|
   143|---
   144|
   145|#### FR-02: Transport-Modi
   146|
   147|**FR-02.1** Das System SOLL einen stdio-Transport-Modus unterstützen, bei dem MCP-JSON-RPC über stdin/stdout erfolgt.
   148|
   149|> *Verifizierbarkeit:* Start mit `python -m catia_mcp` (default) ermöglicht Kommunikation via stdin/stdout.
   150|
   151|**FR-02.2** Das System SOLL einen SSE-Transport-Modus unterstützen, der zwei HTTP-Endpoints bereitstellt:
   152|- `GET /sse` — SSE-Stream (Server → Client)
   153|- `POST /messages/` — Client-Nachrichten (Client → Server)
   154|
   155|> *Verifizierbarkeit:* Start mit `python -m catia_mcp --sse` öffnet HTTP-Endpoints auf konfigurierbarem Host/Port.
   156|
   157|**FR-02.3** Das System SOLL den SSE-Bind-Host per `--host` CLI-Argument konfigurierbar machen (Standard: `0.0.0.0`).
   158|
   159|> *Verifizierbarkeit:* `--host 127.0.0.1` bindet SSE-Server auf localhost.
   160|
   161|**FR-02.4** Das System SOLL den SSE-Port per `--port` CLI-Argument konfigurierbar machen (Standard: `8765`).
   162|
   163|> *Verifizierbarkeit:* `--port 9000` bindet SSE-Server auf Port 9000.
   164|
   165|**FR-02.5** Die Transport-Modus-Argumente `--stdio` und `--sse` SIND mutually exclusive.
   166|
   167|> *Verifizierbarkeit:* Kombination `--stdio --sse` resultiert in Argument-Parser-Fehler.
   168|
   169|---
   170|
   171|#### FR-03: CATIA-Verbindung
   172|
   173|**FR-03.1** Das System SOLL bei `catia_connect` zuerst versuchen, eine existierende CATIA-Instanz zu erreichen.
   174|
   175|> *Verifizierbarkeit:* Bei laufender CATIA-Instanz verwendet `GetActiveObject` statt `CreateObject`.
   176|
   177|**FR-03.2** Das System SOLL bei fehlender CATIA-Instanz eine neue Instanz starten.
   178|
   179|> *Verifizierbarkeit:* Bei nicht-laufender CATIA führt `catia_connect` zum Start von `CATIA.Application`.
   180|
   181|**FR-03.3** Das System SOLL nach COM-Verbindungsabbruch eine erneute Verbindung mit `catia_reconnect` ermöglichen.
   182|
   183|> *Verifizierbarkeit:* Nach `disconnect`+neuem `connect` ist `is_connected` == True.
   184|
   185|**FR-03.4** Das System SOLL bei `catia_disconnect` die COM-Referenz freigeben, aber CATIA nicht beenden.
   186|
   187|> *Verifizierbarkeit:* Nach `catia_disconnect` ist `is_connected` == False, CATIA-Prozess läuft weiter.
   188|
   189|**FR-03.5** Das System SOLL bei `catia_close` CATIA vollständig beenden (einschließlich aller offenen Dokumente).
   190|
   191|> *Verifizierbarkeit:* Nach `catia_close` ist der CATIA-Prozess nicht mehr lauffähig.
   192|
   193|**FR-03.6** Das System SOLL doppelte Verbindungsversuche durch einen Lock-Mechanismus verhindern.
   194|
   195|> *Verifizierbarkeit:* Während eines laufenden `connect()`-Aufrufs resultiert ein neuer `connect()` in `RuntimeError`.
   196|
   197|**FR-03.7** Das System SOLL automatisch bei jedem Tool-Call (außer `catia_connect`, `catia_disconnect`, `catia_close`) eine aktive CATIA-Verbindung sicherstellen.
   198|
   199|> *Verifizierbarkeit:* Aufruf eines Tools ohne vorherigen `catia_connect` löst impliziten Connect aus.
   200|
   201|---
   202|
   203|#### FR-04: Dokument-Verwaltung (10 Tools)
   204|
   205|**FR-04.1** `catia_new_part` SOLL ein neues Part-Dokument erstellen und optional benennen.
   206|
   207|> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Nach Aufruf ist ein neues Part-Dokument aktiv.
   208|
   209|**FR-04.2** `catia_new_product` SOLL ein neues Product-Dokument (Assembly) erstellen und optional benennen.
   210|
   211|> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Nach Aufruf ist ein neues Product-Dokument aktiv.
   212|
   213|**FR-04.3** `catia_open_document` SOLL ein bestehendes CATIA-Dokument (.CATPart, .CATProduct, .CATDrawing) öffnen.
   214|
   215|> *Parameter:* `file_path` (required, string). *Verifizierbarkeit:* Dokument wird als ActiveDocument geladen.
   216|
   217|**FR-04.4** `catia_save_document` SOLL das aktive Dokument speichern (optional als neuen Pfad).
   218|
   219|> *Parameter:* `file_path` (optional, string). *Verifizierbarkeit:* Datei existiert nach Aufruf.
   220|
   221|**FR-04.5** `catia_close_document` SOLL das aktive Dokument schließen (optional mit Speichern).
   222|
   223|> *Parameter:* `save` (optional, bool). *Verifizierbarkeit:* Dokument ist nicht mehr in der Document-Liste.
   224|
   225|**FR-04.6** `catia_list_documents` SOLL alle offenen Dokumente mit Typ und Pfad auflisten.
   226|
   227|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen, Typen und Pfade aller offenen Dokumente.
   228|
   229|**FR-04.7** `catia_get_active_document_info` SOLL detaillierte Informationen über das aktive Dokument zurückgeben.
   230|
   231|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Name, Typ, Pfad, Part Bodies, Features, etc.
   232|
   233|---
   234|
   235|#### FR-05: Sketcher (11 Tools)
   236|
   237|**FR-05.1** `catia_create_sketch` SOLL einen 2D-Sketch auf einer Referenzebene (xy, yz, zx) erstellen.
   238|
   239|> *Parameter:* `plane` (optional, enum: xy/yz/zx, default: xy). *Verifizierbarkeit:* Sketch ist aktiv und editierbar.
   240|
   241|**FR-05.2** `catia_close_sketch` SOLL den aktiven Sketch schließen und zur Part Design-Umgebung zurückkehren.
   242|
   243|> *Parameter:* keine. *Verifizierbarkeit:* Kein aktiver Sketch, 3D-Features können erstellt werden.
   244|
   245|**FR-05.3** `catia_sketch_line` SOLL eine Linie von (x1,y1) nach (x2,y2) zeichnen.
   246|
   247|> *Parameter:* `x1,y1,x2,y2` (required, number, mm). *Verifizierbarkeit:* Line-Element existiert im Sketch.
   248|
   249|**FR-05.4** `catia_sketch_rectangle` SOLL ein Rechteck durch zwei Eckpunkte zeichnen.
   250|
   251|> *Parameter:* `x1,y1,x2,y2` (required, number, mm). *Verifizierbarkeit:* 4 Line-Elemente existieren.
   252|
   253|**FR-05.5** `catia_sketch_centered_rectangle` SOLL ein zentriertes Rechteck erstellen.
   254|
   255|> *Parameter:* `cx,cy` (optional, number), `width,height` (required, number, mm). *Verifizierbarkeit:* Rechteck ist am Zentrum zentriert.
   256|
   257|**FR-05.6** `catia_sketch_circle` SOLL einen Kreis mit gegebenem Radius zeichnen.
   258|
   259|> *Parameter:* `cx,cy` (optional, number), `radius` (required, number > 0, mm). *Verifizierbarkeit:* Circle-Element existiert.
   260|
   261|**FR-05.7** `catia_sketch_arc` SOLL einen Kreisbogen erstellen.
   262|
   263|> *Parameter:* `cx,cy,radius,start_angle,end_angle` (required, number). *Verifizierbarkeit:* Arc-Element existiert mit korrekten Winkeln.
   264|
   265|**FR-05.8** `catia_sketch_spline` SOLL eine Spline durch Kontrollpunkte erstellen.
   266|
   267|> *Parameter:* `points` (required, list of [x,y]), `closed` (optional, bool). *Verifizierbarkeit:* Spline-Element durch alle Punkte.
   268|
   269|**FR-05.9** `catia_sketch_point` SOLL einen Punkt im Sketch erstellen.
   270|
   271|> *Parameter:* `x,y` (required, number, mm). *Verifizierbarkeit:* Point-Element existiert.
   272|
   273|**FR-05.10** `catia_sketch_constraint` SOLL eine geometrische oder dimensionale Constraint hinzufügen.
   274|
   275|> *Parameter:* `type` (required, enum), `value`, `geometry_index_1`, `geometry_index_2` (optional). *Verifizierbarkeit:* Constraint ist in Sketch aktiv.
   276|
   277|**FR-05.11** `catia_sketch_get_geometry` SOLL alle Geometrie-Elemente im aktiven Sketch auflisten.
   278|
   279|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Indizes, Typen und Eigenschaften aller Elemente.
   280|
   281|---
   282|
   283|#### FR-06: Part Design (19 Tools)
   284|
   285|**FR-06.1** `catia_pad` SOLL einen Pad (Extrusion) aus dem letzten oder benannten Sketch erstellen.
   286|
   287|> *Parameter:* `height` (required, number > 0, mm), `direction` (optional, enum: normal/reverse/both), `symmetric` (optional, bool), `sketch_name` (optional, string). *Verifizierbarkeit:* Solid-Feature existiert mit korrekter Höhe.
   288|
   289|**FR-06.2** `catia_pocket` SOLL eine Aussparung (Cut Extrusion) aus dem Sketch erstellen.
   290|
   291|> *Parameter:* `depth` (required, number > 0, mm), `direction` (optional, enum), `sketch_name` (optional, string). *Verifizierbarkeit:* Material wird entfernt.
   292|
   293|**FR-06.3** `catia_shaft` SOLL eine Drehung (Revolution) um eine Achse erstellen.
   294|
   295|> *Parameter:* `angle` (optional, number, default 360, degrees), `sketch_name` (optional, string). *Verifizierbarkeit:* Rotations-Feature existiert.
   296|
   297|**FR-06.4** `catia_groove` SOLL eine Dreh-Aussparung erstellen.
   298|
   299|> *Parameter:* `angle` (optional, number), `sketch_name` (optional, string). *Verifizierbarkeit:* Rotations-Feature mit Materialentfernung.
   300|
   301|**FR-06.5** `catia_fillet` SOLL Rundungen auf Kanten erstellen.
   302|
   303|> *Parameter:* `radius` (required, number > 0, mm), `edge_name` (optional, string). *Verifizierbarkeit:* Fillet-Feature auf Kante(n) existiert.
   304|
   305|**FR-06.6** `catia_chamfer` SOLL Fasen auf Kanten erstellen.
   306|
   307|> *Parameter:* `length` (required, number > 0, mm), `angle` (optional, number, default 45, degrees), `edge_name` (optional, string). *Verifizierbarkeit:* Chamfer-Feature existiert.
   308|
   309|**FR-06.7** `catia_hole` SOLL ein Loch erstellen (einfach, Senkkopf, Zentrierbohrung).
   310|
   311|> *Parameter:* `diameter` (required, number > 0), `depth` (required, number > 0), `type` (optional, enum), `threaded` (optional, bool), `sketch_name` (optional, string). *Verifizierbarkeit:* Hole-Feature existiert.
   312|
   313|**FR-06.8** `catia_rect_pattern` SOLL ein Feature in einem rechteckigen Muster duplizieren.
   314|
   315|> *Parameter:* `dir1_count`, `dir1_spacing` (required), `dir2_count`, `dir2_spacing` (optional), `feature_name` (required, string). *Verifizierbarkeit:* Pattern-Feature existiert mit korrekter Instanzanzahl.
   316|
   317|**FR-06.9** `catia_circ_pattern` SOLL ein Feature um eine Achse dreh-symmetrisch duplizieren.
   318|
   319|> *Parameter:* `count` (required, int > 0), `angular_spacing` (optional, number), `feature_name` (required, string). *Verifizierbarkeit:* Pattern-Feature mit korrekter Anzahl.
   320|
   321|**FR-06.10** `catia_mirror` SOLL ein Feature oder Body an einer Ebene spiegeln.
   322|
   323|> *Parameter:* `plane` (required, enum: xy/yz/zx), `feature_name` (required, string). *Verifizierbarkeit:* Gespiegeltes Feature existiert.
   324|
   325|**FR-06.11** `catia_shell` SOLL ein Part aushöhlen.
   326|
   327|> *Parameter:* `thickness` (required, number > 0, mm), `faces_to_remove` (optional, list of strings). *Verifizierbarkeit:* Hollow-Feature existiert mit gegebener Wandstärke.
   328|
   329|**FR-06.12** `catia_draft` SOLL Ziehkanten anwenden.
   330|
   331|> *Parameter:* `angle` (required, number), `face_name` (optional, string), `pulling_direction` (optional, string). *Verifizierbarkeit:* Draft-Feature existiert.
   332|
   333|**FR-06.13** `catia_thickness` SOLL Fläche verschieben.
   334|
   335|> *Parameter:* `offset` (required, number, mm), `face_name` (optional, string). *Verifizierbarkeit:* Thickness-Feature existiert.
   336|
   337|**FR-06.14** `catia_list_features` SOLL alle Features im aktiven Part Body auflisten.
   338|
   339|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen und Typen aller Features.
   340|
   341|**FR-06.15** `catia_list_edges` SOLL alle Kanten des aktiven Solid auflisten.
   342|
   343|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Kanten-Namen für Fillet/Chamfer-Selektion.
   344|
   345|---
   346|
   347|#### FR-07: Assembly (9 Tools)
   348|
   349|**FR-07.1** `catia_add_component` SOLL eine existierende .CATPart oder .CATProduct als Komponente hinzufügen.
   350|
   351|> *Parameter:* `file_path` (required, string). *Verifizierbarkeit:* Komponente ist in Product-Tree.
   352|
   353|**FR-07.2** `catia_add_new_part` SOLL ein neues Part direkt in der Assembly erstellen.
   354|
   355|> *Parameter:* `name` (optional, string). *Verifizierbarkeit:* Neues Part-Komponente existiert.
   356|
   357|**FR-07.3** `catia_fix_constraint` SOLL eine Komponente fixieren (alle Freiheitsgrade entfernen).
   358|
   359|> *Parameter:* `component_name` (required, string). *Verifizierbarkeit:* Fix-Constraint existiert.
   360|
   361|**FR-07.4** `catia_coincidence_constraint` SOLL eine Coincidence-Constraint zwischen zwei Komponenten erstellen.
   362|
   363|> *Parameter:* `component1`, `component2` (required, string), `element1`, `element2` (optional, string). *Verifizierbarkeit:* Constraint existiert in Assembly.
   364|
   365|**FR-07.5** `catia_offset_constraint` SOLL eine Offset-Constraint erstellen.
   366|
   367|> *Parameter:* `component1`, `component2` (required, string), `offset` (required, number, mm). *Verifizierbarkeit:* Abstand-Constraint existiert.
   368|
   369|**FR-07.6** `catia_angle_constraint` SOLL eine Winkel-Constraint erstellen.
   370|
   371|> *Parameter:* `component1`, `component2` (required, string), `angle` (required, number, degrees). *Verifizierbarkeit:* Winkel-Constraint existiert.
   372|
   373|**FR-07.7** `catia_move_component` SOLL eine Komponente translatieren und/oder rotieren.
   374|
   375|> *Parameter:* `component_name` (required, string), `tx,ty,tz` (optional, number, mm), `rx,ry,rz` (optional, number, degrees). *Verifizierbarkeit:* Komponente hat neue Position/Orientierung.
   376|
   377|**FR-07.8** `catia_list_components` SOLL alle Assembly-Komponenten auflisten.
   378|
   379|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Namen und Positionen aller Komponenten.
   380|
   381|**FR-07.9** `catia_list_constraints` SOLL alle Assembly-Constraints auflisten.
   382|
   383|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält Typen und Ziel-Elemente aller Constraints.
   384|
   385|---
   386|
   387|#### FR-08: Measurement (6 Tools)
   388|
   389|**FR-08.1** `catia_measure_distance` SOLL den Mindestabstand zwischen zwei Geometrie-Elementen messen.
   390|
   391|> *Parameter:* `element1`, `element2` (required, string). *Verifizierbarkeit:* Response enthält Distanz in mm.
   392|
   393|**FR-08.2** `catia_get_inertia` SOLL Trägheitseigenschaften zurückgeben (Volumen, Oberfläche, Schwerpunkt, Masse, Trägheitstensor).
   394|
   395|> *Parameter:* `density` (optional, number, kg/m³). *Verifizierbarkeit:* Response enthält Volumen (mm³), Oberfläche (mm²), COG (mm³), optional Masse.
   396|
   397|**FR-08.3** `catia_get_bounding_box` SOLL die Bounding Box des aktiven Parts zurückgeben.
   398|
   399|> *Parameter:* keine. *Verifizierbarkeit:* Response enthält min/max-Koordinaten in mm.
   400|
   401|**FR-08.4** `catia_get_parameters` SOLL alle user-defined und computed Parameter auflisten.
   402|
   403|> *Parameter:* `filter` (optional, string). *Verifizierbarkeit:* Response enthält Parameter-Namen und -Werte.
   404|
   405|**FR-08.5** `catia_set_parameter` SOLL den Wert eines Parameters setzen.
   406|
   407|> *Parameter:* `name` (required, string), `value` (required, number). *Verifizierbarkeit:* Parameter hat neuen Wert.
   408|
   409|**FR-08.6** `catia_update_part` SOLL das aktive Part aktualisieren/neu berechnen.
   410|
   411|> *Parameter:* keine. *Verifizierbarkeit:* Alle Features sind recalc'd und up-to-date.
   412|
   413|---
   414|
   415|#### FR-09: Export & View (4 Tools)
   416|
   417|**FR-09.1** `catia_export` SOLL das aktive Dokument in ein externes Format exportieren (STEP, IGES, STL, 3DXML, VRML, PDF, CGR).
   418|
   419|> *Parameter:* `file_path` (required, string), `format` (optional, enum: step/iges/stl/3dxml/vrml). *Verifizierbarkeit:* Output-Datei existiert im korrekten Format.
   420|
   421|**FR-09.2** `catia_screenshot` SOLL einen Screenshot der aktuellen 3D-Ansicht speichern (PNG, JPG, BMP).
   422|
   423|> *Parameter:* `file_path` (required, string), `width` (optional, int, default 1920), `height` (optional, int, default 1080). *Verifizierbarkeit:* Bilddatei existiert mit korrekten Abmessungen.
   424|
   425|**FR-09.3** `catia_set_view` SOLL die 3D-Ansicht-Orientierung setzen (front, back, top, bottom, left, right, isometric).
   426|
   427|> *Parameter:* `view` (required, enum). *Verifizierbarkeit:* View-Orientierung ist geändert.
   428|
   429|**FR-09.4** `catia_fit_all` SOLL die Ansicht auf alle Geometrie zoomen (Zoom to Fit).
   430|
   431|> *Parameter:* keine. *Verifizierbarkeit:* Alle Geometrie ist sichtbar.
   432|
   433|---
   434|
   435|### 3.2 Nicht-Funktionale Anforderungen
   436|
   437|#### NR-01: Funktional
   438|
   439|**NR-01.1** Das System SOLL auf dem Zielsystem (Windows) ausführbar sein.
   440|
   441|> *Kriterium:* `python -m catia_mcp` startet ohne ImportError (bei installierten Dependencies).
   442|
   443|**NR-01.2** Die Mindest-Python-Version SOLL Python 3.10 sein.
   444|
   445|> *Kriterium:* `requires-python = ">=3.10"` in `pyproject.toml`.
   446|
   447|**NR-01.3** Der Server SOLL als pip-installierbares Package verfügbar sein.
   448|
   449|> *Kriterium:* `pip install -e .` installiert Package mit entry point `catia-mcp`.
   450|
   451|#### NR-02: Zuverlässigkeit
   452|
   453|**NR-02.1** Das System SOLL nach einem COM-Verbindungsabbruch eine Neuverbindung durch `catia_reconnect` ermöglichen.
   454|
   455|> *Kriterium:* Nach Abbruch ist `reconnect()` erfolgreich innerhalb von 30 Sekunden.
   456|
   457|**NR-02.2** Das System SOLL doppelte COM-Zugriffe durch einen asyncio-Lock serialisieren.
   458|
   459|> *Kriterium:* Parallele Tool-Calls führen nie zu COM-Thread-Violations.
   460|
   461|**NR-02.3** Das System SOLL nach einem CATIA-Neustart wieder verbinden können.
   462|
   463|> *Kriterium:* Nach CATIA-Neustart + `catia_connect` ist Server funktionsfähig.
   464|
   465|#### NR-03: Fehlerbehandlung
   466|
   467|**NR-03.1** Das System SOLL bei ungültigen Eingaben eine klare Fehlermeldung zurückgeben, die den betroffenen Parameter und den erwarteten Wertebereich nennt.
   468|
   469|> *Kriterium:* Fehlermeldung enthält Parametername, tatsächlichen Wert, und erwartetes Format.
   470|
   471|**NR-03.2** Das System SOLL CATIA COM-Fehler in nutzerfreundliche Messages übersetzen.
   472|
   473|> *Kriterium:* Fehlermeldung enthält Operation-Name, CATIA-Fehlermeldung, und gängige Lösungsansätze.
   474|
   475|**NR-03.3** Das System SOLL nicht abstürzen, wenn CATIA nicht installiert oder nicht lizenziert ist.
   476|
   477|> *Kriterium:* `catia_connect` wirft `RuntimeError` mit klarer Message statt uncaught Exception.
   478|
   479|#### NR-04: Eingabe-Validierung
   480|
   481|**NR-04.1** Numerische Eingaben SOLLEN auf Typ und Wertebereich validiert werden, bevor sie an CATIA gesendet werden.
   482|
   483|> *Kriterium:* Negative Abmessungen bei `pad`/`pocket` resultieren in ValidationError, nicht in COM-Fehler.
   484|
   485|**NR-04.2** Dateipfade SOLLEN auf Gültigkeit (Nicht-Leer, absoluter Pfad) validiert werden.
   486|
   487|> *Kriterium:* Relativer Pfad bei `catia_open_document` resultiert in ValidationError.
   488|
   489|**NR-04.3** Ebenen-Namen SOLLEN auf `xy`, `yz`, `zx` beschränkt sein.
   490|
   491|> *Kriterium:* Ungültiger Ebenen-Name resultiert in ValidationError.
   492|
   493|#### NR-05: Performance
   494|
   495|**NR-05.1** Die Latenz zwischen `tools/call`-Eingang und -Antwort SOLL unter 5 Sekunden liegen (bei einfacher Geometrie).
   496|
   497|> *Kriterium:* `catia_list_documents` antwortet innerhalb von 5 Sekunden.
   498|
   499|**NR-05.2** Der SSE-Server SOLL mindestens 10 gleichzeitige Client-Verbindungen unterstützen.
   500|
   501|> *Kriterium:* 10 parallele SSE-Verbindungen ohne Timeout oder Absturz.
   502|
   503|#### NR-06: Logging
   504|
   505|**NR-06.1** Das System SOLL alle Tool-Calls und -Ergebnisse (first 200 chars) loggen.
   506|
   507|> *Kriterium:* Log-Datei enthält Timestamp, Tool-Name, Arguments, und Ergebnis.
   508|
   509|**NR-06.2** Das System SOLL Log-Dateien außerhalb des Projektverzeichnisses speichern (im Temp-Verzeichnis).
   510|
   511|> *Kriterium:* Logs nach `%TEMP%\catia-mcp\catia_mcp.log` (Windows) geschrieben.
   512|
   513|**NR-06.3** Das System SOLL Logs sowohl in Datei als auch auf stderr ausgeben.
   514|
   515|> *Kriterium:* stderr-Output enthält gleiche Log-Messages wie Datei.
   516|
   517|#### NR-07: Sicherheit
   518|
   519|**NR-07.1** Das System SOLL keine API-Keys, Tokens oder Passwörter im Code speichern.
   520|
   521|> *Kriterium:* Keine Zeichenketten mit `ghp_`, `github_pat_`, `xoxp-`, `sk-` im Repository.
   522|
   523|**NR-07.2** Das System SOLL keine persönlichen Daten (E-Mails, Namen) in gepushten Dateien enthalten.
   524|
   525|> *Kriterium:* Kein `*.com`-E-Mail-Pattern in Quelldateien.
   526|
   527|**NR-07.3** Das System SOLL den SSE-Transport-Modus mit konfigurierbarem Bind-Host betreiben (Standard: `0.0.0.0` für LAN).
   528|
   529|> *Kriterium:* `--host 127.0.0.1` für localhost-only Zugriff verfügbar.
   530|
   531|#### NR-08: Wartbarkeit
   532|
   533|**NR-08.1** Das System SOLL eine umfassende Test-Suite mit mockten COM-Abhängigkeiten bereitstellen.
   534|
   535|> *Kriterium:* 205 pytest-Tests, alle bestanden, lauffähig unter Linux ohne CATIA.
   536|
   537|**NR-08.2** Das System SOLL eine `.gitignore`-Datei enthalten, die Python-Artefakte, venvs, Logs und `.env`-Dateien ausschließt.
   538|
   539|> *Kriterium:* Git-Index enthält keine `*.pyc`, `__pycache__/`, `.venv/`, `*.log`, `.env`.
   540|
   541|**NR-08.3** Das System SOLL eine MIT-Lizenz enthalten.
   542|
   543|> *Kriterium:* `LICENSE`-Datei im Repo-Root existiert.
   544|
   545|#### NR-09: Portabilität
   546|
   547|**NR-09.1** Das System SOLL unter Windows 10/11 (64-bit) lauffähig sein.
   548|
   549|> *Kriterium:* COM-Automation funktioniert auf Windows mit CATIA V5.
   550|
   551|**NR-09.2** Die Test-Suite SOLL unter Linux ausführbar sein.
   552|
   553|> *Kriterium:* `pytest tests/` unter Linux ohne CATIA oder COM erfolgreich.
   554|
   555|---
   556|
   557|## 4. Traceability Matrix
   558|
   559|| Req-ID | Kategorie | Implementiert in | Testet in |
   560||--------|-----------|-----------------|-----------|
   561|| FR-01.1–01.4 | MCP-Grundfunktion | `server.py` | `test_server.py` |
   562|| FR-02.1–02.5 | Transport | `server.py` | `test_sse.py` |
   563|| FR-03.1–03.7 | CATIA-Verbindung | `connection.py` | `test_connection.py` |
   564|| FR-04.1–04.7 | Dokument | `tools/document.py` | `test_document_tools.py` |
   565|| FR-05.1–05.14 | Sketcher | `tools/sketcher.py` | `test_sketcher_tools.py` |
   566|| FR-06.1–06.19 | Part Design | `tools/part_design.py` | `test_part_design_tools.py` |
   567|| FR-07.1–07.14 | Assembly | `tools/assembly.py` | `test_assembly_tools.py` |
| FR-10.1–10.16 | GSD (Wireframe & Surface) | `tools/gsd.py` | `test_gsd_tools.py` |
   568|| FR-08.1–08.10 | Measurement | `tools/measurement.py` | `test_measurement_tools.py` |
   569|| FR-11.1–11.4 | Export & View | `tools/export.py` | `test_export_tools.py` |
   570|| NR-01.1–01.3 | Funktional | `pyproject.toml`, `__main__.py` | `test_entry_points.py` |
   571|| NR-02.1–02.3 | Zuverlässigkeit | `connection.py` | `test_connection.py` |
   572|| NR-03.1–03.3 | Fehlerbehandlung | `utils.py` | `test_utils.py` |
   573|| NR-04.1–04.3 | Validierung | `utils.py` | `test_utils.py` |
   574|| NR-05.1–05.2 | Performance | `server.py` | — (manual) |
   575|| NR-06.1–06.3 | Logging | `server.py` | — (verifikation per Log-File) |
   576|| NR-07.1–07.3 | Sicherheit | `.gitignore`, `.gitattributes`, `server.py` | — (manual audit) |
   577|| NR-08.1–08.3 | Wartbarkeit | `tests/`, `.gitignore`, `LICENSE` | — |
   578|| NR-09.1–09.2 | Portabilität | `pyproject.toml` | `pytest tests/` |
   579|
   580|---
   581|
   582|## 5. Änderungsprotokoll
   583|
   584|| Version | Datum | Autor | Änderung |
   585||---------|-------|-------|---------|
   586|| 1.0 | 2026-05-30 | Hermes Agent | Erstfassung (55 Tools, 6 Module, 154 Tests) |
| 1.1 | 2026-05-30 | Hermes Agent | Phase 6 (GSD): +16 Tools, 7 Module, 75 Tools gesamt, 205 Tests. FR-10 hinzugefügt, FR-06.16-19, NR-08.1 aktualisiert, Traceability Matrix erweitert |
   587|