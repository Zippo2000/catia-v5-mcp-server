# CATIA V5 MCP Server — Agent Guide

> **Zweck:** Dieses Dokument gibt Agenten den notwendigen Kontext, die Code-Konventionen
> und die Regeln für Arbeiten am catia-v5-mcp-server-Projekt.
>
> **Version:** 1.1 | **Datum:** 2026-06-06

---

## 1. Projekt-Kontext

### 1.1 Was ist das?

**catia-v5-mcp-server** ist ein Open-Source MCP-Server (Model Context Protocol) für
Dassault Systèmes CATIA V5. Er übersetzt LLM-Tool-Calls in CATIA V5 COM-Automation-Aufrufe
und ermöglicht damit LLM-gesteuerte CAD-Modellierung.

- **Lizenz:** MIT
- **Sprache:** Python 3.10+
- **Plattform:** Windows-only (COM Automation)
- **Tests:** Lauffähig auf Linux/macOS (COM gemockt)
- **Repository:** https://github.com/Zippo2000/catia-v5-mcp-server

### 1.2 Architektur

```
┌──────────────┐  MCP-Protokoll  ┌──────────────┐  pycatia / win32com  ┌──────────┐
│  LLM-Client  │  ──────────────►│  MCP-Server  │  ───────────────────►│ CATIA V5 │
│              │  (stdio / SSE)  │ (Python)     │  (Dual-Backend)      │ (Windows)│
└──────────────┘                  └──────────────┘                      └──────────┘
```

**Drei Transport-Modi:**
- `stdio` — Default; Claude Desktop, Claude Code
- `SSE` — `python -m catia_mcp --sse` (Port 8765); LM Studio, vLLM
- `Streamable HTTP` — `python -m catia_mcp --streamable-http` (Port 3001); Open WebUI

**Sieben Tool-Module (116 Tools):**

| Modul | Datei | Tools | Beschreibung |
|-------|-------|-------|-------------|
| Document | `catia_mcp/tools/document.py` | 10 | Part/Product erstellen, öffnen, speichern, schließen |
| Sketcher | `catia_mcp/tools/sketcher.py` | 18 | 2D-Sketching: Linien, Kreise, Bogen, Conics, Constraints, trim, mirror |
| Part Design | `catia_mcp/tools/part_design.py` | 28 | Pad, Pocket, Fillet, Shaft, Patterns, Boolean, Sweep, Loft, variable fillet, drafted filleted pad/pocket, multi pad/pocket |
| GSD | `catia_mcp/tools/gsd.py` | 32 | Wireframe + Surface: Point, Line, Plane, Fill, Blend, Split, sphere, cone, torus, ruled |
| Assembly | `catia_mcp/tools/assembly.py` | 15 | Komponenten, Constraints (Fix, Coincidence, Contact, ...) |
| Measurement | `catia_mcp/tools/measurement.py` | 10 | Distance, Inertia, Bounding Box, Angle, Area, Length |
| Export | `catia_mcp/tools/export.py` | 4 | STEP/IGES/STL, Screenshots, View Control |

**Kern-Dateien:**

| Datei | Zweck |
|-------|-------|
| `catia_mcp/server.py` | MCP-Server, Tool-Registrierung, Transport-Modi |
| `catia_mcp/connection.py` | COM-Verbindungsmanager, pycatia-Backend, Auto-connect |
| `catia_mcp/utils.py` | Validierungsfunktionen, Error-Formatting |
| `catia_mcp/__main__.py` | `python -m catia_mcp` Entry Point |

### 1.3 Dual-Backend

- **Primär:** `pycatia` (falls installiert) — löst COM-ByRef-Probleme, snake_case-API
- **Fallback:** `win32com` — PascalCase-API, hand-rolled Workarounds für ByRef
- **Erkennung:** `_is_pycatia(obj)` — prüft `type(obj).__module__.startswith('pycatia')`
- **Wichtig:** Beide Pfade müssen funktionieren. Tests mocken beide.

---

## 2. Dokumentation-Referenzen

Alle Dokumentationen liegen in `docs/`. Vor Änderungen: README + REQUIREMENTS lesen.

| Dokument | ID | Version | Zweck |
|----------|-----|---------|-------|
| `README.md` | — | — | Installation, Konfiguration, Tool-Referenz, Troubleshooting |
| `REQUIREMENTS.md` | REQ-001 | 1.9 | ASPICE-Spezifikation, 97 FRs + NRs, Traceability Matrix |
| `GAP_ANALYSIS.md` | GAP-001 | 1.3 | API-Abdeckungsanalyse, 179 API-Bereiche, 65% Abdeckung, Priorisierung |
| `CODE_REVIEW.md` | REV-001 | 1.0 | Code-Qualitätsbericht, Schwächen, Recommendations |
| `MIGRATION_PLAN.md` | MIG-001 | 1.1 | pycatia-Dual-Backend-Migration (abgeschlossen) |
| `TEST_PLAN.md` | TST-001 | 1.0 | Test-Abdeckungsplan, GSD-Pattern als Referenz |
| `CHANGELOG.md` | — | — | Versionshistorie, bekannte Bugs (BUG-001, BUG-002) |
| `tests/TEST_SPECIFICATION.md` | — | — | Detaillierte Test-Spezifikationen |
| `tests/TEST_SPEC_SSE.md` | — | — | SSE-Transport-Testspezifikation |

---

## 3. Code-Konventionen

### 3.1 Allgemein

- **Python 3.10+**, `from __future__ import annotations` in jeder Datei
- **Line length:** 100 Zeichen (in `pyproject.toml` via ruff)
- **Typing:** `Any` für COM-Objekte, `str | None` für optionale Parameter
- **String-Quoting:** `'single quotes'` für Strings, `"double quotes"` nur wenn `'` im String
- **Keine Kommentare** in Code, es sei denn für komplexe COM-API-Logik

### 3.2 Tool-Modul-Pattern

Jedes Tool-Modul folgt exakt diesem Pattern:

```python
class <Module>Tools:
    def __init__(self, connection: CATIAConnection) -> None:
        self.conn = connection

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "catia_<tool_name>",
                "description": "...",
                "inputSchema": {
                    "type": "object",
                    "properties": { ... },
                    "required": [ ... ],
                },
            },
            # ... alle Tools des Moduls
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        match tool_name:
            case "catia_<tool>":
                return self._<method>(arguments)
            case _:
                raise ValueError(f"Unknown <module> tool: {tool_name}")

    def _<method>(self, args: dict[str, Any]) -> str:
        self.conn.ensure_connected()
        # ... Input-Validierung via utils.py ...
        # ... COM-Aufruf (pycatia primär, win32com fallback) ...
        # ... self.conn.refresh_display() ...
        return f"Result message"
```

### 3.3 Validierung

- **Immer** vor COM-Aufruf validieren — nie ungültige Daten an CATIA senden
- Verwende die Funktionen aus `catia_mcp/utils.py`:
  - `validate_positive_float(value, name)` — > 0
  - `validate_non_negative_float(value, name)` — >= 0
  - `validate_positive_int(value, name)` — > 0, int
  - `validate_file_path(value, name)` — absoluter Pfad
  - `validate_plane(value)` — xy/yz/zx
  - `validate_sketch_name(value)` — optional, nicht-leer
  - `format_catia_error(op, e)` — Error-Formatting

### 3.4 Error-Handling

- **Validation-Fehler:** `ValueError` mit klarer Message (Parametername + erwarteter Wert)
- **COM-Fehler:** `RuntimeError` mit `format_catia_error("OperationName", e)`
- **Nicht gefundene Elemente:** `RuntimeError` mit Element-Name
- **Nie** bare `except:` — immer `except Exception:` oder spezifisch

### 3.5 pycatia/win32com-Dual-Backend-Pattern

```python
# In Part Design, GSD, Measurement:
has_pycatia = hasattr(self.conn, "get_active_part_pycatia") and HAS_PYCATIA
if has_pycatia:
    part = self.conn.get_active_part_pycatia()
    sf = part.shape_factory
    part.in_work_object = body
else:
    part = self.conn.get_active_part()
    sf = part.ShapeFactory
    part.InWorkObject = body

# ... COM-Aufruf ...

if has_pycatia:
    part.update_object(feature)
else:
    part.UpdateObject(feature)
```

### 3.6 Naming

- **Tool-Names:** `catia_<action>`, snake_case, immer mit `catia_` Prefix
- **Private Methoden:** `_<action>`, snake_case
- **Parameter:** camelCase in `inputSchema`, snake_case im Python-Code
- **Konstanten:** `UPPER_SNAKE_CASE` (z.B. `PLANE_MAP`, `FORMAT_MAP`)

---

## 4. Test-Regeln

### 4.1 Test-Infrastruktur

- **Framework:** `pytest`
- **COM-Mocking:** `tests/conftest.py` — injiziert `win32com` und `pycatia` Mocks
- **Jeder Test-File** startet mit `fresh_com_mocks` fixture (autouse)
- **Tests laufen auf Linux** ohne CATIA — alles gemockt

### 4.2 Test-Pattern (Referenz: GSD)

```python
class Test<ToolName>:
    # Happy Path
    def test_<tool_snake>_valid(self, tools_fixture, conn_mock):
        result = tools_fixture.execute("catia_<tool_name>", { ... })
        assert isinstance(result, str)
        assert "expected_keyword" in result

    # Error Path — validation
    def test_<tool_snake>_<param>_negative_raises(self, tools_fixture):
        with pytest.raises(ValueError, match="positive"):
            tools_fixture.execute("catia_<tool_name>", { "param": -1 })

    # Error Path — missing element
    def test_<tool_snake>_not_found_raises(self, tools_fixture, conn_mock):
        conn_mock.hso.Count = 0
        with pytest.raises(RuntimeError, match="not found"):
            tools_fixture.execute("catia_<tool_name>", { "element": "Ghost" })
```

### 4.3 Bekannte Test-Probleme

- **BUG-001:** `conftest._install_com_mocks()` setzt `EnsureDispatch.side_effect`,
  was `return_value`-Overrides in individualen Tests überschreibt.
  Betroffen: `test_dispatch_new_instance`, `test_get_active_object_success`,
  `test_reconnect_fallback` (3/256 Tests).
- **BUG-002:** pycatia-Mock aktiviert `HAS_PYCATIA` — behavior hängt von Import-Reihenfolge ab.

### 4.4 Test-Befehl

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 5. Linting & Quality

```bash
# Lint
ruff check catia_mcp/ tests/

# Format
ruff format catia_mcp/ tests/

# Test + Lint (Gate vor Commit)
pytest tests/ -v && ruff check catia_mcp/ tests/
```

---

## 6. Offene Aufgaben (Priority Order)

Aus `docs/CODE_REVIEW.md` — diese sind die nächsten Verbesserungsschritte:

### Phase 1: Quick Wins

- [ ] `_is_pycatia()` aus allen 6 Modulen entfernen → in `utils.py` oder `connection.py` zentralisieren
- [ ] Constraint-Codes in `assembly.py` als `enum.IntEnum` definieren
- [ ] `part_design.py` Import `CATIAConnection` ergänzen

### Phase 2: Refactoring

- [x] **Phase 2 Part Design Tools** — 5 new tools added (v1.11.0): `catia_variable_fillet`, `catia_drafted_filleted_pad`, `catia_drafted_filleted_pocket`, `catia_multi_pad`, `catia_multi_pocket`
- [ ] pycatia/win32com-Backend-Switching in `part_design.py` als Helper-Methode oder Decorator extrahieren
- [ ] `CATIAConnection` um `get_part_factory()` Methode ergänzen, die den pycatia/win32com-Switch kapselt
- [ ] `_is_pycatia()` MagicMock-Detection via `unittest.mock` import verbessern

### Phase 3: Test-Härtung

- [ ] BUG-001 fixen: `conftest.py` `side_effect`/`return_value` Konflikt lösen
- [ ] TEST_PLAN.md (TST-001) umsetzen: ~183 neue Tests, 0 ❌

---

## 7. Verbotene Aktionen

- **Keine Secrets** in Code committen (API-Keys, Tokens, Passwörter)
- **Keine CATIA-Dateien** (.CATPart, .CATProduct) committen
- **Keine `.pyc`/`__pycache__`/`.venv`/`*.log`** committen (`.gitignore` beachten)
- **Kein `cd &&`** in Bash — immer `workdir` Parameter verwenden
- **Kein `echo >/cat <<EOF`** für File-Writes — immer `Write` Tool verwenden
- **Keine neuen Dateien** ohne Notwendigkeit — immer bestehende Dateien editieren
- **Kein `pip install`** ohne aktiviertes `.venv`

---

## 8. Git & Commits

- **Kein Commit ohne explizite Benutzeranfrage**
- Vor Commit: `git status`, `git diff`, `git log --oneline -10` prüfen
- Nur beabsichtigte Dateien staged, **niemals** Secrets committen
- Commit-Message: kurz, imperativ, in Englisch (z.B. "fix: centralize _is_pycatia to utils.py")
- **Kein `--amend`, `--force`, `-i`** ohne explizite Anweisung

---

## 9. Quick Reference

| Frage | Antwort |
|-------|---------|
| Entry Point | `python -m catia_mcp` oder `catia-mcp` |
| Default-Transport | stdio (Claude Desktop/Code) |
| SSE-Port | 8765 |
| Streamable HTTP Port | 3001 |
| Tool-Anzahl | 116 |
| Test-Anzahl | 256 |
| Python-Version | >= 3.10 |
| Platform | Windows (COM), Tests auf Linux |
| Linter | ruff (line-length 100) |
| Test-Framework | pytest |
| Docs-Sprache | README/CHANGELOG: Englisch, docs/: Deutsch |
