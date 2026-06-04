# CATIA V5 MCP Server — Analyse-Vergleich: Hermes vs. OpenCode

> **Datum:** 2026-06-04
> **Quelle:** docs/REALTEST_RESULTS.md (122 Tests) + 8 Quelldateien

---

## 1. Gesamtbewertung

| Kriterium | Hermes Agent (Subagent) | OpenCode (ACP + CLI) |
|-----------|------------------------|---------------------|
| **Analyse abgeschlossen** | ✅ Ja | ❌ Nein |
| **Dateien gelesen** | 9 (REALTEST_RESULTS.md + 8 Source-Dateien) | 9 (gleiche Dateien) |
| **Bugs identifiziert** | **16** (B01–B16) | **0** |
| **Root Causes mit Zeilennummern** | ✅ Ja | ❌ Nein |
| **Systematische Muster** | 5 identifiziert | ❌ Keine |
| **Priorisierung** | ✅ 4 Phasen (Sofort → Langfristig) | ❌ Keine |
| **Falsche Pass-Rate erkannt** | ✅ 99.1% → ~62.3% | ❌ Nein |
| **False Positives quantifiziert** | ✅ 39 von 122 (32%) | ❌ Nein |
| **Laufzeit** | ~90s | ~15min (abgebrochen) |
| **Antwortformat** | Strukturiertes Markdown | Kein finaler Output |

---

## 2. Detailvergleich pro Kategorie

### 2.1 Measurement-Tools (P5)

| | Hermes | OpenCode |
|---|--------|----------|
| **B01: SPAWorkbench nie aktiviert** | ✅ Identifiziert mit Root Cause (`SetWorkbench` fehlt) | ❌ Nicht erkannt |
| **Betroffene Tools** | Alle 7 (distance, inertia, bounding_box, angle, area, length, interference) | — |
| **Lösung vorgeschlagen** | `self.conn.app.SetWorkbench("SPAWorkbench")` vor `GetWorkbench()` | — |

### 2.2 Part Design-Tools (P2)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B03: shaft.FirstAngle read-only** | ✅ gencache-Proxy, Lösung: `dynamic.Dispatch(shaft)` | ❌ |
| **B04: hole.Diameter read-only** | ✅ gleicher gencache-Bug | ❌ |
| **B05: Fillet: Shape statt Reference** | ✅ `CreateReferenceFromObject` fehlt | ❌ |
| **B06: Chamfer: Shape statt Reference** | ✅ gleicher Bug | ❌ |
| **B07: RectPattern: Integer statt Reference** | ✅ `i_dir1`/`i_dir2` müssen References sein | ❌ |
| **B08: close_sketch Update-Fehler** | ✅ Kaskadierender Fehler von B03/B04 | ❌ |

### 2.3 Sketcher-Tools (P1)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B09: Constraints: GeometricElement statt Reference** | ✅ `CreateReferenceFromObject` fehlt | ❌ |
| **B10: CreateArc API-Signatur** | ✅ Inkorrekte Parameter | ❌ |

### 2.4 GSD-Tools (P3)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B14: _find_shape: HybridBodies-Iteration** | ✅ `list()` auf late-bound Proxy → `EnsureDispatch` → `None` | ❌ |
| **B15: _ref: EnsureDispatch für OriginElements** | ✅ gencache hat keine Typbibliothek für Part-Proxy | ❌ |

### 2.5 Assembly-Tools (P4)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B11: Fix-Constraint: Product statt Reference** | ✅ `CreateReferenceFromObject` fehlt | ❌ |

### 2.6 Document-Tools (P0)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B12: SaveAs bei unsaved-Dokument** | ✅ Verzeichnis existiert möglicherweise nicht | ❌ |
| **B13: Open nicht-existente Datei** | ✅ Abhängigkeit von B12 | ❌ |

### 2.7 Viewer-Tools (P6)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B02: Kein aktiver 3D-Viewer im SSE-Modus** | ✅ `ActiveEditor` gibt `None` bei headless-Fernsteuerung | ❌ |

### 2.8 Test-Runner

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B16: False Positives** | ✅ 39 von 122 Tests (32%) — `ok = "error" in r.lower()` ist falsch | ❌ |

---

## 3. Systematische Muster

| # | Muster | Hermes | OpenCode |
|---|--------|--------|----------|
| 1 | Reference-vs-Object-Konfusion (14+ Tools) | ✅ Identifiziert | ❌ |
| 2 | Schreibgeschützte gencache-Eigenschaften (3 Tools) | ✅ Identifiziert | ❌ |
| 3 | Workbench-Wechsel fehlt (7 Tools) | ✅ Identifiziert | ❌ |
| 4 | Kein aktiver Editor/Viewer im SSE-Modus (6 Tools) | ✅ Identifiziert | ❌ |
| 5 | Test-Validierung akzeptiert Fehler als Erfolg | ✅ Identifiziert | ❌ |

---

## 4. Priorisierung

| Phase | Hermes | OpenCode |
|-------|--------|----------|
| **Sofort** | B01, B03/B04, B16 — Niedriger Aufwand, hoher Impact | — |
| **Kurzfristig** | B05/B06, B09, B11, B14 — 14+ Tools | — |
| **Mittelfristig** | B07, B10, B15, B02, B12/B13 | — |
| **Langfristig** | B08 (kaskadierend) | — |

---

## 5. Fazit

| | Hermes Agent | OpenCode |
|---|-------------|----------|
| **Eignung für tiefe Code-Analyse** | ✅ Vollständig | ❌ Nicht geeignet |
| **Ursache** | Subagent mit eigenem Kontext, mehrstufige Reasoning-Kette | vLLM-Provider bricht nach Tool-Call-Round ab (`step-finish: tool-calls`) |
| **Empfehlung** | **Standard für komplexe Analysen** | Nur einfache Tasks (<5 Tool-Calls) |

**Hermes Agent hat alle 16 Bugs mit Root Causes, Zeilennummern und Lösungsvorschlägen identifiziert. OpenCode hat die Dateien gelesen, aber keine analytische Antwort generiert.**