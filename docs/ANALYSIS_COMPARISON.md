# CATIA V5 MCP Server — Analyse-Vergleich: Hermes vs. OpenCode

> **Datum:** 2026-06-04
> **Quelle:** docs/REALTEST_RESULTS.md (122 Tests) + 8 Quelldateien

---

## 1. Gesamtbewertung

| Kriterium | Hermes Agent (Subagent) | OpenCode (qwen3.6-27b) |
|-----------|------------------------|------------------------|
| **Analyse abgeschlossen** | ✅ Ja | ✅ Ja |
| **Dateien gelesen** | 9 (REALTEST_RESULTS.md + 8 Source-Dateien) | 9 (gleiche Dateien) |
| **Bugs identifiziert** | **16** (B01–B16) | **16** (B01–B16) |
| **Root Causes mit Zeilennummern** | ✅ Ja | ✅ Ja |
| **Systematische Muster** | 5 identifiziert | 5 identifiziert |
| **Priorisierung** | ✅ 4 Phasen (Sofort → Langfristig) | ✅ 4 Phasen (Sofort → Langfristig) |
| **Falsche Pass-Rate erkannt** | ✅ 99.1% → ~62.3% | ✅ 99.1% → ~62% |
| **False Positives quantifiziert** | ✅ 39 von 122 (32%) | ✅ 39 von 122 (32%) |
| **Übereinstimmung** | — | **100%** (alle 16 Bugs identisch) |

---

## 2. Detailvergleich pro Kategorie

### 2.1 Measurement-Tools (P5)

| | Hermes | OpenCode |
|---|--------|----------|
| **B01: SPAWorkbench nie aktiviert** | ✅ `SetWorkbench` fehlt | ✅ `SetWorkbench` fehlt |
| **Root Cause** | `measurement.py:364` — `GetWorkbench("SPAWorkbench")` ohne vorherige `SetWorkbench()` | **Identisch** |
| **Betroffene Tools** | Alle 7 (distance, inertia, bounding_box, angle, area, length, interference) | **Identisch** |
| **Lösung vorgeschlagen** | `self.conn.app.SetWorkbench("SPAWorkbench")` vor `GetWorkbench()` | **Identisch** |

### 2.2 Part Design-Tools (P2)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B03: shaft.FirstAngle read-only** | ✅ gencache-Proxy, Lösung: `dynamic.Dispatch(shaft)` | **Identisch** |
| **B04: hole.Diameter read-only** | ✅ gleicher gencache-Bug | **Identisch** |
| **B05: Fillet: Shape statt Reference** | ✅ `CreateReferenceFromObject` fehlt | **Identisch** |
| **B06: Chamfer: Shape statt Reference** | ✅ gleicher Bug | **Identisch** |
| **B07: RectPattern: Integer statt Reference** | ✅ `i_dir1`/`i_dir2` müssen References sein | **Identisch** |
| **B08: close_sketch Update-Fehler** | ✅ Kaskadierender Fehler von ungültigem Sketch (unconstrained Point) | **Identisch** |

### 2.3 Sketcher-Tools (P1)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B09: Constraints: GeometricElement statt Reference** | ✅ `CreateReferenceFromObject` fehlt | **Identisch** |
| **B10: CreateArc API-Signatur** | ✅ Inkorrekte Parameter | **Identisch** |

### 2.4 GSD-Tools (P3)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B14: _find_shape: HybridBodies-Iteration** | ✅ `list()` auf late-bound Proxy → `EnsureDispatch` → `None` | **Identisch** |
| **B15: _ref: EnsureDispatch für OriginElements** | ✅ gencache hat keine Typbibliothek für Part-Proxy | **Identisch** |

### 2.5 Assembly-Tools (P4)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B11: Fix-Constraint: Product statt Reference** | ✅ `CreateReferenceFromObject` fehlt | **Identisch** |

### 2.6 Document-Tools (P0)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B12: SaveAs bei unsaved-Dokument** | ✅ Verzeichnis existiert möglicherweise nicht | **Identisch** |
| **B13: Open nicht-existente Datei** | ✅ Abhängigkeit von B12 | **Identisch** |

### 2.7 Viewer/Export-Tools (P6)

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B02: Kein aktiver 3D-Viewer im SSE-Modus** | ✅ `ActiveEditor` gibt `None` bei headless-Fernsteuerung | **Identisch** |

### 2.8 Test-Runner

| Bug | Hermes | OpenCode |
|-----|--------|----------|
| **B16: False Positives** | ✅ 39 von 122 Tests (32%) — `ok = "error" in r.lower()` ist falsch | **Identisch** |

---

## 3. Systematische Muster

| # | Muster | Hermes | OpenCode |
|---|--------|--------|----------|
| 1 | Reference-vs-Object-Konfusion (14+ Tools) | ✅ Identifiziert | **Identisch** |
| 2 | Schreibgeschützte gencache-Eigenschaften (3 Tools) | ✅ Identifiziert | **Identisch** |
| 3 | Workbench-Wechsel fehlt (7 Tools) | ✅ Identifiziert | **Identisch** |
| 4 | Kein aktiver Editor/Viewer im SSE-Modus (6 Tools) | ✅ Identifiziert | **Identisch** |
| 5 | Test-Validierung akzeptiert Fehler als Erfolg | ✅ Identifiziert | **Identisch** |

---

## 4. Priorisierung

| Phase | Hermes | OpenCode |
|-------|--------|----------|
| **Sofort** | B01, B03/B04, B16 — Niedriger Aufwand, hoher Impact | **Identisch** |
| **Kurzfristig** | B05/B06, B09, B11, B14 — 14+ Tools | **Identisch** |
| **Mittelfristig** | B07, B10, B15, B02, B12/B13 | **Identisch** |
| **Langfristig** | B08 (kaskadierend) | **Identisch** |

---

## 5. Abweichungen & Ergänzungen

### OpenCode-spezifische Erkenntnisse

| Thema | Detail |
|-------|--------|
| **Code-Struktur-Analyse** | OpenCode hat die Bug-Muster direkt im Quellcode verifiziert (Zeilennummern in 8 Dateien) |
| **Dual-Backend-Kontext** | OpenCode hat identifiziert, dass B03/B04 spezifisch für win32com gencache sind und im pycatia-Pfad nicht auftreten |
| **Test-Runner-Bug** | OpenCode hat bestätigt, dass die False-Positive-Logik in der Test-Auswertung liegt, nicht in den Tools selbst |
| **_is_pycatia Duplizierung** | OpenCode hat festgestellt, dass `_is_pycatia()` in allen 7 Tool-Modulen dupliziert ist (Code-Qualitätsproblem) |

### Hermes-spezifische Erkenntnisse

| Thema | Detail |
|-------|--------|
| **Subagent-Architektur** | Hermes nutzte einen dedizierten Subagent mit eigenem Kontext für mehrstufige Reasoning-Ketten |
| **Laufzeit** | ~90s vs. OpenCode ~5min (inklusive paralleles Lesen aller Quelldateien) |

---

## 6. Fazit

| | Hermes Agent | OpenCode |
|---|-------------|----------|
| **Bug-Erkennung** | ✅ Alle 16 Bugs | ✅ Alle 16 Bugs (100% Übereinstimmung) |
| **Root-Cause-Analyse** | ✅ Mit Zeilennummern | ✅ Mit Zeilennummern (direkte Code-Verifikation) |
| **Lösungsvorschläge** | ✅ Konkret | ✅ Konkret (identisch) |
| **Eignung für tiefe Code-Analyse** | ✅ Vollständig | ✅ Vollständig |
| **Differenz** | Schneller (~90s), Subagent-Architektur | Langsamer (~5min), aber Code wurde direkt verifiziert |
| **Empfehlung** | **Standard für komplexe Analysen** | **Gleichwertig für Code-verifizierte Analysen** |

**Beide Agenten haben dieselben 16 Bugs mit denselben Root Causes und Lösungsvorschlägen identifiziert. Die Analysen sind inhaltlich identisch.**
