# SSE Transport Tests — Spezifikation

## Test-Scope

Der SSE-Transport in `catia_mcp/server.py` erweitert den MCP-Server um einen
HTTP-basierten Server-Sent-Events (SSE) Transport. Dieser Test-Spec definiert
alle zu testenden Bereiche und Fälle.

---

## 1. CLI Argument Parsing

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 1.1 | `parse_args()` ohne Argumente | `stdio=False`, `sse=False`, `host=0.0.0.0`, `port=8765` (Default: stdio) |
| 1.2 | `parse_args(["--sse"])` | `sse=True`, `stdio=False`, `host=0.0.0.0`, `port=8765` |
| 1.3 | `parse_args(["--sse", "--host", "127.0.0.1", "--port", "9999"])` | `sse=True`, `host=127.0.0.1`, `port=9999` |
| 1.4 | `parse_args(["--stdio", "--sse"])` | argparse `ArgumentError` (mutually exclusive) |
| 1.5 | `parse_args(["--port", "abc"])` | argparse TypeError (port muss int sein) |

## 2. Transport-Selektion in `main()`

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 2.1 | `main()` mit Default-args | Ruft `server.run(transport="stdio")` auf |
| 2.2 | `main()` mit `--sse` | Ruft `server.run(transport="sse", host, port)` auf |

## 3. SSE Server-Infrastruktur (Unit-Tests, kein Live-HTTP)

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 3.1 | `CATIAMCPServer` erstellt `SseServerTransport` korrekt | `SseServerTransport("/messages/")` existiert |
| 3.2 | Starlette-App hat zwei Routen: `/sse` (GET) und `/messages/` (Mount) | Routes existieren mit korrekten Methoden |
| 3.3 | `run_sse()` loggt Host, Port und Endpunkte beim Start | Logger-Einträge enthalten Host/Port-Info |

## 4. SSE `handle_sse` Handler (Mocked)

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 4.1 | `handle_sse` erstellt SSE-Session via `connect_sse()` | `connect_sse()` wird aufgerufen mit `scope/receive/send` |
| 4.2 | `handle_sse` ruft `server.run()` mit Streams auf | `server.run()` bekommt read/write streams |
| 4.3 | `handle_sse` gibt `Response()` nach Session-Ende zurück | Verhindert `NoneType`-Error bei Client-Disconnect |

## 5. Integration: SSE + Tool-Calling (Mocked)

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 5.1 | SSE-Mode listet gleiche Tools wie stdio | `list_tools` returns 55+ tools |
| 5.2 | Tool-Routing funktioniert im SSE-Modus | `catia_connect`, `catia_pad`, etc. werden korrekt geroutet |

## 6. Edge Cases

| # | Test | Erwartetes Verhalten |
|---|------|---------------------|
| 6.1 | `run_sse()` mit nicht-standard Port | `port=1` — uvicorn sollte starten (valid port) |
| 6.2 | `run_sse()` mit Host "127.0.0.1" | Bindet nur auf localhost |
| 6.3 | Disconnect bei SSE-Server-Ende | `connection.disconnect()` wird im `finally`-Block aufgerufen |

---

## Test-Constraints

- Tests laufen **ohne Live-HTTP** (keinen echten uvicorn starten)
- `SseServerTransport`, `Starlette`, `uvicorn` werden gemocked
- COM (`win32com`) wird via `conftest.py` gemocked (existiert bereits)
- Ziel: ~20 Tests für SSE-spezifische Funktionalität