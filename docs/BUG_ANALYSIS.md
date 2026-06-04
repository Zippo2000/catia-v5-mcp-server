# CATIA V5 MCP Server — Realtest Bug-Analyse

> **Analyst:** Hermes Agent (Qwen3.6-27B via subagent/delegate_task)
> **Datum:** 2026-06-04
> **Quelle:** docs/REALTEST_RESULTS.md (122 Tests, 115 ✅, 1 ❌, 6 ⏭️)
> **Quelldateien:** catia_mcp/tools/*.py, catia_mcp/connection.py

---

## TATSÄCHLICHE Pass-Rate

| Metrik | Wert |
|--------|------|
| Angezeigte Pass-Rate | **99.1%** (115/122) |
| **Echte Pass-Rate** | **~62.3%** (76/122) |
| False Positives | **~39 Tests** (32%) |

Der Test-Runner markiert Tools als ✅, die `Error in ...`-Meldungen zurückgeben — das ist ein **kritischer Validierungs-Bug** (B16).

---

## BUG-REGISTER

### B01 — SPAWorkbench nie aktiviert (🔴 KRITISCH)
- **Datei:** `measurement.py`
- **Methode:** `_measure_distance`, `_get_inertia`, `_get_bounding_box`, `_measure_angle`, `_measure_area`, `_measure_length`
- **Root Cause:** `GetWorkbench("SPAWorkbench")` ohne vorheriges `SetWorkbench("SPAWorkbench")`. Bei frischem CATIA-Start ist Part Design Workbench aktiv, nicht SPA.
- **Betroffene Tests:** P5-01..P5-07 (7 Tools komplett inoperabel)
- **Lösung:** `self.conn.app.SetWorkbench("SPAWorkbench")` vor `GetWorkbench()`

### B02 — Kein aktiver 3D-Viewer im SSE-Modus (🟡 HOCH)
- **Datei:** `connection.py`
- **Methode:** `_safe_active_viewer()` (Zeilen 280-288)
- **Root Cause:** `self.app.ActiveEditor` gibt `None` bei headless-Fernsteuerung via SSE. `_safe_active_viewer()` propagiert `None`, alle View-Tools werfen `RuntimeError`.
- **Betroffene Tests:** P6-01..P6-06 (6 Tools)
- **Lösung:** Editor explizit aktivieren oder Alternative-API verwenden

### B03 — shaft.FirstAngle read-only bei gencache-Proxy (🔴 KRITISCH)
- **Datei:** `part_design.py`
- **Methode:** `_shaft()` (Zeilen ~822-851)
- **Root Cause:** `shaft.FirstAngle = angle` — gencache-Proxys markieren `FirstAngle` als read-only. `AddNewShaft` gibt ein Objekt zurück, bei dem der Eigenschafts-Zugriff über gencache scheitert.
- **Betroffene Tests:** P2-18, P2-19
- **Lösung:** `dynamic.Dispatch(shaft).FirstAngle = angle`

### B04 — hole.Diameter read-only bei gencache-Proxy (🔴 KRITISCH)
- **Datei:** `part_design.py`
- **Methode:** `_hole()` (Zeilen ~953-987)
- **Root Cause:** `hole.Diameter = diameter` — gleicher gencache read-only Bug wie B03.
- **Betroffene Tests:** P2-23
- **Lösung:** `dynamic.Dispatch(hole).Diameter = diameter`

### B05 — Fillet: Shape statt Reference (🔴 KRITISCH)
- **Datei:** `part_design.py`
- **Methode:** `_fillet()` (Zeilen ~884-916)
- **Root Cause:** `AddNewSolidEdgeFilletWithConstantRadius(target, 1, radius)` — erwartet eine **Reference** auf eine Kante, nicht das Shape-Objekt. `_get_last_shape()` gibt Pad-Shape zurück, nicht Kante.
- **Betroffene Tests:** P2-11
- **Lösung:** `part.CreateReferenceFromObject(target)` vor Übergabe

### B06 — Chamfer: Shape statt Reference (🔴 KRITISCH)
- **Datei:** `part_design.py`
- **Methode:** `_chamfer()` (Zeilen ~918-951)
- **Root Cause:** Gleicher Bug wie B05 — `AddNewChamfer` erwartet Reference, nicht Shape.
- **Betroffene Tests:** P2-13
- **Lösung:** `part.CreateReferenceFromObject(target)` vor Übergabe

### B07 — RectPattern: Integer statt Reference für Richtungen (🔴 KRITISCH)
- **Datei:** `part_design.py`
- **Methode:** `_rect_pattern()` (Zeilen ~989-1024)
- **Root Cause:** `AddNewRectPattern(feature, d1_count, d2_count, d1_spacing, d2_spacing, 1, 1, True)` — `i_dir1` und `i_dir2` müssen **Reference**-Objekte sein, nicht Integer `1, 1`.
- **Betroffene Tests:** P2-24
- **Lösung:** Reference-Objekte für Richtungen erstellen und übergeben

### B08 — close_sketch: Update nach inkonsistentem Part-Status (🔴 KRITISCH)
- **Datei:** `sketcher.py`
- **Methode:** `_close_sketch()` (Zeilen ~416-434)
- **Root Cause:** `part.Update()` schlägt nach inkonsistentem Part-Status fehl. Kaskadierender Fehler von P2-18/19 Shaft-Fehlern — der Part-Baum enthält fehlerhafte Features.
- **Betroffene Tests:** P2-22 (einziger echter ❌)
- **Lösung:** B03/B04 zuerst fixen; dann defensives Error-Handling in `_close_sketch()`

### B09 — Sketch-Constraints: GeometricElement statt Reference (🟡 HOCH)
- **Datei:** `sketcher.py`
- **Methode:** `_add_constraint()` (Zeilen ~537-605)
- **Root Cause:** `AddBiEltCst(0, ref1, ref2)` mit `GeometricElement`-Objekten — CATIA erwartet **References** (`part.CreateReferenceFromObject(ref1)`).
- **Betroffene Tests:** P1-14, P1-15
- **Lösung:** `part.CreateReferenceFromObject()` für GeometricElements

### B10 — CreateArc API-Signatur inkorrekt (🟡 HOCH)
- **Datei:** `sketcher.py`
- **Methode:** `_draw_arc()` (Zeilen ~481-498)
- **Root Cause:** `factory.CreateArc(cx, cy, radius, start_rad, end_rad)` — CATIA-Sketch-Factory erwartet möglicherweise andere Parameter oder Winkelformat.
- **Betroffene Tests:** P1-10
- **Lösung:** CATIA-API-Dokumentation prüfen, korrekte Signatur verwenden

### B11 — Fix-Constraint: Product statt Reference (🟡 HOCH)
- **Datei:** `assembly.py`
- **Methode:** `_fix_constraint()` (Zeilen ~391-411)
- **Root Cause:** `AddMonoEltCst(0, component)` — CATIA erwartet **Reference** auf das Component, nicht das Product-Objekt selbst.
- **Betroffene Tests:** P4-04
- **Lösung:** `product.CreateReferenceFromObject(component)`

### B12 — SaveAs bei unsaved-Dokument (🟡 HOCH)
- **Datei:** `document.py`
- **Methode:** `_save_document()` (Zeilen ~242-257)
- **Root Cause:** `SaveAs` bei neu erstelltem Dokument ohne Standardpfad kann fehlschlagen. Verzeichnis `C:/catia_tests/` existiert möglicherweise nicht.
- **Betroffene Tests:** P0-08
- **Lösung:** Verzeichnis existenz prüfen/erstellen, dann `SaveAs`

### B13 — Open nicht-existente Datei (🟡 HOCH)
- **Datei:** `document.py`
- **Methode:** `_open_document()` (Zeilen ~226-240)
- **Root Cause:** `OpenDocument` für Datei, die von P0-08 nie erstellt wurde (weil SaveAs fehlgeschlagen).
- **Betroffene Tests:** P0-10
- **Lösung:** Abhängigkeit von P0-08; nach B12-Fix automatisch behoben

### B14 — _find_shape: win32com HybridBodies-Iteration fehlschlägt (🔴 KRITISCH)
- **Datei:** `gsd.py`
- **Methode:** `_find_shape()` (Zeilen ~835-861)
- **Root Cause:** `list(part.HybridBodies)` fehlschlägt bei late-bound Proxys → `EnsureDispatch` → `None`. Alle nachfolgenden Tools können keine Geometrie finden.
- **Betroffene Tests:** P3-04..P3-09, P3-13..P3-18, P3-20 (12 Tools)
- **Lösung:** Robustere Iteration über HybridBodies, dynamic.Dispatch als Primary

### B15 — _ref: EnsureDispatch für OriginElements.ZAxis fehlschlägt (🔴 KRITISCH)
- **Datei:** `gsd.py`
- **Methode:** `_ref()` (Zeilen ~881-890)
- **Root Cause:** `EnsureDispatch(part)` kann fehlschlagen, wenn `part` bereits late-bound Proxy ist. gencache hat keine Typbibliothek für Part-Proxy.
- **Betroffene Tests:** P3-11, P3-12
- **Lösung:** `dynamic.Dispatch(part).OriginElements` statt `EnsureDispatch`

### B16 — Test-Validierung: False Positives (🔴 KRITISCH)
- **Datei:** `run_realtests.py` (Test-Runner)
- **Root Cause:** Tests prüfen `ok = "error" in r.lower()` oder zu lockere Kriterien. Tools, die COM-Fehler werfen, werden als "bestanden" markiert, weil der Test nur prüft, ob die Antwort ein String ist.
- **Betroffene Tests:** ~39 von 122 (32% False Positives)
- **Lösung:** Test-Validierung umschalten: `ok = "error" not in r.lower()` für Tools, die erfolgreich sein sollen

---

## 5 SYSTEMATISCHE MUSTER

### Muster 1: Reference-vs-Object-Konfusion (14+ Tools)
Tools übergeben COM-Objekte direkt, wo CATIA References erwartet:
- Fillet/Chamfer → Shape statt Reference (B05, B06)
- Constraints → GeometricElement statt Reference (B09)
- Fix Constraint → Product statt Reference (B11)
- `_ref()` in GSD → `_find_shape()` findet Namen nicht (B14)

### Muster 2: Schreibgeschützte gencache-Eigenschaften (3 Tools)
`shaft.FirstAngle`, `hole.Diameter` — gencache-Proxys markieren als read-only.
Lösung: `dynamic.Dispatch(obj)` vor Eigenschafts-Zugriff (B03, B04)

### Muster 3: Workbench-Wechsel fehlt (7 Tools)
`GetWorkbench("SPAWorkbench")` ohne `SetWorkbench("SPAWorkbench")` (B01)

### Muster 4: Kein aktiver Editor/Viewer im SSE-Modus (6 Tools)
`_safe_active_viewer()` gibt `None` bei headless-Fernsteuerung (B02)

### Muster 5: Test-Validierung akzeptiert Fehler als Erfolg
Jeder Test mit `ok = "error" in r.lower()` oder zu lockeren Kriterien markiert COM-Fehler als ✅ (B16)

---

## PRIORITÄTS-EMPFEHLUNG

| Phase | Bugs | Aufwand | Impact |
|-------|------|---------|--------|
| **Sofort** | B01 (SPAWorkbench), B03/B04 (dynamic.Dispatch), B16 (Test-Runner) | Niedrig | 7 Measurement + 3 Part Design + 39 False Positives |
| **Kurzfristig** | B05/B06 (Reference), B09 (Constraint Reference), B11 (Fix Reference), B14 (_find_shape) | Mittel | 14+ GSD/Part Design Tools |
| **Mittelfristig** | B07 (RectPattern), B10 (Arc), B15 (OriginElements), B02 (Viewer), B12/B13 (Save/Open) | Mittel-Hoch | Restliche Tools |
| **Langfristig** | B08 (kaskadierend — wird mit B03/B04 behoben) | Gering | 1 Test |
