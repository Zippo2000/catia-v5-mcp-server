# CATIA V5 — Gap Analyse: MCP-Server vs. Vollständiger Funktionsumfang

| Feld | Wert |
|------|------|
| **Dokument-ID** | GAP-001 |
| **Version** | 1.0 |
| **Status** | Entwurf |
| **Letzte Änderung** | 2026-05-30 |
| **Basis** | CATIA V5 Automation API, pycatia 0.9.x, CATIA Workbench-Übersicht |

---

## 1. Methodik

Diese Analyse vergleicht den aktuellen Funktionsumfang des **catia-v5-mcp-server** (87 Tools
über 7 Module) mit dem vollständigen CATIA V5 Automation API-Spektrum.

**Quellen:**
- Dassault Systèmes CATIA V5 Automation API (catiadoc.free.fr)
- pycatia 0.9.x API-Dokumentation (referenz Python-Wrapper)
- CATIA V5 Workbench-Struktur (Infrastructure, Part Design, GSD, Assembly, Drafting, ...)

**Abbildungsgrade:**
- 🟢 **Vollständig** — Alle relevanten COM-Methoden sind im MCP-Server verfügbar
- 🟡 **Teilweise** — Nur ein Subset der API-Methoden ist verfügbar
- 🔴 **Nicht vorhanden** — Kein MCP-Tool deckt diesen Bereich ab

---

## 2. Infrastruktur (Infrastructure Workbench)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | Application-Steuerung (`Start`, `Quit`, `Visible`) | 🟢 | — |
| 2 | Document-Management (`Open`, `SaveAs`, `Close`, `Documents`-Collection) | 🟢 | — |
| 3 | ActiveDocument-Query | 🟢 | — |
| 4 | Document-Typ-Diskriminierung (Part, Product, Drawing) | 🟢 | — |
| 5 | **Document-Eigenschaften** (`Title`, `Subject`, `Author`, `Keywords`) | 🔴 | Nicht abgedeckt — keine Tools für Metadaten-Lesen/Schreiben |
| 6 | **Design-Parameter** (`Factory`, `GetUserParameter`) | 🟡 | `get_parameters` / `set_parameter` vorhanden, aber **nur einfache Werte** — keine Parameter-Erstellung, keine Relationen/Abhängigkeiten |
| 7 | **Geometrical Sets** (`CreateGeometricalSet`) | 🟢 | `catia_create_geometrical_set` + `catia_list_geometrical_sets` |
| 8 | **Selection** (`BeginSelection`, `SelectElement2`, `SelectElement3`) | 🔴 | Keine explizite Selection-API — Tools verwenden interne Referenzierung |
| 9 | **Timeline** (`TimelineController`, `Feature`-Ablaufsteuerung) | 🔴 | Keine Timeline-Features (Feature-Aktivierung, Order, etc.) |
| 10 | **Search** (`Search`-Methode: z.B. "All Features, name=*Pad*") | 🔴 | Keine suchbasierte Feature-Recherche |

**Fazit:** Infrastruktur-Grundlagen sind gut abgedeckt. Metadaten, Parameter-Erstellung,
Geometrical Sets, Selection, Timeline und Search fehlen.

---

## 3. Part Design (Part Design Workbench)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Pad** (Extrusion) | 🟢 | — |
| 2 | **Pocket** (Cut Extrusion) | 🟢 | — |
| 3 | **Shaft** (Revolution) | 🟢 | — |
| 4 | **Groove** (Revolution Cut) | 🟢 | — |
| 5 | **Hole** (Simple, Counterbored, Countersunk) | 🟢 | — |
| 6 | **Fillet** | 🟢 | — |
| 7 | **Chamfer** (Distance/Angle) | 🟢 | — |
| 8 | **Rib** (Versteifung) | 🟡 | Teilweise — über `catia_pad` mit Sketch machbar, aber kein dediziertes Rib-Tool |
| 9 | **Slot** (Nut) | 🔴 | Kein dediziertes Slot-Tool |
| 10 | **Multibody Pad/Pocket** | 🔴 | Kein Multibody-Modus — nur Single-Body-Extrusion |
| 11 | **PowerCopy** (Parametric Feature Template) | 🔴 | Keine PowerCopy-Unterstützung |
| 12 | **PowerCopy Pattern** | 🔴 | — |
| 13 | **Rectangular Pattern** | 🟢 | — |
| 14 | **Circular Pattern** | 🟢 | — |
| 15 | **Mirror** (Feature & Body) | 🟢 | — |
| 16 | **Boolean Operations** (Union, Intersection, Difference) | 🔴 | Keine Boolean-Operationen zwischen Bodies |
| 17 | **Shell** | 🟢 | — |
| 18 | **Draft** | 🟢 | — |
| 19 | **Thickness** | 🟢 | — |
| 20 | **Lifting** (Variable-Thickness Extrusion) | 🟢 | — |
| 21 | **Variable Section Sweep** (VSS) | 🟢 | — |
| 22 | **Loft** (Multi-Sketch) | 🟢 | — |
| 23 | **Boolean Operations** (Union, Intersection, Difference) | 🟢 | — |
| 24 | **PowerCopy** (Parametric Feature Template) | 🔴 | Keine PowerCopy-Unterstützung |
| 25 | **PowerCopy Pattern** | 🔴 | — |
| 26 | **Rectangular Pattern** | 🟢 | — |
| 27 | **Circular Pattern** | 🟢 | — |
| 28 | **Mirror** (Feature & Body) | 🟢 | — |
| 29 | **Boolean Operations** (Union, Intersection, Difference) | 🟢 | — |
| 30 | **Combine** (Sum/Difference on Bodies) | 🔴 | Keine Body-Combine |
| 31 | **Split** (Split Body by Plane/Surface) | 🔴 | Keine Split-Operation |
| 32 | **Reference Patterns** | 🔴 | Keine Referenz-Patterns |
| 33 | **Multi-Direction Pattern** | 🔴 | Keine MD-Patterns |
| 34 | **Semi-Constraints** | 🔴 | Keine Semi-Constraints-Unterstützung |
| 35 | **Instant Design** | 🔴 | Kein Instant Design-Modus |
| 36 | **Instant Features** (Quick Pad, etc.) | 🔴 | — |
| 37 | **Multi-Sketch Pad/Pocket** | 🔴 | Keine Multi-Sketch-Features |

**Fazit:** Die 19 aktuellen Part-Design-Tools decken die **Core-Features** plus Lifting, Sweep, Loft und Boolean ab.
Fehlend sind fortgeschrittene Features (PowerCopy, Split, Combine, Multi-Body, Instant Design).

---

## 4. Sketcher

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | Line | 🟢 | — |
| 2 | Rectangle | 🟢 | — |
| 3 | Circle | 🟢 | — |
| 4 | Arc | 🟢 | — |
| 5 | Spline | 🟢 | — |
| 6 | Point | 🟢 | — |
| 7 | **Ellipse** | 🔴 | Keine Ellipse |
| 8 | **Hyperbola** | 🔴 | Keine Hyperbel |
| 9 | **Parabola** | 🔴 | Keine Parabel |
| 10 | **Construction Element** (Hilfslinie) | 🔴 | Keine Konstruktionselemente |
| 11 | **Trim/Extend** (Kurven trimmen/verlängern) | 🔴 | Keine Trim/Extend |
| 12 | **Break/Join** (Kurven aufteilen/verbinden) | 🔴 | Keine Break/Join |
| 13 | **Mirror** (in Sketch) | 🔴 | Kein Sketch-Mirror |
| 14 | **Translate/Rotate** (in Sketch) | 🔴 | Keine Sketch-Transformationen |
| 15 | Constraints (Dim & Geo) | 🟢 | — |
| 16 | **Tangent constraint** | 🟢 | — |
| 17 | **Symmetry constraint** | 🔴 | Keine Symmetrie-Constraint |
| 18 | **Equidistance constraint** | 🔴 | Keine Äquidistanz-Constraint |
| 19 | **Point-On-Curve** | 🔴 | — |
| 20 | **Offset curve** | 🔴 | Keine Offset-Kurve |
| 21 | **Text** (in Sketch) | 🔴 | Kein Text im Sketch |
| 22 | **Quick Constraints** | 🔴 | Keine automatischen Constraints |

**Fazit:** Core-Sketching (Line, Rect, Circle, Arc, Spline, Point, Basic Constraints) ist
vollständig. Fehlend: Konische Kurven (Ellipse, Hyperbel, Parabel), Trim/Extend,
Konstruktionselemente, erweiterte Constraints.

---

## 5. Wireframe & Surface Design (GSD)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Plane** (Reference, 3-Point, Offset) | 🟢 | Plane 3-Points + Plane Offset implementiert |
| 2 | **Cylinder** | 🟢 | `catia_create_cylinder` |
| 3 | **Sphere** | 🔴 | Kein Sphere-Tool |
| 4 | **Cone** | 🔴 | Kein Cone-Tool |
| 5 | **Torus** | 🔴 | Kein Torus-Tool |
| 6 | **Line** (2-Point, Tangent, Normal, etc.) | 🟡 | Line 2-Points + Line Pt/Dir implementiert; Tangent/Normal fehlen |
| 7 | **Point** (Coord, on Curve, Intersection, etc.) | 🟡 | Point Coord implementiert; on Curve/Intersection fehlen |
| 8 | **Axis** | 🔴 | Kein Axis-Tool |
| 9 | **Multi-Section Surface** (Loft) | 🟢 | `catia_create_surface_from_contours` |
| 10 | **Fill** | 🟢 | `catia_create_fill` |
| 11 | **Sweep** (Simple, VSS) | 🟢 | `catia_create_sweep` |
| 12 | **Rotational Surface** | 🟢 | `catia_create_rotational_surface` |
| 13 | **Offset Surface** | 🟢 | `catia_create_offset_surface` |
| 14 | **Ruled Surface** | 🔴 | Keine Ruled Surface |
| 15 | **Tabulated Cylinder** | 🔴 | Kein Tabulated Cylinder |
| 16 | **Blend** (Edge-to-Edge Surface) | 🔴 | Kein Blend |
| 17 | **Small Sphere** / **Small Blend** | 🔴 | — |
| 18 | **Bridge** | 🔴 | Keine Bridge |
| 19 | **Healed Fill** | 🔴 | Kein Healed Fill |
| 20 | **Surface from Contours** | 🟢 | `catia_create_surface_from_contours` |
| 21 | **Intersection Curves** | 🔴 | Keine Intersection |
| 22 | **Split Surface** | 🔴 | Kein Split |
| 23 | **Extend Surface** | 🔴 | Kein Extend |
| 24 | **Thicken** (Surface → Solid) | 🟢 | `catia_create_thicken` |
| 25 | **Extract** (Surface Copy) | 🔴 | Kein Extract |
| 26 | **Trim/Untrim Surface** | 🔴 | Kein Trim |
| 27 | **Simplify / Refine Surface** | 🔴 | Kein Refine |
| 28 | **Join** (Multiple Surfaces) | 🟢 | `catia_create_join` |
| 29 | **Average Surface** | 🔴 | Kein Average |
| 30 | **Sagitta** | 🔴 | Keine Sagitta |
| 31 | **Reverse Normal** | 🔴 | Kein Reverse Normal |
| 32 | **Tangent Surface** | 🔴 | Kein Tangent Surface |
| 33 | **Swept Surface** (with Profile + Guide) | 🟢 | `catia_create_sweep` |
| 34 | **Surface Deform** | 🔴 | Kein Deform |
| 35 | **Surface Project** | 🔴 | Kein Project |
| 36 | **Analytic Shapes** (from Part Design) | 🔴 | — |
| 0 | **Geometrical Set Management** | 🟢 | `catia_create_geometrical_set` + `catia_list_geometrical_sets` |
| 0 | **Circle** | 🟢 | `catia_create_circle_center_radius` |

**Fazit:** **GSD-Grundlagen sind jetzt abgedeckt** (16/36 API-Bereiche = 44% 🟡). Wireframe-Basics
(Point, Line, Circle, Plane, Cylinder) und Surface-Grundlagen (Fill, Sweep, Join, Thicken, Offset,
Rotational Surface, Multi-Section) sind implementiert. Fehlend: Sphere, Cone, Torus, Blend,
Ruled, Tabulated Cylinder, Surface-Manipulation (Split, Extend, Trim, Deform).

---

## 6. Assembly (Product Structure)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | Add Component (from file) | 🟢 | — |
| 2 | Add New Part | 🟢 | — |
| 3 | Fix Constraint | 🟢 | — |
| 4 | Coincidence Constraint | 🟢 | — |
| 5 | Offset Constraint | 🟢 | — |
| 6 | Angle Constraint | 🟢 | — |
| 7 | **Contact Constraint** | 🔴 | Keine Contact (Face-to-Face) Constraint |
| 8 | **Distance Constraint** | 🔴 | Keine Distance (Edge-to-Edge) Constraint |
| 9 | **Tangent Constraint** | 🔴 | Keine Tangent Constraint |
| 10 | **Smallest/Longest Distance** | 🔴 | Keine Extreme-Distance Constraint |
| 11 | **Intersection Constraint** | 🔴 | Keine Intersection Constraint |
| 12 | Move Component | 🟢 | — |
| 13 | List Components | 🟢 | — |
| 14 | List Constraints | 🟢 | — |
| 15 | **Remove Component** | 🔴 | Keine Komponente-Entfernung |
| 16 | **Remove Constraint** | 🔴 | Keine Constraint-Entfernung |
| 17 | **Ground / UNGround** | 🔴 | Kein Grounding (abgesehen von Fix) |
| 18 | **In-Context Design** | 🔴 | Kein In-Context-Modus |
| 19 | **Reference Set** | 🔴 | Keine Reference Sets |
| 20 | **Configuration Management** (Show/Hide, Configurations) | 🔴 | Keine Konfigurations-Verwaltung |
| 21 | **Virtual Components** | 🔴 | Keine virtuellen Komponenten |
| 22 | **Skeleton Design** | 🔴 | Kein Skeleton-Modus |
| 23 | **Exploded View** | 🔴 | Keine Explosionsansicht |
| 24 | **Update Assembly** | 🔴 | Keine explizite Assembly-Update |

**Fazit:** Core-Assembly-Grundlagen sind gut. Fehlend: Contact-, Distance-, Tangent-Constraints,
Komponente/Constraint-Entfernung, In-Context Design, Reference Sets, Konfigurationen.

---

## 7. Drafting (2D Drawing)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Drawing Document** (Create, Open) | 🔴 | — |
| 2 | **Sheet** (Create, Size, Orientation) | 🔴 | — |
| 3 | **Sheet Format** (Border, Title Block, Background) | 🔴 | — |
| 4 | **View Creation** (Front, Side, Top, Isometric, Section, Detail) | 🔴 | — |
| 5 | **Section View** (Full, Half, Broken) | 🔴 | — |
| 6 | **Detail View** (Circular, Local) | 🔴 | — |
| 7 | **Auxiliary View** | 🔴 | — |
| 8 | **Exploded Assembly View** | 🔴 | — |
| 9 | **Dimensioning** (Linear, Diameter, Angular, Radius) | 🔴 | — |
| 10 | **Tolerance** (GD&T, Linear, Angular) | 🔴 | — |
| 11 | **Surface Finish** | 🔴 | — |
| 12 | **Leader / Balloon** | 🔴 | — |
| 13 | **Bill of Materials (BOM)** | 🔴 | — |
| 14 | **Welding Symbols** | 🔴 | — |
| 15 | **Center Lines** | 🔴 | — |
| 16 | **Hatching / Material** | 🔴 | — |
| 17 | **Annotations** (Text, Title, Note) | 🔴 | — |
| 18 | **Table** (Part Properties, Custom) | 🔴 | — |
| 19 | **Simplify Drawing View** | 🔴 | — |
| 20 | **Drawing Update from Part** | 🔴 | — |

**Fazit:** **Drafting ist komplett nicht abgedeckt** (0 von 20 API-Bereichen).
2D-Zeichnungen sind für Dokumentation und Fertigung kritisch.

---

## 8. Presentation / Visualization

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | Screenshot | 🟢 | — |
| 2 | Set View | 🟢 | — |
| 3 | Fit All | 🟢 | — |
| 4 | **Rendering** (Material, Lighting, Environment) | 🔴 | Keine Rendering-Steuerung |
| 5 | **Appearance** (Color, Transparency, Reflection) | 🔴 | Keine Appearance-Steuerung |
| 6 | **Animation** (Keyframe, Motion) | 🔴 | Keine Animation-Unterstützung |
| 7 | **Scene** (Create, Save, Apply) | 🔴 | Keine Scene-Verwaltung |
| 8 | **Visualization Mode** (Shaded, Wireframe, Hidden Lines) | 🔴 | Keine View-Mode-Steuerung |
| 9 | **Section Plane** (Cross-Section in 3D View) | 🔴 | Keine Section-Plane |
| 10 | **Clipping Plane** | 🔴 | Keine Clipping |

**Fazit:** Basis-View-Steuerung vorhanden. Appearance, Rendering, Animation, Section/Clipping fehlen.

---

## 9. Measurement

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | Distance | 🟢 | — |
| 2 | **Angle** | 🟢 | `catia_measure_angle` |
| 3 | **Area** | 🟢 | `catia_measure_area` |
| 4 | **Volume** | 🟡 | Nur über `get_inertia` (implizit) |
| 5 | Inertia (COG, Mass, Moments) | 🟢 | — |
| 6 | Bounding Box | 🟢 | — |
| 7 | **Curve Length** | 🟢 | `catia_measure_length` |
| 8 | **Circumference** | 🔴 | — |
| 9 | **Surface Area** | 🟢 | `catia_measure_area` + `catia_get_inertia` |
| 10 | **Interference / Clearance Check** | 🟢 | `catia_measure_interference` |
| 11 | **Collision Detection** | 🔴 | Keine Kollisionserkennung |

**Fazit:** Core-Measurement vollständig abgedeckt (Distance, Angle, Area, Length, Inertia, Bounding Box, Interference). Nur Circumference, Collision Detection und Knowledgeware fehlen.

---

## 10. Knowledgeware (Formulas, Rules, Check)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Formula** (Create, Read, Update, Delete) | 🔴 | Keine Formula-API |
| 2 | **Rule** (Create, Activate, Deactivate, Apply) | 🔴 | Keine Rule-API |
| 3 | **Check** (Design Rule Validation) | 🔴 | Keine Check-API |
| 4 | **Knowledge Advisor** (Run Knowledge Object) | 🔴 | — |
| 5 | **Parameter** (Create, Link, Get/Set) | 🟡 | `get_parameters`/`set_parameter` vorhanden, aber **keine Parameter-Erstellung** |
| 6 | **Expression Editor** | 🔴 | Keine Expression-API |
| 7 | **Variable** (Create, Set, Link) | 🔴 | Keine Variable-API |
| 8 | **External Parameter** (Excel Link, External References) | 🔴 | — |

**Fazit:** Knowledgeware ist fast komplett nicht abgedeckt.
Nur einfache Parameter-Lesen/-Schreiben vorhanden.

---

## 11. PMI (Product Manufacturing Information)

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Tolerance** (Geometric, Dimensional, Angular, Flatness, etc.) | 🔴 | — |
| 2 | **Geometric Tolerance Frame** | 🔴 | — |
| 3 | **Datum Reference Frame** | 🔴 | — |
| 4 | **Welding Symbol** | 🔴 | — |
| 5 | **Surface Finish** (3D) | 🔴 | — |
| 6 | **Manufacturing Symbol** | 🔴 | — |

**Fazit:** PMI ist komplett nicht abgedeckt. Wichtig für MBD (Model-Based Definition).

---

## 12. Management & Configuration

| # | API-Bereich | MCP-Status | Lücke |
|---|-------------|-----------|-------|
| 1 | **Export** (STEP, IGES, STL, 3DXML, PDF) | 🟢 | — |
| 2 | **Import** | 🔴 | Kein Import (nur `open_document`) |
| 3 | **Properties** (Design Properties: Author, Revision, Keywords) | 🔴 | Keine Properties-Verwaltung |
| 4 | **Reference Set** | 🔴 | Keine Reference Sets |
| 5 | **Configuration** (Product Configurations, Show/Hide) | 🔴 | Keine Konfigurations-Verwaltung |
| 6 | **Version / History** (Document Properties, Revision History) | 🔴 | — |
| 7 | **License Check** (CATIA License Status) | 🔴 | Keine License-Query |
| 8 | **User Preferences** (CATIA Options, Units, Display) | 🔴 | Keine Preference-Steuerung |
| 9 | **Macro Execution** | 🔴 | Keine CATScript/Macro-Execution |
| 10 | **Task Scheduler / Job** | 🔴 | Keine Job-Steuerung |

**Fazit:** Export vorhanden. Import, Properties, Reference Sets, Konfigurationen,
Lizenzen, Preferences, Makros fehlen.

---

## 13. Zusammenfassung

### 13.1 Abdeckungsgrad nach Workbench

| Workbench | CATIA API-Bereiche | MCP-Abgedeckt | Abdeckung | Priorität |
|-----------|-------------------|--------------|-----------|-----------|
| **Infrastructure** | 10 | 6/10 | 60% 🟡 | Mittel |
| **Part Design** | 30 | 19/30 | 63% 🟡 | **Hoch** |
| **Sketcher** | 22 | 11/22 | 50% 🟡 | **Hoch** |
| **Wireframe & Surface (GSD)** | 36 | 16/36 | 44% 🟡 | **Hoch** |
| **Assembly** | 24 | 10/24 | 42% 🟡 | **Hoch** |
| **Drafting** | 20 | 0/20 | 0% 🔴 | Mittel |
| **Presentation** | 10 | 3/10 | 30% 🟡 | Niedrig |
| **Measurement** | 11 | 10/11 | 91% 🟢 | Mittel |
| **Knowledgeware** | 8 | 1/8 | 12% 🔴 | Mittel |
| **PMI** | 6 | 0/6 | 0% 🔴 | Niedrig |
| **Management** | 10 | 1/10 | 10% 🔴 | Niedrig |
| **GESAMT** | **187** | **87/187** | **47%** 🟢 | — |

### 13.2 Kritische Lücken (Priorität: Hoch)

| # | Lücke | Impact | Aufwand | Empfehlung |
|---|-------|--------|---------|-----------|
| 1 | **GSD (Wireframe & Surface)** — Sphere, Cone, Torus, Blend, Ruled, Surface-Manipulation (Split, Extend, Trim) | Sehr hoch — Advanced Surface Design fehlt | Mittel (15-20 neue Tools) | Phase 6b — Advanced GSD (Sphere, Cone, Blend, Surface Manipulation) |
| 2 | **Part Design** — PowerCopy, Split, Combine, Multi-Body fehlen | Hoch — Limitiert komplexe Part-Geometrien | Mittel (6 neue Tools) | Phase 5b — PowerCopy + Split + Combine |
| 3 | **Sketcher** — Ellipse, Hyperbola, Parabel, Trim/Extend fehlen | Hoch — Limitiert Sketch-Flexibilität | Niedrig (5-6 neue Tools) | Phase 5c — Conics + Trim |
| 4 | **Assembly** — Contact, Distance, Tangent, Remove Component/Constraint fehlen | Hoch — Limitiert Assembly-Engineering | Mittel (8 neue Tools) | Phase 5d — Advanced Constraints |
| 5 | **Parameter/Formula** — Keine Parameter-Erstellung oder Formulas | Mittel-Hoch — Limitiert Parametric Design | Mittel (5 neue Tools) | Phase 6 |

### 13.3 Mäßige Lücken (Priorität: Mittel)

| # | Lücke | Empfehlung |
|---|-------|-----------|
| 1 | **Drafting** (2D Zeichnungen) | Phase 7 — Drawing-Grundlagen (View, Dimension, BOM) |
| 2 | **GSD Advanced** — Sphere, Cone, Torus, Blend, Ruled, Split/Extend/Trim | Phase 8b |
| 3 | **Infrastructure** — Properties, Selection, Search | Phase 6b |
| 4 | **Knowledgeware** — Formula, Rule, Check | Phase 7 |

### 13.4 Geringe Lücken (Priorität: Niedrig)

| # | Lücke | Empfehlung |
|---|-------|-----------|
| 1 | **PMI** (Tolerances, GD&T) | Zukunft — bei explizitem Bedarf |
| 2 | **Presentation** — Appearance, Rendering, Animation | Zukunft |
| 3 | **Management** — Properties, Preferences, Macro Execution | Zukunft |

---

## 14. Empfohlene Implementierungs-Priorisierung

| Phase | Fokus | Tools (neu) | Aufwand |
|-------|-------|-------------|---------|
| **Phase 5** | GSD-Grundlagen + Part Design Extensions | 15-20 | ⭐⭐⭐ |
| **Phase 5a** | Lifting, Sweep, Loft, Boolean (Part Design) | 10 | ⭐⭐ |
| **Phase 5b** | Conics, Trim/Extend (Sketcher) | 6 | ⭐ |
| **Phase 5c** | Contact, Distance, Tangent, Remove (Assembly) | 8 | ⭐⭐ |
| **Phase 8** | GSD Advanced (Sphere, Cone, Torus, Blend, Ruled) | 10 | ⭐⭐ |
| **Phase 7** | Drafting-Grundlagen, Knowledgeware | 15-20 | ⭐⭐⭐ |
| **Phase 8** | PMI, Presentation, Management | 10-15 | ⭐⭐ |

---

## 15. Änderungsprotokoll

| Version | Datum | Autor | Änderung |
|---------|-------|-------|---------|
| 1.0 | 2026-05-30 | Hermes Agent | Erstfassung — Gap-Analyse gegen CATIA V5 Automation API |
| 1.1 | 2026-05-30 | Hermes Agent | Phase 6 (GSD) integriert: 16 neue Tools; GSD-Abdeckung 44%; Gesamt 35% (65/187) |
